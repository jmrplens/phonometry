#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Six printed tables of solids and fluids, against a second reading of the page.

Norton & Karczub 2e Table 3.1, Table 6.1 and Appendix 4 A, B and C; Vigran
(2008) Table 3.1; and Rossing (2014) Table 15.5. The catalogues and the oracle
in :mod:`tests.reference_data.wave3_solids` were transcribed by two readers who
never saw each other's work. These tests keep that comparison alive, cell by
cell and in the page's own notation, and check the three things a transcription
cannot say about itself: that every unit was converted with the factor the
page's own heading names, that a cell the page misprinted is refused rather
than served, and that a column the table derives from its other columns by
its own approximation is held as printed rather than replaced by this
library's.
"""

from __future__ import annotations

import math
import re

import pytest
import reference_data as ref

from phonometry import fluids, solids
from phonometry.fluids import PUBLISHED_FLUIDS
from phonometry.solids import (
    PUBLISHED_ORTHOTROPIC_WOOD,
    PUBLISHED_PLATEAU_DATA,
    PUBLISHED_SOLIDS,
)

#: Superscript digits and minus, as the pages set a power of ten.
_SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")

#: A rule: the page prints no value in this cell.
_RULES = {"–", "-", "—"}

#: The speed of sound in air that Norton & Karczub's last appendix column uses.
_AIR_SPEED_M_S = 343.0


def _number(text: str) -> float:
    """One printed number, with a power of ten and a thin-space separator."""
    text = text.replace(" ", "").replace(" ", "").replace(" ", "")
    text = text.replace("−", "-")
    if "×10" in text:
        mantissa, power = text.split("×10")
        return float(mantissa) * 10 ** int(power.translate(_SUPERSCRIPT))
    return float(text)


def _cell(text: str) -> tuple[str, float | tuple[float, float] | None]:
    """What a printed cell says, as (kind, value).

    The kind is ``rule``, ``range``, ``approximate`` or ``value``. A range that
    carries one power of ten after it, as ``1–6 × 10⁻⁴``, applies it to both
    ends, which is how the page means it.
    """
    text = text.strip()
    # A footnote mark follows the number after a space (``3.8 ²``); an
    # exponent is set against it (``10⁻²``). Only the first is not a digit of
    # the value, and neither is an estimate asterisk.
    text = re.sub(r"\s+[²¹]$", "", text).rstrip("*").strip()
    if text in _RULES:
        return "rule", None
    approximate = text[:1] in {"~", "∼"}
    if approximate:
        text = text[1:].strip()
    if "–" in text:
        low, high = text.split("–", 1)
        scale = 1.0
        if "×" in high:
            high, power = high.split("×", 1)
            scale = _number("1×" + power.strip())
        return "range", (_number(low) * scale, _number(high) * scale)
    return ("approximate" if approximate else "value"), _number(text)


def _held(row: object, field: str, scale: float = 1.0) -> tuple[str, object]:
    """What the catalogue holds for one field, in the same shape as :func:`_cell`."""
    if field in getattr(row, "ranges", {}):
        low, high = row.ranges[field]
        return "range", (low / scale, high / scale)
    value = getattr(row, field)
    if value is None or row.is_derived(field):
        # Not read off the page: absent, or computed from the row's other
        # cells, which a solid row does for the speeds a page leaves out.
        return "rule", None
    kind = "approximate" if field in getattr(row, "approximate", ()) else "value"
    return kind, value / scale


def _same(printed: tuple[str, object], held: tuple[str, object]) -> bool:
    if printed[0] != held[0]:
        return False
    if printed[1] is None:
        return held[1] is None
    if isinstance(printed[1], tuple):
        return all(
            math.isclose(a, b, rel_tol=1e-9)
            for a, b in zip(printed[1], held[1], strict=True)
        )
    return math.isclose(printed[1], held[1], rel_tol=1e-9)


def _rows(catalogue: object, table: str) -> list[object]:
    return [row for key, row in catalogue.items() if key.startswith(f"{table}/")]


def _named(catalogue: object, table: str, name: str) -> object:
    return next(row for row in _rows(catalogue, table) if row.name == name)


# ---------------------------------------------------------------------------
# Norton & Karczub Appendix 4 A: solids
# ---------------------------------------------------------------------------
APPENDIX_A = "norton-karczub-2003-appendix-4a"
APPENDIX_A_FIELDS = (
    "density_kg_m3",
    "youngs_modulus_pa",
    "poisson_ratio",
    "bar_longitudinal_speed_m_s",
    "bulk_longitudinal_speed_m_s",
)


def test_the_appendix_holds_every_solid_the_page_prints() -> None:
    assert (
        len(_rows(PUBLISHED_SOLIDS, APPENDIX_A))
        == len(ref.NORTON_KARCZUB_APPENDIX_4A)
        == 21
    )


@pytest.mark.parametrize("printed", ref.NORTON_KARCZUB_APPENDIX_4A, ids=lambda r: r[0])
def test_every_appendix_cell_is_the_printed_one(
    printed: tuple[str, tuple[str, ...]],
) -> None:
    name, cells = printed
    row = _named(PUBLISHED_SOLIDS, APPENDIX_A, name)
    for field, text in zip(APPENDIX_A_FIELDS, cells, strict=False):
        if field in row.misprinted:
            continue
        assert _same(_cell(text), _held(row, field)), f"{name}.{field}: page {text!r}"


def test_the_last_appendix_column_is_held_as_printed() -> None:
    """The product of critical frequency and thickness is c_air^2 / (1.8 c).

    The page derives it from the speed beside it, the bar speed where the page
    gives one and the bulk speed where it does not, with its own 1.8 for the
    plate's 2 pi / sqrt(12) and no Poisson correction. That is an
    approximation this library does not make, so the column is held as the
    page prints it and marked as printed, and the page's own arithmetic is
    checked to reproduce it to within the rounding the page applied.
    """
    checked = 0
    for name, cells in ref.NORTON_KARCZUB_APPENDIX_4A:
        printed = _cell(cells[5])[1]
        row = _named(PUBLISHED_SOLIDS, APPENDIX_A, name)
        assert row.thickness_critical_frequency_product_m_hz == printed, name
        assert not row.is_derived("thickness_critical_frequency_product_m_hz")
        bar, bulk = cells[3], cells[4]
        # The printed bar speed where there is one, the printed bulk speed
        # where there is not; never a speed this library derived, which for
        # soft rubber differs from the printed one by a factor of fourteen.
        speed = _number(bar) if bar.strip() not in _RULES else _number(bulk)
        assert _AIR_SPEED_M_S**2 / (1.8 * speed) == pytest.approx(printed, rel=6e-3), (
            name
        )
        checked += 1
    assert checked == 21


def test_the_cork_modulus_is_refused_and_says_why() -> None:
    """The page gives cork the modulus it also gives Pyrex, a thousand too large."""
    cork = _named(PUBLISHED_SOLIDS, APPENDIX_A, "Cork")
    pyrex = _named(PUBLISHED_SOLIDS, APPENDIX_A, "Glass (Pyrex)")
    assert cork.youngs_modulus_pa is None
    assert "ERRATA" in cork.why_missing("youngs_modulus_pa")
    # The rest of the cork row is what contradicts the printed exponent.
    implied = cork.density_kg_m3 * cork.bulk_longitudinal_speed_m_s**2
    assert implied == pytest.approx(6.25e7)
    assert pyrex.youngs_modulus_pa == pytest.approx(6.2e10)
    assert pyrex.youngs_modulus_pa / implied > 900


# ---------------------------------------------------------------------------
# Norton & Karczub Table 6.1 and Table 3.1
# ---------------------------------------------------------------------------
TABLE_61 = "norton-karczub-2003-table-6-1"
TABLE_31 = "norton-karczub-2003-table-3-1"


@pytest.mark.parametrize("printed", ref.NORTON_KARCZUB_6_1, ids=lambda r: r[0])
def test_every_loss_factor_is_the_printed_one(
    printed: tuple[str, tuple[str, ...]],
) -> None:
    name, (text,) = printed
    row = _named(PUBLISHED_SOLIDS, TABLE_61, name)
    assert _same(_cell(text), _held(row, "loss_factor")), f"{name}: page {text!r}"


def test_a_row_the_page_prints_for_two_materials_stays_one_row() -> None:
    assert [row.name for row in _rows(PUBLISHED_SOLIDS, TABLE_61)].count(
        "Brick, concrete"
    ) == 1


@pytest.mark.parametrize("printed", ref.NORTON_KARCZUB_3_1, ids=lambda r: r[0])
def test_every_plateau_constant_is_the_printed_one(
    printed: tuple[str, tuple[str, ...]],
) -> None:
    name, (sigma, height, ratio) = printed
    row = _named(PUBLISHED_PLATEAU_DATA, TABLE_31, name)
    assert row.surface_density_per_mm_kg_m2 == pytest.approx(float(sigma))
    assert row.coincidence_height_db == pytest.approx(float(height))
    assert row.plateau_frequency_ratio == pytest.approx(float(ratio))


def test_the_plateau_catalogue_holds_all_eight_rows() -> None:
    assert len(PUBLISHED_PLATEAU_DATA) == len(ref.NORTON_KARCZUB_3_1) == 8
    assert solids.plateau_material_named("steel")[0].name == "Steel"
    assert solids.plateau_material_named("unobtainium") == ()


# ---------------------------------------------------------------------------
# Vigran Table 3.1
# ---------------------------------------------------------------------------
VIGRAN = "vigran-2008-table-3-1"
#: Field and the factor the column heading names: the modulus column is in
#: 10^9 Pa and the loss factor column in units of 10^-3.
VIGRAN_FIELDS = (
    ("density_kg_m3", 1.0),
    ("youngs_modulus_pa", 1e9),
    ("poisson_ratio", 1.0),
    ("loss_factor", 1e-3),
)


@pytest.mark.parametrize("printed", ref.VIGRAN_3_1, ids=lambda r: r[0])
def test_every_vigran_cell_is_the_printed_one_in_the_headings_units(
    printed: tuple[str, tuple[str, ...]],
) -> None:
    name, cells = printed
    row = _named(PUBLISHED_SOLIDS, VIGRAN, name)
    for (field, scale), text in zip(VIGRAN_FIELDS, cells, strict=True):
        if field in row.misprinted:
            continue
        assert _same(_cell(text), _held(row, field, scale)), (
            f"{name}.{field}: page {text!r}"
        )


def test_the_aluminium_poisson_ratio_is_refused_and_says_why() -> None:
    aluminium = _named(PUBLISHED_SOLIDS, VIGRAN, "Aluminium")
    assert aluminium.poisson_ratio is None
    assert "poisson_ratio" not in aluminium.ranges
    assert "034" in aluminium.why_missing("poisson_ratio")
    assert "ERRATA" in aluminium.why_missing("poisson_ratio")


def test_the_one_static_modulus_says_so() -> None:
    """Footnote 2 makes one cell static in a column footnote 1 makes dynamic."""
    aerated = _named(PUBLISHED_SOLIDS, VIGRAN, "Concrete (autoclaved aerated)")
    assert "static" in aerated.note
    others = [row for row in _rows(PUBLISHED_SOLIDS, VIGRAN) if row is not aerated]
    assert all("static" not in row.note for row in others)


def test_the_static_modulus_derives_no_dynamic_quantity() -> None:
    """A wave speed is dynamic, and this row's modulus is not.

    Every other row of the table derives its three speeds, a shear modulus and
    a critical frequency from its dynamic modulus. Doing it here would put a
    static modulus into a dynamic quantity, so each of those says why it is
    empty instead.
    """
    aerated = _named(PUBLISHED_SOLIDS, VIGRAN, "Concrete (autoclaved aerated)")
    assert dict(aerated.derived) == {}
    for field in (
        "shear_modulus_pa",
        "bar_longitudinal_speed_m_s",
        "plate_longitudinal_speed_m_s",
        "bulk_longitudinal_speed_m_s",
        "transverse_speed_m_s",
        "thickness_critical_frequency_product_m_hz",
    ):
        assert getattr(aerated, field) is None
        assert "static" in aerated.why_missing(field)


# ---------------------------------------------------------------------------
# Norton & Karczub Appendix 4 B and C: liquids and gases
# ---------------------------------------------------------------------------
APPENDIX_BC = "norton-karczub-2003-appendix-4bc"


def _fluid(name: str, temperature_c: float) -> object:
    return next(
        state
        for key, state in PUBLISHED_FLUIDS.items()
        if key.startswith(f"{APPENDIX_BC}/")
        and state.model.startswith(f"{name} as printed")
        and state.temperature_c == pytest.approx(temperature_c)
    )


@pytest.mark.parametrize(
    "printed",
    ref.NORTON_KARCZUB_APPENDIX_4B + ref.NORTON_KARCZUB_APPENDIX_4C,
    ids=lambda r: f"{r[0]}-{r[1][1]}",
)
def test_every_fluid_state_is_the_printed_one(
    printed: tuple[str, tuple[str, ...]],
) -> None:
    name, (density, temperature, gamma, speed) = printed
    state = _fluid(name, float(temperature))
    assert state.density == pytest.approx(_number(density))
    assert state.speed_of_sound == pytest.approx(_number(speed))
    if gamma.strip() in _RULES:
        with pytest.raises(
            fluids.FluidPropertyUnavailable, match="heat_capacity_ratio"
        ):
            _ = state.heat_capacity_ratio
    else:
        assert state.heat_capacity_ratio == pytest.approx(_number(gamma))


def test_a_repeated_density_says_so_on_the_state_itself() -> None:
    """A state has no note, so the row's note follows the table's hedge.

    The page prints hydrogen and oxygen with one density at two temperatures;
    a caller who reads those four states has to be told, and a note left in
    the data file would have told nobody.
    """
    for name in ("Hydrogen", "Oxygen"):
        for temperature in (0.0, 20.0):
            validity = _fluid(name, temperature).validity
            assert validity.startswith("Norton & Karczub say of Appendix 4")
            assert "same density" in validity
    assert "same density" not in _fluid("Air", 20.0).validity


def test_each_fluid_table_carries_its_own_books_hedge() -> None:
    """The Bies hedge used to be applied to every table the loader read."""
    appendix = _fluid("Air", 20.0)
    bies = PUBLISHED_FLUIDS["bies-2017-table-c1-fluids/air"]
    assert "Norton & Karczub" in appendix.validity
    assert "representative only" not in appendix.validity
    assert "representative only" in bies.validity


# ---------------------------------------------------------------------------
# Rossing Table 15.5: orthotropic wood
# ---------------------------------------------------------------------------
#: The printed symbol, the row field it becomes, and the factor to pascals.
ROSSING_FIELDS = {
    "ρ": ("density_kg_m3", 1.0),
    "D₁": ("plate_stiffness_d1_pa", 1e6),
    "D₂": ("plate_stiffness_d2_pa", 1e6),
    "D₃": ("plate_stiffness_d3_pa", 1e6),
    "D₄": ("plate_stiffness_d4_pa", 1e6),
}


@pytest.mark.parametrize("wood", ["Spruce", "Maple"])
def test_the_turned_table_is_the_printed_one(wood: str) -> None:
    """The page prints the woods as columns; the catalogue keys them as rows."""
    row = solids.orthotropic_wood_named(wood)[0]
    column = 2 if wood == "Spruce" else 3
    for printed in ref.ROSSING_15_5:
        symbol = printed[0]
        text = printed[column]
        if symbol in ROSSING_FIELDS:
            field, scale = ROSSING_FIELDS[symbol]
            assert getattr(row, field) == pytest.approx(
                float(text.rstrip("*")) * scale
            ), symbol
            assert (row.basis_of(field) == "estimated") is text.endswith("*"), symbol
        else:
            assert row.relative_scaling_factor == pytest.approx(float(text))


def test_only_the_two_asterisked_maple_cells_are_estimates() -> None:
    maple = solids.orthotropic_wood_named("maple")[0]
    spruce = solids.orthotropic_wood_named("spruce")[0]
    assert dict(maple.basis) == {
        "plate_stiffness_d2_pa": "estimated",
        "plate_stiffness_d4_pa": "estimated",
    }
    assert dict(spruce.basis) == {}
    assert len(PUBLISHED_ORTHOTROPIC_WOOD) == 2


def test_the_scaling_factor_follows_the_printed_relation_except_on_maple() -> None:
    """The same row prints the relation, the fourth root of D1 over D3.

    It holds for spruce to the digit the page prints. For maple it does not:
    860 and 170, neither asterisked, give 1.50 and the page prints 1.4. Both
    are served as printed, maple carries a note, and the defect is registered
    in the errata. Naming the exception here keeps it a documented one, so a
    second row breaking the relation fails rather than passing unseen.
    """
    broken = set()
    for row in PUBLISHED_ORTHOTROPIC_WOOD.values():
        computed = (row.plate_stiffness_d1_pa / row.plate_stiffness_d3_pa) ** 0.25
        if round(computed, 1) != pytest.approx(row.relative_scaling_factor):
            broken.add(row.name)
    assert broken == {"Maple"}
    maple = solids.orthotropic_wood_named("maple")[0]
    assert "1.50" in maple.note
    assert "ERRATA" in maple.note


def test_the_constants_are_the_ones_equation_15_86_defines() -> None:
    """D1 and D3 are the two directions, D2 the coupling, D4 the twisting.

    Along the grain over across it is D1 over D3, which puts spruce at
    thirteen, and the scaling factor the page prints beside it is the fourth
    root of that same ratio. The coupling term D2 is the smallest of the
    four in spruce; read as "across the grain" it would give sixteen.
    """
    spruce = PUBLISHED_ORTHOTROPIC_WOOD["rossing-2014-table-15-5/spruce"]
    along = spruce.plate_stiffness_d1_pa
    across = spruce.plate_stiffness_d3_pa
    assert along / across == pytest.approx(13.1, abs=0.05)
    assert (along / across) ** 0.25 == pytest.approx(
        spruce.relative_scaling_factor, abs=0.05
    )
    assert spruce.plate_stiffness_d2_pa == min(
        spruce.plate_stiffness_d1_pa,
        spruce.plate_stiffness_d2_pa,
        spruce.plate_stiffness_d3_pa,
        spruce.plate_stiffness_d4_pa,
    )


def test_the_table_credits_woodhouse_on_every_row() -> None:
    assert all(
        row.attributed_to == {"table": "Woodhouse [15.77]"}
        for row in PUBLISHED_ORTHOTROPIC_WOOD.values()
    )
