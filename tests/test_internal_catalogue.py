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

And it reads JSON as a browser does, because the published tables are read
from JavaScript too: a ``NaN`` or an infinity is refused, so is a name written
twice in one object (JSON keeps the last and says nothing), and so is a ``/``
in a row key, which separates the table from the row in every catalogue key.
"""

from __future__ import annotations

import json
import pathlib
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

from phonometry._internal.catalogue import (
    CatalogueError,
    CatalogueRow,
    parse_packaged,
    read_table,
    take,
)


def _packaged_text(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    """Make ``read_table`` see *text* instead of a file on disk."""

    class _Entry:
        def __truediv__(self, other: str) -> _Entry:
            return self

        def read_text(self, encoding: str = "utf-8") -> str:
            return text

    monkeypatch.setattr("importlib.resources.files", lambda _: _Entry())


def _packaged(monkeypatch: pytest.MonkeyPatch, document: dict[str, object]) -> None:
    """Make ``read_table`` see *document* instead of a file on disk.

    ``json.dumps`` writes a float NaN or infinity as the bare token CPython's
    reader accepts, which is what the refusals below need to see.
    """
    _packaged_text(monkeypatch, json.dumps(document))


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


def test_take_converts_nothing_and_leaves_the_freezing_to_the_row() -> None:
    """A list stays a list here; the row freezes it from its annotation.

    The loaders once listed which of their fields were sets, fifteen times,
    and the solids' list had fallen behind the dataclass it fed; a loader
    with no list, and a row built by hand, never froze its sets at all.
    """
    record = {
        "key": "x",
        "approximate": ["poisson_ratio"],
        "ranges": {"density_kg_m3": [400.0, 800.0]},
    }
    fields = take(record)
    assert fields == {
        "approximate": ["poisson_ratio"],
        "ranges": {"density_kg_m3": [400.0, 800.0]},
    }
    assert take({"key": "x"}) == {}


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_a_number_json_does_not_have_is_refused_naming_the_row(
    monkeypatch: pytest.MonkeyPatch, token: str
) -> None:
    """CPython reads these three; ``JSON.parse`` rejects them on sight."""
    text = (
        '{"source": "s", "about": "a", "rows": '
        f'[{{"key": "steel", "name": "Steel", "density_kg_m3": {token}}}]}}'
    )
    _packaged_text(monkeypatch, text)
    with pytest.raises(CatalogueError, match=r"^t\.json: row 'steel': density_kg_m3"):
        read_table("phonometry.solids", "t.json")


def test_a_nan_nested_in_a_hedge_names_its_row_and_its_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = _document(
        rows=[
            {"key": "brick", "name": "Brick"},
            {"key": "steel", "name": "Steel", "ranges": {"x": [1.0, float("nan")]}},
        ]
    )
    _packaged(monkeypatch, document)
    with pytest.raises(CatalogueError, match=r"row 'steel': ranges\.x\[1\] is NaN"):
        read_table("phonometry.solids", "t.json")


def test_a_name_written_twice_in_a_row_is_refused_naming_the_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """JSON keeps the second of two members with one name, and says nothing."""
    text = (
        '{"source": "s", "about": "a", "rows": '
        '[{"key": "steel", "density_kg_m3": 7800, "density_kg_m3": 7850}]}'
    )
    _packaged_text(monkeypatch, text)
    with pytest.raises(CatalogueError, match=r"row 'steel': .*'density_kg_m3' twice"):
        read_table("phonometry.solids", "t.json")


def test_a_name_written_twice_inside_a_hedge_names_the_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = (
        '{"source": "s", "about": "a", "rows": [{"key": "steel", '
        '"ranges": {"x": [1, 2], "x": [3, 4]}}]}'
    )
    _packaged_text(monkeypatch, text)
    with pytest.raises(CatalogueError, match=r"row 'steel': ranges names 'x' twice"):
        read_table("phonometry.solids", "t.json")


def test_a_top_level_name_written_twice_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = '{"source": "s", "source": "t", "about": "a", "rows": [{"key": "k"}]}'
    _packaged_text(monkeypatch, text)
    with pytest.raises(CatalogueError, match=r"the document names 'source' twice"):
        read_table("phonometry.solids", "t.json")


def test_a_slash_in_a_row_key_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """The slash is what separates the table from the row in a catalogue key."""
    _packaged(monkeypatch, _document(rows=[{"key": "steel/mild", "name": "Steel"}]))
    with pytest.raises(CatalogueError, match=r"row 'steel/mild': a row key holds no"):
        read_table("phonometry.solids", "t.json")


def test_a_key_that_is_not_text_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    _packaged(monkeypatch, _document(rows=[{"key": 7, "name": "Steel"}]))
    with pytest.raises(CatalogueError, match=r"the key 7 is not text"):
        read_table("phonometry.solids", "t.json")


def test_a_row_that_is_not_an_object_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _packaged(monkeypatch, _document(rows=["steel"]))
    with pytest.raises(CatalogueError, match=r"every row is a JSON object"):
        read_table("phonometry.solids", "t.json")


@pytest.mark.parametrize("extra", ["provenance", "schema", "rows_extra"])
def test_a_top_level_key_a_packaged_table_does_not_hold_is_refused(
    monkeypatch: pytest.MonkeyPatch, extra: str
) -> None:
    """A packaged table cites its page in ``source``; nothing else goes on top."""
    _packaged(monkeypatch, _document(**{extra: "x"}))
    with pytest.raises(CatalogueError, match=rf"no top-level '{extra}'"):
        read_table("phonometry.solids", "t.json")


@pytest.mark.parametrize("extra", ["conventions", "validity"])
def test_the_two_optional_top_level_keys_are_read(
    monkeypatch: pytest.MonkeyPatch, extra: str
) -> None:
    _packaged(monkeypatch, _document(**{extra: ["a legend"]}))
    source, rows = read_table("phonometry.solids", "t.json")
    assert source.startswith("Hopkins")
    assert [row["key"] for row in rows] == ["steel"]


@pytest.mark.parametrize(
    ("text", "fragment"),
    [
        ('{"source": "s", "about": ', "this is not JSON"),
        ('["source", "about", "rows"]', "one JSON object"),
    ],
)
def test_a_file_that_is_not_one_json_object_is_refused(
    monkeypatch: pytest.MonkeyPatch, text: str, fragment: str
) -> None:
    _packaged_text(monkeypatch, text)
    with pytest.raises(CatalogueError, match=fragment):
        read_table("phonometry.solids", "t.json")


def test_every_packaged_file_reads_through_the_strict_reader() -> None:
    """The 83 data files pass what a user file will have to pass."""
    for path in _DATA_FILES:
        document = parse_packaged(path.read_text(encoding="utf-8"), path.name)
        assert document["rows"], path.name


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


# ---------------------------------------------------------------------------
# The shared row: the hedges every catalogue needs, and reading them back
# ---------------------------------------------------------------------------
def test_a_row_holds_each_reported_list_as_a_tuple_of_values_and_pairs() -> None:
    """A page that lists several readings lists numbers and intervals mixed.

    Cox prints "96, 200-450" in one cell of his characteristic-length table:
    one study measured 96 um and another a band. Both have to survive into one
    field, so an entry is a float or a pair and the pair is a tuple like every
    other interval a row holds, whatever the data file wrote it as.
    """
    from phonometry.materials.absorbers import PorousMaterial

    row = PorousMaterial(
        name="PU foam, fully reticulated",
        source="Cox & D'Antonio 3e Table 6.8, PDF page 261 (printed p. 204)",
        reported={"viscous_length_um": [96.0, [200.0, 450.0]]},
    )
    assert row.reported == {"viscous_length_um": (96.0, (200.0, 450.0))}
    assert isinstance(row.reported["viscous_length_um"][1], tuple)


def test_a_row_says_a_listed_cell_is_listed_and_not_empty() -> None:
    """``None`` with three published readings behind it is not a blank cell.

    Read through a subclass, because the shared row carries the hedges and a
    subclass carries the quantities they hedge.
    """
    from phonometry.materials.absorbers import PorousMaterial

    row = PorousMaterial(
        name="Plastic foam",
        source="Cox & D'Antonio 3e Table 6.8, PDF page 261 (printed p. 204)",
        reported={"viscous_length_um": (25.0, 207.0, 230.0)},
    )
    assert row.why_missing("viscous_length_um") == (
        "the page lists 25, 207, 230 and no single value"
    )


def test_a_listed_cell_that_holds_an_interval_reads_it_out_as_one() -> None:
    from phonometry.materials.absorbers import PorousMaterial

    row = PorousMaterial(
        name="PU foam, fully reticulated",
        source="Cox & D'Antonio 3e Table 6.8, PDF page 261 (printed p. 204)",
        reported={"viscous_length_um": (96.0, (200.0, 450.0))},
    )
    assert row.why_missing("viscous_length_um") == (
        "the page lists 96, 200 to 450 and no single value"
    )


def test_the_hedges_of_a_shared_row_cannot_be_edited_in_place() -> None:
    """Every mapping a row holds is frozen, including the new one."""
    from phonometry.materials.absorbers import PorousMaterial

    row = PorousMaterial(
        name="x",
        source="y",
        youngs_modulus_pa=4.4e6,
        thickness_mm=40.0,
        reported={"viscous_length_um": (1.0,)},
        unquantified={"tortuosity": "model"},
        derived={"youngs_modulus_pa": "from the shear modulus"},
        ranges={"porosity": (0.9, 0.99), "flow_resistivity_pa_s_m2": (5e3, 9e3)},
        attributed_to={"row": "Someone, 1990"},
        basis={"row": "measured"},
        converted={"flow_resistivity_pa_s_m2": ("5", "kPa s/m2")},
        carried={"thickness_mm": "from the row above"},
    )
    for mapping in (
        row.reported,
        row.unquantified,
        row.derived,
        row.ranges,
        row.attributed_to,
        row.basis,
        row.converted,
        row.carried,
    ):
        with pytest.raises(TypeError):
            mapping["porosity"] = "edited"  # type: ignore[index]


def test_why_missing_refuses_a_field_the_row_does_not_have() -> None:
    """A misspelt field would otherwise answer as if the cell were empty."""
    row = CatalogueRow(name="x", source="y")
    with pytest.raises(AttributeError):
        row.why_missing("porsity")


def test_a_field_the_row_does_have_has_no_reason_to_be_missing() -> None:
    row = CatalogueRow(name="x", source="y")
    assert row.why_missing("name") == ""


def test_a_bound_may_leave_open_the_end_the_quantity_has_no_limit_on() -> None:
    """A transmission loss printed ">45" has no ceiling to record.

    Cox's aerogel stops at a porosity of 1 because that is what a porosity
    is; ASHRAE's duct wall stops nowhere, so the open end holds nothing. The
    refusal reads off the end the page did print, which is the whole of what
    it says.
    """
    from phonometry.noise_control import DuctWallSpectrum

    row = DuctWallSpectrum(
        name="200 mm",
        source="ASHRAE (2019) Chapter 49 Table 30, PDF page 914 (printed p. 49.30)",
        ranges={"transmission_loss_63_db": (45.0, None)},
        bounded_below=frozenset({"transmission_loss_63_db"}),
    )
    assert row.ranges["transmission_loss_63_db"] == (45.0, None)
    assert row.why_missing("transmission_loss_63_db") == (
        "the page prints a lower bound of 45 and no value"
    )


_TL = "transmission_loss_63_db"


@pytest.mark.parametrize(
    ("ranges", "bounded_above", "bounded_below"),
    [
        ({_TL: (45.0, None)}, frozenset(), frozenset()),
        ({_TL: (None, 5.0)}, frozenset(), frozenset()),
        ({_TL: (None, 5.0)}, frozenset(), frozenset({_TL})),
        ({_TL: (45.0, None)}, frozenset({_TL}), frozenset()),
    ],
)
def test_a_range_missing_the_end_the_page_printed_is_refused(
    ranges: dict[str, tuple[float | None, float | None]],
    bounded_above: frozenset[str],
    bounded_below: frozenset[str],
) -> None:
    """Only the open side of a bound may be empty.

    An interval missing the end the page did print reads back as a cell the
    book left blank, which is the one thing these hedges exist to tell apart,
    and it would reach a published table as half a range.
    """
    from phonometry.noise_control import DuctWallSpectrum

    with pytest.raises(CatalogueError, match="missing an end"):
        DuctWallSpectrum(
            name="x",
            source="y",
            ranges=ranges,
            bounded_above=bounded_above,
            bounded_below=bounded_below,
        )


# ---------------------------------------------------------------------------
# What every packaged data file must hold, whatever catalogue it belongs to
# ---------------------------------------------------------------------------
#: Every data file this package ships, whichever catalogue reads it. Walked
#: from disk rather than through an import, so a file a catalogue forgot to
#: list is checked too, and so this runs in a tree where only some of the
#: catalogues exist.
_DATA_FILES = sorted(
    pathlib.Path(__file__).resolve().parents[1].glob("src/phonometry/*/**/data/*.json")
)

#: The longest a printed cell can be. ``"Varies with frequency"`` is 21
#: characters, and it is the longest thing any of these pages prints instead
#: of a number; a hundred-character string is a sentence about the cell, not
#: the cell.
_LONGEST_PRINTED_CELL = 32

#: More significant figures than any of these pages prints. A page gives four
#: or five; sixteen is what ``0.82e10`` becomes when it is written that way
#: and read back, and it reaches the published table as
#: ``8 199 999 999,999999``.
_MOST_SIGNIFICANT_FIGURES = 9


def _numbers(node: object, where: str = "") -> Iterator[tuple[str, float]]:
    """Every float in a decoded data file, with the path that reaches it."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _numbers(value, f"{where}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _numbers(value, f"{where}[{index}]")
    elif isinstance(node, float):
        yield where, node


