#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the catalogue data the site renders (``generate_catalogue_data``).

The script decides how every published number reads on the page, and nothing
downstream can tell a good decision from a bad one: a modulus written as
``62 110 000 000`` and one written as ``6,211 × 10¹⁰`` are the same value and
only one of them is a table a reader can compare down. So the decisions are
pinned here, with the cases that made them: a column is written in powers of
ten when the middle of the column asks for it and not when one outlier does,
a cell holds what its page printed, and a cell this library refuses to fill
reads as empty with the reason beside it.
"""

from __future__ import annotations

import dataclasses
import pathlib
import sys
from collections.abc import Mapping

import pytest

from phonometry.fluids import PUBLISHED_FLUIDS
from phonometry.io import CatalogueRow

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import generate_catalogue_data as gcd

#: The narrow no-break space the corpus groups thousands with.
_GROUP = " "


@dataclasses.dataclass(frozen=True, kw_only=True)
class _Specimen(CatalogueRow):
    """A row with quantities on it, standing in for the published classes.

    The shared row carries the provenance and the hedges and no quantity of
    its own, because which quantities a catalogue has is what distinguishes a
    solid from a porous material. The tests need some, and inventing two of
    each kind here keeps them independent of what any one catalogue happens
    to publish today.
    """

    density_kg_m3: float | None = None
    youngs_modulus_pa: float | None = None
    bar_longitudinal_speed_m_s: float | None = None
    loss_factor: float | None = None
    porosity: float | None = None
    tortuosity: float | None = None
    viscous_length_um: float | None = None
    thermal_permeability_m2: float | None = None
    shot_content_percent: float | None = None


def _row(**fields: object) -> _Specimen:
    """One row, with the provenance every row needs and nothing else."""
    return _Specimen(
        name="specimen",
        source="Book Table 1, PDF page 1 (printed p. 1)",
        **fields,  # type: ignore[arg-type]
    )


def _catalogue(*rows: _Specimen) -> dict[str, _Specimen]:
    return {f"table/row{index}": row for index, row in enumerate(rows)}


# ---------------------------------------------------------------------------
# How a number is written
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.0, "0"),
        (343.0, "343"),
        (1206.0, f"1{_GROUP}206"),
        (1100000.0, f"1{_GROUP}100{_GROUP}000"),
        (0.0125, "0,0125"),
        (-2700.0, f"-2{_GROUP}700"),
    ],
)
def test_a_number_is_written_with_a_comma_and_grouped_thousands(
    value: float, expected: str
) -> None:
    """The separators of every figure and table in this documentation."""
    assert gcd.number(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (62110000000.0, "6,211 × 10¹⁰"),
        (1e12, "1 × 10¹²"),
        (3.3e-9, "3,3 × 10⁻⁹"),
        (1.84e-5, "1,84 × 10⁻⁵"),
    ],
)
def test_a_power_of_ten_sets_as_a_power_of_ten(value: float, expected: str) -> None:
    """Not ``6.211e10``, which is how a program writes it and nobody reads it."""
    assert gcd.number(value, scientific=True) == expected


def test_a_printed_number_keeps_every_digit_it_carries() -> None:
    """The metrology annex prints 345,866 52 m/s, and that is the number."""
    assert gcd.number(345.86652) == "345,86652"


def test_a_derived_number_is_rounded_to_what_its_inputs_could_support() -> None:
    """A modulus and a density printed to four figures do not give fifteen."""
    assert gcd.number(4795.831523312615, exact=False) == f"4{_GROUP}796"


# ---------------------------------------------------------------------------
# How a column is written: the prefix moves into the heading
# ---------------------------------------------------------------------------
def test_a_column_of_moduli_is_a_column_of_gigapascals() -> None:
    """62,11 under GPa beats 6,211 × 10¹⁰ under Pa in every cell of a table."""
    style = gcd.column_style("Pa", [6.211e10, 4.717e11, 1.2e9])

    assert style.unit == "GPa"
    assert style.exponent == 9
    assert not style.scientific
    assert gcd.number(6.211e10, exponent=style.exponent) == "62,11"


def test_the_prefix_is_the_one_that_writes_the_column_shortest() -> None:
    """Which is what a reader means by the prefix that reads best."""
    assert gcd.column_style("Pa·s", [1.84e-5]).unit == "µPa·s"
    assert gcd.column_style("Pa·s/m²", [4e3, 2.2e4, 3.2e6]).unit == "kPa·s/m²"


def test_a_column_that_needs_no_prefix_keeps_its_unit() -> None:
    """A tie goes to the unit the quantity is stored in."""
    style = gcd.column_style("Pa", [100.0, 250.0, 900.0])

    assert style == gcd.Style("Pa", 0, scientific=False)


def test_scaling_a_column_does_not_invent_a_digit() -> None:
    """143 000 000 / 1000 in binary floating point is 143 000,000 000 000 01."""
    assert gcd.number(1.43e8, exponent=3) == f"143{_GROUP}000"


def test_a_unit_that_takes_no_prefix_falls_back_on_a_power_of_ten() -> None:
    """A squared metre would square the prefix with it, so it keeps none."""
    style = gcd.column_style("m²", [3.3e-9, 6e-9])

    assert style == gcd.Style("m²", 0, scientific=True)


def test_an_empty_column_is_written_in_the_unit_it_was_given() -> None:
    assert gcd.column_style("Pa", []) == gcd.Style("Pa")


# ---------------------------------------------------------------------------
# Which columns are written in powers of ten
# ---------------------------------------------------------------------------
def test_a_column_of_moduli_is_written_in_powers_of_ten() -> None:
    """Twelve digits of a modulus are not a number anybody reads."""
    catalogue = _catalogue(
        _row(youngs_modulus_pa=6.211e10),
        _row(youngs_modulus_pa=4.717e11),
        _row(youngs_modulus_pa=1.2e6),
    )

    assert gcd.by_powers(catalogue, "youngs_modulus_pa")


def test_one_small_outlier_does_not_take_a_column_with_it() -> None:
    """The loss factors run to 0,000003 around a median of 0,005.

    Writing that column in powers of ten to spare its smallest cell would
    turn every ordinary 0,005 in it into 5 × 10⁻³, which is the opposite of
    the point.
    """
    catalogue = _catalogue(
        _row(loss_factor=3e-6),
        _row(loss_factor=0.005),
        _row(loss_factor=0.01),
        _row(loss_factor=0.3),
    )

    assert not gcd.by_powers(catalogue, "loss_factor")


def test_a_column_that_lives_below_a_ten_thousandth_is_written_in_powers() -> None:
    """A permeability of 0,0000000033 m2 is eight leading zeros."""
    catalogue = _catalogue(
        _row(thermal_permeability_m2=3.3e-9),
        _row(thermal_permeability_m2=6e-9),
    )

    assert gcd.by_powers(catalogue, "thermal_permeability_m2")


def test_a_column_with_nothing_in_it_is_not_written_in_powers() -> None:
    """An empty column has no middle to ask."""
    assert not gcd.by_powers(_catalogue(_row()), "youngs_modulus_pa")


def test_the_ends_of_a_range_count_towards_the_decision() -> None:
    """A column of intervals holds its numbers in ``ranges`` and nowhere else."""
    catalogue = _catalogue(_row(ranges={"youngs_modulus_pa": (1.8e10, 3.0e10)}))

    assert sorted(gcd.values(catalogue, "youngs_modulus_pa")) == [1.8e10, 3.0e10]
    assert gcd.by_powers(catalogue, "youngs_modulus_pa")


def test_every_reading_of_a_reported_cell_counts_too() -> None:
    """A cell that lists several readings lists them all, ranges included."""
    catalogue = _catalogue(
        _row(reported={"viscous_length_um": (25.0, 207.0, (200.0, 450.0))})
    )

    assert sorted(gcd.values(catalogue, "viscous_length_um")) == [
        25.0,
        200.0,
        207.0,
        450.0,
    ]


# ---------------------------------------------------------------------------
# What a cell says
# ---------------------------------------------------------------------------
def test_a_printed_cell_is_printed() -> None:
    cell = gcd.cell(_row(density_kg_m3=2700.0), "density_kg_m3")

    assert cell == {"text": f"2{_GROUP}700", "kind": "printed", "note": ""}


def test_a_derived_cell_says_what_it_came_from() -> None:
    row = _row(
        youngs_modulus_pa=7.0e10,
        derived={"youngs_modulus_pa": "from the speed and the density"},
    )

    cell = gcd.cell(row, "youngs_modulus_pa", style=gcd.Style("GPa", 9))

    assert cell["kind"] == "derived"
    assert cell["note"] == "from the speed and the density"


def test_a_converted_cell_carries_the_figure_the_page_prints() -> None:
    row = _row(
        density_kg_m3=2700.0,
        converted={"density_kg_m3": ("168.6", "lb/ft3")},
    )

    cell = gcd.cell(row, "density_kg_m3")

    assert cell["kind"] == "converted"
    assert cell["printed"] == "168.6 lb/ft3"
    assert cell["note"] == ""


def test_a_carried_cell_says_where_the_page_prints_it() -> None:
    row = _row(
        density_kg_m3=2700.0,
        carried={"density_kg_m3": "carried down from the row above"},
    )

    cell = gcd.cell(row, "density_kg_m3")

    assert cell["kind"] == "carried"
    assert cell["note"] == "carried down from the row above"
    assert "printed" not in cell


def test_an_estimate_for_the_whole_row_marks_every_cell_of_it() -> None:
    row = _row(density_kg_m3=2700.0, basis={"row": "estimated"})

    assert gcd.cell(row, "density_kg_m3")["kind"] == "estimated"


def _holds_a_cell(row: CatalogueRow, field: str) -> bool:
    """Whether *field* of *row* is something the page would print in a cell.

    A number, or an interval, a list of readings or a word the page printed
    where a number would go. A text field such as a name is not a cell, and
    neither is a flag.
    """
    value = getattr(row, field)
    number = isinstance(value, (int, float)) and not isinstance(value, bool)
    return (
        number
        or field in row.ranges
        or field in row.reported
        or field in row.unquantified
    )


def _hedged_cells() -> list[tuple[str, CatalogueRow, str]]:
    """Every field of every published row that carries a hedge the page shows.

    Walked from the hedges rather than from the cells, so that a hedge on a
    cell with no single value is found as surely as one on a number: every
    key of ``converted`` and ``carried``, every field ``basis`` calls an
    estimate, and, where ``basis`` calls the whole row one, every cell of the
    row.
    """
    catalogues = [
        catalogue
        for name, catalogue in vars(gcd).items()
        if name.startswith("PUBLISHED_") and isinstance(catalogue, Mapping)
    ]
    found: list[tuple[str, CatalogueRow, str]] = []
    for catalogue in catalogues:
        for key, row in catalogue.items():
            if not isinstance(row, CatalogueRow):
                continue
            fields = set(row.converted) | set(row.carried)
            fields |= {
                name
                for name, basis in row.basis.items()
                if name != "row" and basis == "estimated"
            }
            if row.basis.get("row") == "estimated":
                fields |= {
                    field.name
                    for field in dataclasses.fields(row)
                    if _holds_a_cell(row, field.name)
                }
            found.extend((key, row, field) for field in sorted(fields))
    return found


def test_every_hedged_cell_reaches_the_page_as_its_own_kind() -> None:
    """Every published catalogue, not the one row a defect was found on.

    The generator once asked each row for ``is_estimated``, which the woods
    spelled and the solids did not, so the 33 estimated cells of 21 solids
    reached the page as printed numbers, among them the Poisson's ratio 0.2
    of the aircrete of Hopkins Table A2. Since then the estimate is one
    entry of ``basis``, and a value the page gives in another unit or by
    reference to another row has a mapping of its own. The walk starts from
    every hedge of every row the generator publishes, whatever the cell it
    sits on holds, so a hedge on an interval, or two hedges on one value, is
    found here too: :func:`gcd.cell` refuses those, and the refusal fails
    this test before the page could drop one of them.

    The three carried fields that are text (the row a Harris description
    refers to, where the page prints "Parecido al anterior" and no number)
    have no column on the page, and are counted apart so that the set cannot
    grow unseen.
    """
    estimated: list[str] = []
    converted: list[str] = []
    carried: list[str] = []
    text: list[str] = []
    wrong: list[str] = []
    for key, row, field in _hedged_cells():
        where = f"{key}: {field}"
        if isinstance(getattr(row, field), str):
            text.append(where)
            continue
        cell = gcd.cell(row, field)
        if row.basis_of(field) == "estimated":
            estimated.append(where)
            if cell["kind"] != "estimated":
                wrong.append(f"{where} reads as {cell['kind']}, not estimated")
        elif field in row.converted:
            converted.append(where)
            figure, unit = row.converted[field]
            if (cell["kind"], cell.get("printed")) != ("converted", f"{figure} {unit}"):
                wrong.append(f"{where} reads as {cell['kind']}, not converted")
        elif field in row.carried:
            carried.append(where)
            if (cell["kind"], cell["note"]) != ("carried", row.carried[field]):
                wrong.append(f"{where} reads as {cell['kind']}, not carried")

    assert not wrong, wrong
    assert len(estimated) == 35
    assert len(converted) == 125
    assert len(carried) == 18
    assert {where.rpartition(": ")[2] for where in text} == {"refers_to_row"}
    assert len(text) == 3


@pytest.mark.parametrize(
    ("hedges", "wanted"),
    [
        (
            {
                "ranges": {"density_kg_m3": (1000.0, 1200.0)},
                "basis": {"density_kg_m3": "estimated"},
            },
            "density_kg_m3 is estimated on a cell with no single value",
        ),
        (
            {
                "ranges": {"density_kg_m3": (5000.0, None)},
                "bounded_below": frozenset({"density_kg_m3"}),
                "converted": {"density_kg_m3": ("5", "g/cm3")},
            },
            "density_kg_m3 is converted on a cell with no single value",
        ),
        (
            {
                "ranges": {"density_kg_m3": (1000.0, 1200.0)},
                "basis": {"row": "estimated"},
            },
            "density_kg_m3 is estimated on a cell with no single value",
        ),
        (
            {
                "density_kg_m3": 5000.0,
                "approximate": frozenset({"density_kg_m3"}),
                "converted": {"density_kg_m3": ("5", "g/cm3")},
            },
            "density_kg_m3 is converted and approximate on a value",
        ),
        (
            {
                "density_kg_m3": 5000.0,
                "converted": {"density_kg_m3": ("5", "g/cm3")},
                "basis": {"density_kg_m3": "estimated"},
            },
            "density_kg_m3 is converted and estimated on a value",
        ),
    ],
    ids=[
        "estimated interval",
        "converted bound",
        "estimated row with an interval",
        "approximate conversion",
        "estimated conversion",
    ],
)
def test_a_hedge_the_page_cannot_show_stops_the_generator(
    hedges: dict[str, object], wanted: str
) -> None:
    """Refused, rather than published with one of its hedges gone."""
    row = _row(**hedges)

    with pytest.raises(ValueError, match=wanted):
        gcd.cell(row, "density_kg_m3")


def test_an_approximate_interval_is_still_an_interval() -> None:
    """The tilde on a cell that only holds an interval is not refused.

    Cox prints one, and a tilde is not a hedge that needs a single value.
    """
    row = _row(
        ranges={"density_kg_m3": (400.0, 800.0)},
        approximate=frozenset({"density_kg_m3"}),
    )

    assert gcd.cell(row, "density_kg_m3")["kind"] == "range"


def test_an_interval_stays_an_interval() -> None:
    cell = gcd.cell(_row(ranges={"density_kg_m3": (400.0, 800.0)}), "density_kg_m3")

    assert cell["text"] == "400 to 800"
    assert cell["kind"] == "range"


def test_an_interval_the_page_prints_with_a_tilde_keeps_it() -> None:
    """The range kind has no mark of its own, so the tilde goes in the text.

    Cox Table 6.5 prints the porosity of granular vermiculite as an interval
    with a tilde; before, the page showed the bare interval.
    """
    row = _row(ranges={"porosity": (0.65, 0.68)}, approximate=frozenset({"porosity"}))

    cell = gcd.cell(row, "porosity")

    assert cell["text"] == "~0,65 to 0,68"
    assert cell["kind"] == "range"


def test_an_upper_bound_stays_a_bound() -> None:
    row = _row(
        ranges={"shot_content_percent": (0.0, 1.0)},
        bounded_above=frozenset({"shot_content_percent"}),
    )

    cell = gcd.cell(row, "shot_content_percent")

    assert cell["text"] == "< 1"
    assert cell["kind"] == "bound"


def test_a_lower_bound_stays_a_bound_and_reads_as_one() -> None:
    """Before this branch existed it was published as a two-sided interval.

    Cox prints a porosity of ">0.75" and the published table read it back as
    "0,75 to 1", an interval whose high end nobody measured; a table whose
    bound has no ceiling at all had no number to put on that side and reached
    this function with an infinity.
    """
    row = _row(
        ranges={"porosity": (0.75, 1.0)},
        bounded_below=frozenset({"porosity"}),
    )

    cell = gcd.cell(row, "porosity")

    assert cell["text"] == "> 0,75"
    assert cell["kind"] == "bound"


def test_a_bound_whose_open_end_is_empty_prints_the_end_the_page_gave() -> None:
    open_ended = _row(
        ranges={"porosity": (0.75, None)},
        bounded_below=frozenset({"porosity"}),
    )

    cell = gcd.cell(open_ended, "porosity")

    assert cell["text"] == "> 0,75"
    assert cell["kind"] == "bound"
    assert list(gcd.values({"x": open_ended}, "porosity")) == [0.75]


def test_a_cell_that_lists_several_readings_lists_them() -> None:
    row = _row(reported={"viscous_length_um": (25.0, 207.0, (200.0, 450.0))})

    cell = gcd.cell(row, "viscous_length_um")

    assert cell["text"] == "25, 207, 200 to 450"
    assert cell["kind"] == "reported"


def test_a_cell_that_printed_a_word_shows_the_word() -> None:
    """And the sentence about why there is no number goes in the note.

    The word is what the page has in that cell, so it is what the table shows;
    a hundred-character sentence inside a numeric column reads as though the
    book had printed it.
    """
    cell = gcd.cell(_row(unquantified={"tortuosity": "model"}), "tortuosity")

    assert cell["text"] == "model"
    assert cell["kind"] == "unquantified"
    assert cell["note"] == "the page prints “model” where the number would be"


def test_a_cell_this_library_will_not_fill_reads_as_empty() -> None:
    """The page is empty there, so the table is empty there, with the reason."""
    reason = "the page leaves the cell blank, and the quantity does not exist here"
    row = _row(not_derivable={"bar_longitudinal_speed_m_s": reason})

    cell = gcd.cell(row, "bar_longitudinal_speed_m_s")

    assert cell["text"] == ""
    assert cell["kind"] == "absent"
    assert cell["note"] == reason


def test_a_cell_the_page_never_had_says_nothing_at_all() -> None:
    cell = gcd.cell(_row(), "porosity")

    assert cell == {"text": "", "kind": "absent", "note": ""}


# ---------------------------------------------------------------------------
# The committed module
# ---------------------------------------------------------------------------
def test_two_runs_write_the_same_bytes() -> None:
    """The freshness gate in CI compares text; a wobble would fail it daily."""
    first, second = gcd.render(), gcd.render()

    assert first == second


def test_the_committed_module_is_current(capsys: pytest.CaptureFixture[str]) -> None:
    """The same check CI runs, so a stale artefact fails here first."""
    assert gcd.main(["--check"]) == 0
    assert "is current" in capsys.readouterr().out


def test_a_state_a_model_fixes_is_not_a_state_a_page_printed() -> None:
    """Both are firm numbers; only one of them was read off a table.

    The fluid rows gather the three states Bies prints with the four airs the
    tree carries beside the model or the standard that fixes each, and a cell
    marked "as the page prints it" on one of those four would say the wrong
    thing about where the number came from.
    """
    columns, states = gcd.fluids()

    printed = [row for row in states if row["key"] in PUBLISHED_FLUIDS]
    fixed = [row for row in states if row["key"] in gcd.IN_TREE_FLUIDS]

    assert printed
    assert fixed
    assert {
        cell["kind"] for row in printed for cell in row["cells"] if cell["text"]
    } == {"printed"}
    assert {cell["kind"] for row in fixed for cell in row["cells"] if cell["text"]} == {
        "fixed"
    }
    assert [column["field"] for column in columns][0] == "speed_of_sound"
