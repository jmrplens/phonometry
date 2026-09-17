#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the packaged-table reader (``phonometry._internal.catalogue``).

A catalogue is the one place in this library where a wrong character is
invisible. A wrong formula fails an oracle; a row whose key was typed twice,
or whose citation was dropped, produces a catalogue that imports cleanly and
is quietly missing a material. The reader is therefore strict at import time
about the three things nothing downstream can recover from: a document that
does not say where it came from, a table with nothing in it, and two rows
answering to the same name.

The reader is also what keeps the citation single. It is read from the file
that holds the rows, so the provenance gate and the published record cannot
disagree: there is only one copy to be right or wrong.
"""

from __future__ import annotations

import json

import pytest

from phonometry._internal.catalogue import CatalogueError, read_table, take


def _packaged(monkeypatch: pytest.MonkeyPatch, document: dict[str, object]) -> None:
    """Make ``read_table`` see *document* instead of a file on disk."""

    class _Entry:
        def __truediv__(self, other: str) -> _Entry:
            return self

        def read_text(self, encoding: str = "utf-8") -> str:
            return json.dumps(document)

    monkeypatch.setattr("importlib.resources.files", lambda _: _Entry())


def _document(**overrides: object) -> dict[str, object]:
    """A minimal well-formed table, for a test to break one part of."""
    base: dict[str, object] = {
        "source": "Hopkins (2007) Table A2, PDF page 635 (printed p. 607)",
        "about": "why this page was read the way it was",
        "rows": [{"key": "steel", "name": "Steel"}],
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize("missing", ["source", "about", "rows"])
def test_a_document_missing_a_top_level_key_is_refused(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    document = _document()
    del document[missing]
    _packaged(monkeypatch, document)
    with pytest.raises(CatalogueError, match=f"needs a top-level {missing!r}"):
        read_table("phonometry.solids", "table.json")


def test_a_table_with_no_rows_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    _packaged(monkeypatch, _document(rows=[]))
    with pytest.raises(CatalogueError, match="publishes nothing"):
        read_table("phonometry.solids", "table.json")


def test_a_row_without_a_key_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    _packaged(monkeypatch, _document(rows=[{"name": "Steel"}]))
    with pytest.raises(CatalogueError, match="every row needs a key"):
        read_table("phonometry.solids", "table.json")


def test_two_rows_sharing_a_key_are_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [{"key": "steel", "name": "Steel"}, {"key": "steel", "name": "Mild steel"}]
    _packaged(monkeypatch, _document(rows=rows))
    with pytest.raises(CatalogueError, match="two rows share the key 'steel'"):
        read_table("phonometry.solids", "table.json")


def test_the_file_name_is_in_every_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    """The caller sees a package and a file name, never the text that failed."""
    _packaged(monkeypatch, _document(rows=[]))
    with pytest.raises(CatalogueError, match="^hopkins-2007-table-a2.json: "):
        read_table("phonometry.solids", "hopkins-2007-table-a2.json")


def test_the_rows_keep_the_order_the_file_lists_them_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [{"key": name} for name in ("brick", "aircrete", "steel")]
    _packaged(monkeypatch, _document(rows=rows))
    _, read = read_table("phonometry.solids", "table.json")
    assert [row["key"] for row in read] == ["brick", "aircrete", "steel"]


def test_the_citation_comes_back_as_the_file_wrote_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _packaged(monkeypatch, _document())
    source, _ = read_table("phonometry.solids", "table.json")
    assert source == "Hopkins (2007) Table A2, PDF page 635 (printed p. 607)"


def test_take_drops_the_key_and_keeps_everything_else() -> None:
    fields = take({"key": "steel", "name": "Steel", "density_kg_m3": 7800.0})
    assert fields == {"name": "Steel", "density_kg_m3": 7800.0}


def test_take_freezes_the_named_sets() -> None:
    """A list in JSON implies an order a set does not have."""
    fields = take({"key": "x", "estimated": ["poisson_ratio"]}, frozen=("estimated",))
    assert fields["estimated"] == frozenset({"poisson_ratio"})


def test_take_leaves_a_set_absent_rather_than_inventing_an_empty_one() -> None:
    """The dataclass default says what a missing field means, not this."""
    assert take({"key": "x"}, frozen=("estimated",)) == {}


def test_take_turns_each_range_into_a_pair() -> None:
    """JSON has no tuple, and the field is typed as one."""
    fields = take({"key": "x", "ranges": {"density_kg_m3": [400.0, 800.0]}})
    assert fields["ranges"] == {"density_kg_m3": (400.0, 800.0)}


def test_the_packaged_solids_table_reads_back_from_its_own_file() -> None:
    """The real file, through the real resource lookup, with no patching."""
    source, rows = read_table("phonometry.solids", "hopkins-2007-table-a2.json")
    assert "Hopkins (2007) Table A2" in source
    assert len(rows) == 25


def test_the_data_file_is_utf8_and_ends_with_a_newline() -> None:
    """A data file is text in a repository before it is a table in a package."""
    from importlib.resources import files

    entry = files("phonometry.solids.data") / "hopkins-2007-table-a2.json"
    text = entry.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text)["rows"]


def test_a_field_name_the_dataclass_does_not_have_fails_at_construction() -> None:
    """The reader does not validate field names; the dataclass does, loudly.

    This is the property the reader's docstring leans on: a column misspelt in
    a data file cannot become a row with a missing value, because the row
    cannot be built at all.
    """
    from phonometry.solids.catalogue import SolidMaterial

    fields = take(
        {
            "key": "steel",
            "name": "Steel",
            "source": "Hopkins (2007) Table A2, PDF page 635 (printed p. 607)",
            "plate_longitudinal_speed_m_s": 5270.0,
            "poisson_ratio": 0.28,
            "densty_kg_m3": 7800.0,
        }
    )
    with pytest.raises(TypeError, match="densty_kg_m3"):
        SolidMaterial(**fields)
