#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Resilient moduli, damping treatments and carpets, against a second reading.

The oracle in :mod:`tests.reference_data.wave4_materials` holds each cell of
Vigran (2008) Table 8.3, Harris (1977) Table 14.2 and Harris 3e Tables 30.2 and
30.3 as the page prints it. These tests read every value back out of the three
catalogues, and pin the hedges each table needed: ranges, the approximate
density, the static load of the moduli, the word "No" in a bonded area, and the
pile weights whose two printed halves are not each other.
"""

from __future__ import annotations

import math
import re

import pytest
import reference_data as ref

from phonometry import materials, solids
from phonometry.materials import (
    PUBLISHED_CARPETS,
    PUBLISHED_RESILIENT_MODULI,
    carpets_named,
    resilient_moduli_named,
)
from phonometry.solids import PUBLISHED_DAMPING_TREATMENTS, damping_treatments_named

#: One ounce per square yard, in kilograms per square metre, by definition.
OZ_YD2_KG_M2 = 0.45359237 / 16 / 0.9144**2


def _num(cell: str) -> float:
    return float(cell.replace(",", ".").strip())


def _span(cell: str) -> tuple[float, float] | None:
    parts = re.split(r"\s*[–-]\s*", cell.strip())
    return (_num(parts[0]), _num(parts[1])) if len(parts) == 2 else None


# ---------------------------------------------------------------------------
# Vigran Table 8.3
# ---------------------------------------------------------------------------
def test_every_modulus_and_density_is_the_printed_one() -> None:
    rows = list(PUBLISHED_RESILIENT_MODULI.values())
    assert [row.name for row in rows] == [label for label, _ in ref.VIGRAN_8_3]
    for row, (_label, (density, modulus)) in zip(rows, ref.VIGRAN_8_3, strict=True):
        low, high = _span(modulus)
        assert row.dynamic_youngs_modulus_pa is None
        assert row.ranges["dynamic_youngs_modulus_pa"] == pytest.approx(
            (low * 1e6, high * 1e6)
        )
        if density.startswith("approx."):
            assert row.density_kg_m3 == _num(density.removeprefix("approx."))
            assert row.is_approximate("density_kg_m3")
        else:
            assert row.density_kg_m3 is None
            assert row.ranges["density_kg_m3"] == _span(density)


def test_every_modulus_carries_the_load_the_heading_prints() -> None:
    for row in PUBLISHED_RESILIENT_MODULI.values():
        assert row.static_load_pa == 2000
        assert row.is_approximate("static_load_pa")


def test_the_two_rock_wools_are_told_apart_by_their_densities() -> None:
    first, second = resilient_moduli_named("rock wool")
    assert first.name == second.name == "Rock wool"
    assert first.ranges["density_kg_m3"] != second.ranges["density_kg_m3"]


# ---------------------------------------------------------------------------
# Harris (1977) Table 14.2
# ---------------------------------------------------------------------------
def test_every_treatment_holds_the_printed_decay_area_and_weight() -> None:
    rows = list(PUBLISHED_DAMPING_TREATMENTS.values())
    assert len(rows) == len(ref.HARRIS_1977_14_2) == 8
    for row, (label, (decay, area, weight)) in zip(
        rows, ref.HARRIS_1977_14_2, strict=True
    ):
        assert row.name == label.rstrip(" *")
        assert row.temperature_c == 21
        for field, cell in (
            ("decay_rate_db_s", decay),
            ("surface_density_kg_m2", weight),
        ):
            printed = _span(cell)
            if printed:
                assert getattr(row, field) is None
                assert row.ranges[field] == printed
            else:
                assert getattr(row, field) == _num(cell)
        if area == "No":
            assert row.adhered_area_percent is None
            assert "No" in row.why_missing("adhered_area_percent")
        else:
            assert row.adhered_area_percent == _num(area)


def test_the_two_loose_treatments_carry_the_footnote() -> None:
    loose = [row for row in PUBLISHED_DAMPING_TREATMENTS.values() if row.variant]
    assert [row.variant for row in loose] == ["sin adhesivo", "sin adhesivo"]
    assert all("pintura del suelo del automóvil" in row.note for row in loose)


def test_the_lookup_matches_the_spanish_description() -> None:
    assert len(damping_treatments_named("MUESCADO")) == 3
    assert damping_treatments_named("viscoelastic") == ()


# ---------------------------------------------------------------------------
# Harris 3e Tables 30.2 and 30.3
# ---------------------------------------------------------------------------
def _pair(cell: str) -> tuple[str, str]:
    si, _, us = cell.partition("(")
    return si.strip(), us.rstrip(")").strip()


def _holds(si: str, us: str) -> bool:
    """The Chapter 32 criterion: rounded or truncated to the printed precision."""
    converted = _num(us) * OZ_YD2_KG_M2
    decimals = len(si.split(",")[1]) if "," in si else 0
    scale = 10**decimals
    return _num(si) in {
        round(converted, decimals),
        math.floor(converted * scale) / scale,
    }


@pytest.mark.parametrize(
    ("table", "oracle", "mounting"),
    [
        ("harris-1995-table-30-2", ref.HARRIS_30_2, "Sobre hormigón desnudo"),
        ("harris-1995-table-30-3", ref.HARRIS_30_3, "Sobre un relleno"),
    ],
)
def test_every_carpet_holds_the_printed_pile_and_rating(
    table: str, oracle: tuple[tuple[str, tuple[str, ...]], ...], mounting: str
) -> None:
    rows = [row for row in PUBLISHED_CARPETS.values() if row.table == table]
    assert len(rows) == len(oracle)
    for row, (label, (_weight, height, surface, fibre, nrc)) in zip(
        rows, oracle, strict=True
    ):
        assert (row.name, row.pile_surface, row.fibre) == (label, surface, fibre)
        assert row.variant == f"{surface}, {fibre.lower()}"
        assert row.mounting.startswith(mounting)
        assert row.noise_reduction_coefficient == _num(nrc)
        si_height, _ = _pair(height)
        if _span(si_height):
            assert row.ranges["pile_height_mm"] == _span(si_height)
        else:
            assert row.pile_height_mm == _num(si_height)


def test_a_pile_weight_whose_halves_disagree_serves_nothing() -> None:
    """Four pairs of Table 30.2 fail; the fifth lost a digit in its ounces."""
    rows = [row for row in PUBLISHED_CARPETS.values() if row.table.endswith("30-2")]
    failed = []
    for row, (_label, (weight, *_rest)) in zip(rows, ref.HARRIS_30_2, strict=True):
        si, us = _pair(weight)
        if _holds(si, us):
            assert row.pile_weight_kg_m2 == _num(si)
        elif us == "3,2":
            # 32 oz/yd2 printed with a stray comma; Table 30.3 prints "1,1 (32)".
            assert row.pile_weight_kg_m2 == _num(si)
            assert "ERRATA" in row.note
        else:
            failed.append(weight)
            assert row.pile_weight_kg_m2 is None
            assert "ERRATA" in row.why_missing("pile_weight_kg_m2")
    assert failed == ["1,3 (32)", "2,3 (66)", "3,1 (88)", "2,1 (60)"]


def test_three_of_the_failing_pairs_follow_a_factor_of_0_035() -> None:
    """The arithmetic the errata entry states, checked on every pair."""
    pairs = [_pair(cells[0]) for _label, cells in (*ref.HARRIS_30_2, *ref.HARRIS_30_3)]
    at_0_035 = {(si, us) for si, us in pairs if _num(si) == round(_num(us) * 0.035, 1)}
    exact = {(si, us) for si, us in pairs if _holds(si, us)}
    assert at_0_035 - exact == {
        ("2,3", "66"),
        ("3,1", "88"),
        ("2,1", "60"),
    }
    assert ("1,3", "32") not in at_0_035 | exact
    # And the factor reproduces every pair that does hold.
    assert exact <= at_0_035


def test_every_pair_of_table_30_3_holds() -> None:
    for _label, (weight, *_rest) in ref.HARRIS_30_3:
        assert _holds(*_pair(weight))


def test_the_lookup_matches_construction_surface_and_fibre() -> None:
    assert len(carpets_named("nylon")) == 3
    assert {row.name for row in carpets_named("de nudo")} == {"De nudo"}
    assert carpets_named("RIZO") == carpets_named("rizo")


def test_the_catalogues_are_reachable_where_the_page_says() -> None:
    assert materials.PUBLISHED_CARPETS is PUBLISHED_CARPETS
    assert materials.PUBLISHED_RESILIENT_MODULI is PUBLISHED_RESILIENT_MODULI
    assert solids.PUBLISHED_DAMPING_TREATMENTS is PUBLISHED_DAMPING_TREATMENTS
