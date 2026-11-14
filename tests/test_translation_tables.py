#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A blank Spanish entry is no translation, in every table that holds one.

The catalogue generator took an entry of ``catalogue-es.json`` written as an
empty string for the Spanish of a row's name, and the Spanish page printed the
row with no name, no error raised and nothing reported missing. The plates and
the reports read their own tables the same way, each taking any value it found
under the English key, and each now reads a blank entry as no entry. The
figures' lookup is left as it is, since the clips are fingerprinted with the
code they reach and it is part of it; that table, like the other three, is
held to holding no blank entry, which is what keeps a blank out of a figure.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import diagrams.i18n as plates
import figures.i18n as figures
import generate_catalogue_data as catalogue

from phonometry._report import _i18n as reports

# The figure and plate tables come with the figure tooling, whose stack is
# pinned and kept off the dependency floors.
pytestmark = pytest.mark.pinned_stack

#: Values a reader would take for a word and print as nothing.
BLANKS = ["", " ", "\t", "\u00a0"]


def test_no_table_holds_a_blank_spanish_entry() -> None:
    """The four tables the Spanish pages, figures, plates and reports read."""
    tables = {
        "catalogue-es.json": json.loads(catalogue.SPANISH.read_text(encoding="utf-8")),
        "diagrams/i18n.py _ES": plates._ES,
        "figures/i18n.py _ES_EXACT": figures._ES_EXACT,
        "_report/_i18n.py _STRINGS": reports._STRINGS,
    }
    blank = {
        name: sorted(key for key, value in table.items() if not value.strip())
        for name, table in tables.items()
    }
    assert blank == {name: [] for name in tables}
    # A figure label a pattern rewrites takes the pattern's replacement.
    assert [
        pattern
        for pattern, replacement in figures._ES_PATTERNS
        if not str(replacement).strip()
    ] == []


@pytest.mark.parametrize("value", BLANKS)
def test_a_plate_label_with_a_blank_entry_stays_english(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """The ``_es`` plate drew nothing where the English one draws the label."""
    monkeypatch.setitem(plates._ES, "A label", value)
    assert plates.lookup("A label", translate=True) == "A label"


@pytest.mark.parametrize("value", BLANKS)
def test_a_report_string_with_a_blank_entry_stays_english(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """The Spanish report printed nothing where the English one prints the string."""
    monkeypatch.setitem(reports._STRINGS, "A string", value)
    assert reports.t("A string", "es") == "A string"
