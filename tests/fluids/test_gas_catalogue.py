#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The published gases, against the pages they were read on.

Two books print the pair that closes a gas, and this catalogue holds both
printings rather than choosing between them. So the tests are about three
things: that every cell matches the page, that a cell the page prints as
something other than a value stays that way, and that where the two books
overlap they agree.

The oracle is written out separately in :mod:`tests.reference_data.gases`,
from the rendered pages rather than from the data files, so that a
transcription error in a data file cannot make the test that checks it pass.
"""

from __future__ import annotations

import warnings

import pytest
import reference_data as ref

from phonometry.fluids import PUBLISHED_GASES, Gas, gases_named

#: Bies 5e Table C.2 keyed the way the catalogue keys it.
BIES = "bies-2017-table-c2"

#: Hopkins (2007) Table A1, the same.
HOPKINS = "hopkins-2007-table-a1"


def _key(table: str, name: str) -> str:
    """The catalogue key for a gas of a table, from its printed name."""
    return next(
        key
        for key, row in PUBLISHED_GASES.items()
        if key.startswith(f"{table}/") and row.name == name
    )


# ---------------------------------------------------------------------------
# The transcription
# ---------------------------------------------------------------------------
def test_the_catalogue_holds_every_row_of_both_tables() -> None:
    """Thirty-seven gases and six, and not one row more or fewer."""
    counted = {BIES: 0, HOPKINS: 0}
    for key in PUBLISHED_GASES:
        counted[key.split("/", 1)[0]] += 1
    assert counted == {BIES: len(ref.BIES_C2_GASES), HOPKINS: len(ref.HOPKINS_A1_GASES)}


@pytest.mark.parametrize(("name", "molar_mass", "ratio"), ref.BIES_C2_GASES)
def test_each_bies_row_holds_what_its_page_prints(
    name: str, molar_mass: float, ratio: float | tuple[float, float]
) -> None:
    """The molar mass always, and the ratio unless the cell was not a value."""
    row = PUBLISHED_GASES[_key(BIES, name)]
    if name in ref.BIES_C2_MISPRINTED:
        pytest.skip("this cell is checked by the errata tests below")
    assert row.molar_mass_kg_mol == molar_mass
    if isinstance(ratio, tuple):
        assert row.heat_capacity_ratio is None
        assert row.ranges["heat_capacity_ratio"] == ratio
    else:
        assert row.heat_capacity_ratio == ratio


@pytest.mark.parametrize(
    ("name", "ratio", "molar_mass", "_speed", "_density"), ref.HOPKINS_A1_GASES
)
def test_each_hopkins_row_holds_what_its_page_prints(
    name: str, ratio: float, molar_mass: float, _speed: float, _density: float
) -> None:
    """The two columns of Table A1 this catalogue takes, to the printed digit."""
    row = PUBLISHED_GASES[_key(HOPKINS, name)]
    assert row.molar_mass_kg_mol == molar_mass
    assert row.heat_capacity_ratio == ratio


def test_a_gas_row_names_the_page_it_was_read_on() -> None:
    """Document, table, PDF page and printed folio, once, in the data file."""
    assert PUBLISHED_GASES[f"{BIES}/methane"].source == (
        "Bies 5e Table C.2, PDF page 751 (printed p. 722)"
    )
    assert PUBLISHED_GASES[f"{HOPKINS}/argon"].source == (
        "Hopkins (2007) Table A1, PDF page 634 (printed p. 607)"
    )


def test_the_only_interval_on_the_bies_page_is_saturated_steam() -> None:
    """A range is the page refusing to give one number, and only one row does."""
    ranged = {
        key
        for key, row in PUBLISHED_GASES.items()
        if "heat_capacity_ratio" in row.ranges
    }
    assert ranged == {f"{BIES}/saturated_steam"}


# ---------------------------------------------------------------------------
# From the two constants to a state
# ---------------------------------------------------------------------------
def test_a_gas_reaches_a_state_through_the_ideal_closure() -> None:
    """The pair the page prints is exactly what the closure takes."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        state = PUBLISHED_GASES[f"{BIES}/methane"].ideal_state(temperature_c=20.0)
    assert state.speed_of_sound == pytest.approx(447.9, abs=0.1)
    assert state.density == pytest.approx(0.667, abs=0.001)


