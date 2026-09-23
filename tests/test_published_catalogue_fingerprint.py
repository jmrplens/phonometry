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


def _first_difference(expected: dict[str, object], live: dict[str, object]) -> str:
    """The first field two dumps of one row disagree on, for the message."""
    for field in sorted(set(expected) | set(live)):
        if expected.get(field) != live.get(field):
            return (
                f"{field}: expected {json.dumps(expected.get(field), ensure_ascii=False)}"
                f", built {json.dumps(live.get(field), ensure_ascii=False)}"
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
    never shows, and a hedge moved from one field to another.
    """
    expected = fp.expected()
    live = fp.dump()
    for name, rows in expected.items():
        assert list(live[name]) == list(rows), f"{name}: the keys or their order moved"
        for key, row in rows.items():
            built = live[name][key]
            assert built == row, f"{name}[{key!r}]: {_first_difference(row, built)}"
