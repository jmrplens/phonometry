#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every published cell is the baseline's, or a listed change made it so.

``tests/catalogue_fingerprint.py`` says why the baseline exists and how a
change to a published cell is written down. These tests hold the library to
it: a cell that moves without a step fails here, and so does a step that
claims a move the library did not make.
"""

from __future__ import annotations

import json

import catalogue_fingerprint as fp


def _text(value: object) -> str:
    """*value* as the baseline writes it, so a type change is a change.

    Python holds ``2700 == 2700.0`` and ``True == 1``, so comparing the parsed
    dumps would let a published float turn into an integer, or a flag into a
    number, without a word. Their text differs, and the text is what the
    baseline file holds.
    """
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _first_difference(expected: dict[str, object], live: dict[str, object]) -> str:
    """The first field two dumps of one row disagree on, for the message."""
    for field in sorted(set(expected) | set(live)):
        if _text(expected.get(field)) != _text(live.get(field)):
            return (
                f"{field}: expected {_text(expected.get(field))}"
                f", built {_text(live.get(field))}"
            )
    return "no field differs"


def test_the_baseline_holds_every_row_the_catalogues_published() -> None:
    """The dump the changes start from covers the 1982 rows of 23 mappings."""
    catalogues = fp.baseline()
    assert len(catalogues) == 23
    assert sum(len(rows) for rows in catalogues.values()) == 1982


def test_the_baseline_reads_back_as_it_is_rendered() -> None:
    """One row per line, and the file is still the JSON it claims to be."""
    catalogues = fp.baseline()
    assert fp.render(catalogues) == fp.BASELINE.read_text(encoding="utf-8")


def test_every_published_mapping_is_in_the_fingerprint() -> None:
    """A catalogue published after the baseline would need a step of its own."""
    assert sorted(fp.dump()) == sorted(fp.expected())


def test_every_published_row_is_the_baseline_carried_through_the_changes() -> None:
    """Same rows, same order, and every field of every row to the last digit.

    ``generate_catalogue_data.py --check`` catches a number the page would
    print differently; this catches the last digit of a float, which the page
    never shows, a float served as an integer, which the page prints the
    same, and a hedge moved from one field to another. Rows are compared as
    the text the baseline holds, not as parsed values, for the reason
    :func:`_text` gives.
    """
    expected = fp.expected()
    live = fp.dump()
    for name, rows in expected.items():
        assert list(live[name]) == list(rows), f"{name}: the keys or their order moved"
        for key, row in rows.items():
            built = live[name][key]
            assert _text(built) == _text(row), (
                f"{name}[{key!r}]: {_first_difference(row, built)}"
            )


def test_a_float_served_as_an_integer_is_a_change() -> None:
    """The comparison sees the type of a number, not only its value."""
    row = {"density_kg_m3": 2700.0, "flag": True}
    served = {"density_kg_m3": 2700, "flag": 1}

    assert row == served
    assert _text(row) != _text(served)
    assert _first_difference(row, served).startswith("density_kg_m3: expected 2700.0")


def test_one_row_shape_moves_the_cells_it_lists_and_no_others() -> None:
    """The step that gave every row one shape moved 54 rows, and this is which.

    Thirty-five estimated cells in twenty-two rows (Hopkins Table A2 and the
    maple of Rossing Table 15.5) became ``basis``; the 116 Fahrenheit and psi
    cells of Ver and Beranek Table 14.1 and the nine sabin cells of Long
    Table 7.1 became ``converted``; the 21 values the pages give by reference
    to another row, 18 cells left blank under a block and the three rows of
    Harris that print "Parecido al anterior" and no row number, became
    ``carried``. A step that grew to touch one more row would fail here
    before it failed anywhere else.
    """
    before = fp.baseline()
    after = fp.one_row_shape(before)
    moved: dict[tuple[str, str], list[int]] = {}
    for name, rows in after.items():
        for row in rows.values():
            for hedge in ("basis", "converted", "carried"):
                if hedge in row:
                    count = moved.setdefault((hedge, name), [0, 0])
                    count[0] += 1
                    count[1] += len(row[hedge])
    assert moved == {
        ("basis", "PUBLISHED_ORTHOTROPIC_WOOD"): [1, 2],
        ("basis", "PUBLISHED_SOLIDS"): [21, 33],
        ("carried", "PUBLISHED_DUCT_TRANSMISSION_LOSS"): [2, 2],
        ("carried", "PUBLISHED_FLOW_RESISTANCE"): [8, 16],
        ("carried", "PUBLISHED_IMPACT_INSULATION"): [3, 3],
        ("converted", "PUBLISHED_ABSORPTION_AREAS"): [2, 9],
        ("converted", "PUBLISHED_DAMPING"): [17, 116],
    }
    changed = sum(
        before[name][key] != after[name][key] for name in before for key in before[name]
    )
    assert changed == 54
    # Only the hedges this step moves, and the notes that described them,
    # may differ: a number that changed along with the step would pass the
    # count above and the comparison with the live rows below.
    moves = {"estimated", "derived", "basis", "converted", "carried", "note"}
    for name, rows in before.items():
        for key, row in rows.items():
            kept_before = {f: v for f, v in row.items() if f not in moves}
            kept_after = {f: v for f, v in after[name][key].items() if f not in moves}
            assert kept_after == kept_before, f"{name}[{key!r}]"


def test_resilient_layer_row_moves_the_fifteen_layers_and_no_others() -> None:
    """The step that made the resilient layers rows touched their fifteen only.

    Each row of Hopkins Table A3 gained the table half of its key and a
    ``table``, the credit of the four rebond foams became a mapping, and the
    four density cells the page prints blank say which row prints them; every
    other mapping comes out of the step as it went in, and so does every
    number of the fifteen.
    """
    before = fp.one_row_shape(fp.baseline())
    after = fp.resilient_layer_row(before)
    assert {name for name in before if before[name] != after[name]} == {
        "PUBLISHED_RESILIENT_LAYERS"
    }
    old = before["PUBLISHED_RESILIENT_LAYERS"]
    new = after["PUBLISHED_RESILIENT_LAYERS"]
    assert list(new) == [f"hopkins-2007-table-a3/{key}" for key in old]
    moved = {"table", "attributed_to", "carried"}
    for key, row in old.items():
        built = new[f"hopkins-2007-table-a3/{key}"]
        assert built["table"] == "hopkins-2007-table-a3"
        assert _text({f: v for f, v in built.items() if f not in moved}) == _text(
            {f: v for f, v in row.items() if f not in moved}
        )
        assert "apparent_dynamic_stiffness_n_m3" not in built
    credited = [row["attributed_to"] for row in new.values() if "attributed_to" in row]
    assert credited == [{"row": "Hopkins and Hall (2006)"}] * 4
    carried = {key: row["carried"] for key, row in new.items() if "carried" in row}
    assert carried == {
        f"hopkins-2007-table-a3/{key}": {"density_kg_m3": text}
        for key, text in fp.RESILIENT_LAYER_CARRIED.items()
    }
    assert sorted(fp.RESILIENT_LAYER_CARRIED) == [
        "mineral_wool_glass_36_25",
        "mineral_wool_glass_75_40",
        "rebond_foam_64_15",
        "rebond_foam_64_25",
    ]


def test_row_contract_moves_the_six_percent_porosities_and_no_others() -> None:
    """The step that made rows check themselves moved six cells, and no number.

    Cox Table 6.7 prints six porosities in per cent in a column of fractions;
    each moved from ``porosity`` to ``porosity_percent`` with its digits, the
    one ``± 4`` with it. Every other mapping and every other row comes out of
    the step as it went in.
    """
    before = fp.resilient_layer_row(fp.one_row_shape(fp.baseline()))
    after = fp.row_contract(before)
    assert {name for name in before if before[name] != after[name]} == {
        "PUBLISHED_GROUND"
    }
    old, new = before["PUBLISHED_GROUND"], after["PUBLISHED_GROUND"]
    assert list(new) == list(old)
    changed = sorted(key for key in old if old[key] != new[key])
    assert changed == sorted(fp.GROUND_POROSITY_IN_PER_CENT)
    moved = {
        key: (new[key]["porosity_percent"], new[key].get("uncertainty", {}))
        for key in changed
    }
    assert {key: value for key, (value, _) in moved.items()} == {
        key: old[key]["porosity"] for key in changed
    }
    for key in changed:
        assert "porosity" not in new[key]
        assert "porosity" not in new[key].get("uncertainty", {})
        kept = {"porosity", "porosity_percent", "uncertainty", "note"}
        assert _text({f: v for f, v in new[key].items() if f not in kept}) == _text(
            {f: v for f, v in old[key].items() if f not in kept}
        )
    assert sorted(value for value, _ in moved.values()) == [
        26.9,
        36.5,
        37.5,
        38.9,
        48.0,
        58.1,
    ]
    assert new["cox-2017-table-6-7/grass_root_layer_in_loamy_sand"]["uncertainty"] == {
        "flow_resistivity_pa_s_m2": 90000.0,
        "porosity_percent": 4.0,
    }