def _significant_figures(value: float) -> int:
    """How many digits *value* carries, counted the way ``repr`` writes it."""
    digits = repr(abs(value)).partition("e")[0]
    return len(digits.replace(".", "").strip("0")) or 1


def test_every_data_file_is_in_the_sweep() -> None:
    """The glob is the guard; an empty one would pass every test below."""
    assert _DATA_FILES


def _not_a_json_constant(token: str) -> float:
    """Refuse the three bare tokens that only CPython's reader accepts."""
    msg = f"{token} is a Python constant, not JSON"
    raise ValueError(msg)


@pytest.mark.parametrize("path", _DATA_FILES, ids=lambda path: path.name)
def test_a_data_file_is_json_and_not_python(path: pathlib.Path) -> None:
    """Whatever reads one of these next may not be Python.

    ``Infinity``, ``-Infinity`` and ``NaN`` are an extension of CPython's
    ``json`` module and not JSON: ``JSON.parse`` rejects them on the first
    character, and the published tables are read from JavaScript. One
    catalogue shipped seventeen bare ``Infinity`` tokens as the open end of a
    lower bound before this ran, and the file imported cleanly the whole time.
    """
    json.loads(path.read_text(encoding="utf-8"), parse_constant=_not_a_json_constant)


@pytest.mark.parametrize("path", _DATA_FILES, ids=lambda path: path.name)
def test_an_unquantified_cell_holds_what_the_page_printed(path: pathlib.Path) -> None:
    """Not why the number is missing: :meth:`why_missing` composes that.

    A sentence stored here reaches the published table, where it lands inside
    a numeric column and reads as though the book had printed it.
    """
    document = json.loads(path.read_text(encoding="utf-8"))
    for row in document["rows"]:
        for field, printed in (row.get("unquantified") or {}).items():
            assert printed, f"{path.name}: {row['key']}.{field} is empty"
            assert len(printed) <= _LONGEST_PRINTED_CELL, (
                f"{path.name}: {row['key']}.{field} holds {printed!r}, which is a "
                f"sentence about the cell rather than what the page printed in it"
            )