def test_the_state_carries_the_page_of_the_row_it_came_from() -> None:
    """A number that leaves the catalogue keeps the citation with it."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        state = PUBLISHED_GASES[f"{BIES}/helium"].ideal_state(temperature_c=20.0)
    assert "Helium" in state.model
    assert "Bies 5e Table C.2" in state.model
    assert "ideal gas" in state.model


def test_a_row_whose_ratio_is_an_interval_refuses_to_make_a_state() -> None:
    """And the refusal says what the page had there, not just that it failed."""
    row = PUBLISHED_GASES[f"{BIES}/saturated_steam"]
    with pytest.raises(ValueError, match=r"1\.25 to 1\.32"):
        row.ideal_state(temperature_c=100.0)


# ---------------------------------------------------------------------------
# Two books on one gas
# ---------------------------------------------------------------------------
def test_a_name_answers_with_every_books_reading_of_it() -> None:
    """Air is printed by both, under two names, and both come back."""
    rows = gases_named("air")
    assert [row.table for row in rows] == [BIES, HOPKINS]
    assert [row.name for row in rows] == ["Air", "Air (dry)"]


def test_a_gas_only_one_book_prints_answers_with_one_row() -> None:
    methane = gases_named("methane")
    assert len(methane) == 1
    assert methane[0].table == BIES


def test_a_name_no_page_prints_answers_with_nothing() -> None:
    assert gases_named("unobtainium") == ()


@pytest.mark.parametrize(("name", "bies", "hopkins"), ref.SHARED_GASES)
def test_the_two_books_agree_on_the_gases_they_both_print(
    name: str, bies: tuple[float, float], hopkins: tuple[float, float]
) -> None:
    """Not equality: the two readings have to sit inside a stated tolerance.

    The molar masses are the same physical constant read to different
    precision, so they agree to a part in a thousand. The ratios of specific
    heats are measurements, and carbon dioxide is the one gas where the two
    books are further apart than a rounding digit.
    """
    rows = gases_named(name)
    assert len(rows) == 2, name
    for row, printed in zip(rows, (bies, hopkins), strict=True):
        assert row.molar_mass_kg_mol == printed[0]
        assert row.heat_capacity_ratio == printed[1]
    for index, field in enumerate(("molar_mass_kg_mol", "heat_capacity_ratio")):
        apart = abs(bies[index] - hopkins[index]) / max(bies[index], hopkins[index])
        assert apart <= ref.SHARED_GAS_TOLERANCE[field], (
            f"{name}: the two books are {apart:.1%} apart on {field}"
        )


# ---------------------------------------------------------------------------
# The cells the registry calls wrong
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(("name", "field"), sorted(ref.BIES_C2_MISPRINTED.items()))
def test_a_cell_the_errata_names_is_not_served_as_a_value(
    name: str, field: str
) -> None:
    """The page printed a number and this library will not hand it over."""
    row = PUBLISHED_GASES[_key(BIES, name)]
    assert getattr(row, field) is None
    assert field in row.misprinted


@pytest.mark.parametrize(("name", "field"), sorted(ref.BIES_C2_MISPRINTED.items()))
def test_the_refusal_quotes_the_printed_number_and_points_at_the_registry(
    name: str, field: str
) -> None:
    """A reader told the book is wrong needs both halves to check it."""
    row = PUBLISHED_GASES[_key(BIES, name)]
    reason = row.why_missing(field)
    printed = next(
        (mass if field == "molar_mass_kg_mol" else ratio)
        for gas, mass, ratio in ref.BIES_C2_GASES
        if gas == name
    )
    assert f"{printed:g}" in reason, (
        f"{name}: the reason does not quote the {printed:g} the page prints"
    )
    assert "ERRATA" in reason
    with pytest.raises(ValueError, match="prints"):
        row.printed(field)


def test_no_other_cell_of_either_table_is_called_wrong() -> None:
    """Six cells, and the claim does not spread quietly to a seventh."""
    called = {
        (row.name, field)
        for row in PUBLISHED_GASES.values()
        for field in row.misprinted
    }
    assert called == set(ref.BIES_C2_MISPRINTED.items())


def test_the_row_of_a_misprinted_cell_still_holds_its_other_column() -> None:
    """One wrong cell does not throw the row away."""
    ammonia = PUBLISHED_GASES[_key(BIES, "Ammonia")]
    assert ammonia.heat_capacity_ratio == 1.32


# ---------------------------------------------------------------------------
# The catalogue as an object
# ---------------------------------------------------------------------------
def test_the_catalogue_cannot_be_written_to() -> None:
    """One object shared by every caller, and provenance nobody can rewrite."""
    with pytest.raises(TypeError):
        PUBLISHED_GASES["invented/gas"] = Gas(  # type: ignore[index]
            name="Invented", source="nowhere"
        )


@pytest.mark.parametrize(("name", "molar_mass", "_ratio"), ref.BIES_C2_GASES)
def test_a_row_the_registry_leaves_alone_weighs_what_its_molecule_weighs(
    name: str, molar_mass: float, _ratio: float | tuple[float, float]
) -> None:
    """The comparison that makes the four exceptions exceptions.

    A molar mass is not a measurement with a spread, it follows from the
    molecule the row names, so the whole table can be held against the 2021
    IUPAC atomic weights. Thirty-one rows land inside the page's own printed
    precision and two more miss only by their last digit.
    """
    if name in ref.BIES_C2_MISPRINTED:
        pytest.skip("this row is one of the four the registry names")
    formula = ref.FORMULA_MASSES_G_MOL.get(name)
    if formula is None:
        pytest.skip("a mixture has no formula mass")
    apart = abs(molar_mass * 1000.0 - formula) / formula
    assert apart <= ref.FORMULA_MASS_TOLERANCE, (
        f"{name}: the page prints {molar_mass * 1000:g} g/mol where the "
        f"molecule weighs {formula:g}, {apart:.2%} apart"
    )


@pytest.mark.parametrize(
    "name",
    [
        gas
        for gas, field in sorted(ref.BIES_C2_MISPRINTED.items())
        if field == "molar_mass_kg_mol"
    ],
)
def test_the_four_the_registry_names_are_the_ones_that_do_not(name: str) -> None:
    """The other half of the argument, and the reason it is not a convention."""
    printed = next(mass for gas, mass, _ in ref.BIES_C2_GASES if gas == name)
    formula = ref.FORMULA_MASSES_G_MOL[name]
    apart = abs(printed * 1000.0 - formula) / formula
    assert apart > ref.FORMULA_MASS_TOLERANCE * 5, (
        f"{name} is only {apart:.2%} from its formula mass, which is not far "
        f"enough to call the page wrong"
    )