@pytest.mark.parametrize("path", _DATA_FILES, ids=lambda path: path.name)
def test_a_not_derivable_cell_says_why_in_words(path: pathlib.Path) -> None:
    """The opposite of the rule above: this field is the sentence."""
    document = json.loads(path.read_text(encoding="utf-8"))
    for row in document["rows"]:
        for field, reason in (row.get("not_derivable") or {}).items():
            assert len(reason) > _LONGEST_PRINTED_CELL, (
                f"{path.name}: {row['key']}.{field} says {reason!r}, which does not "
                f"explain why this library leaves the cell empty"
            )


@pytest.mark.parametrize("path", _DATA_FILES, ids=lambda path: path.name)
def test_a_misprinted_cell_says_what_the_page_printed_and_why_it_cannot_be(
    path: pathlib.Path,
) -> None:
    """The heaviest claim a row can make, so it has to carry its own argument.

    A reader who meets an empty cell here is being told the book is wrong, and
    a sentence that does not quote the printed number leaves them no way to
    check that for themselves.
    """
    document = json.loads(path.read_text(encoding="utf-8"))
    for row in document["rows"]:
        for field, reason in (row.get("misprinted") or {}).items():
            assert len(reason) > _LONGEST_PRINTED_CELL, (
                f"{path.name}: {row['key']}.{field} says {reason!r}, which does not "
                f"say why the printed value cannot be right"
            )
            assert "prints" in reason, (
                f"{path.name}: {row['key']}.{field} does not quote what the page "
                f"prints, so a reader cannot check the claim against it"
            )
            assert "ERRATA" in reason, (
                f"{path.name}: {row['key']}.{field} calls a printed value wrong "
                f"without pointing at the registry entry that argues it"
            )


@pytest.mark.parametrize("path", _DATA_FILES, ids=lambda path: path.name)
def test_a_misprinted_number_is_not_also_served(path: pathlib.Path) -> None:
    """The hedge says the number is not served, so the field has to be empty.

    Hung on a field that holds a number, it is read by nothing:
    :meth:`~phonometry._internal.catalogue.CatalogueRow.why_missing` answers
    the empty string for a field that is not missing, and the published table
    prints the number and stops before ever looking at the hedge. The reader
    is told the book is wrong nowhere at all, while the value the registry
    calls wrong goes on being handed out. A defect in a cell this library does
    not hold, such as the customary restatement of a value kept in SI, belongs
    in ``note``, which is served. A defect inside a printed description is a
    different thing and not this: there is no number in that cell to refuse.
    """
    document = json.loads(path.read_text(encoding="utf-8"))
    for row in document["rows"]:
        for field in row.get("misprinted") or {}:
            held = row.get(field)
            assert not isinstance(held, (int, float)), (
                f"{path.name}: {row['key']}.{field} is served as {held!r} and "
                f"carries a misprinted hedge, which says it is not served"
            )


@pytest.mark.parametrize("path", _DATA_FILES, ids=lambda path: path.name)
def test_no_number_carries_more_digits_than_a_page_prints(path: pathlib.Path) -> None:
    """``0.82e10`` read back is ``8199999999.999999``, and the table shows it.

    The value is right and its spelling is not: a modulus printed as 0,82 of
    ten thousand million is ``8.2e9``, which round-trips, where the other
    spelling lands one unit in the last place away and prints sixteen digits.
    """
    document = json.loads(path.read_text(encoding="utf-8"))
    for where, value in _numbers(document):
        assert _significant_figures(value) <= _MOST_SIGNIFICANT_FIGURES, (
            f"{path.name}{where} is {value!r}, which carries more digits than any "
            f"page prints: write the number the page printed"
        )
