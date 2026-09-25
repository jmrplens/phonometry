#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The JSON Schema of a catalogue document agrees with the reader.

``io.catalogue_schema`` exists so that an editor can complete a catalogue
file and mark what is wrong with it while it is typed, which is only worth
anything if the schema and the reader agree. Two directions are held here.
Every document the reader reads, every published table written out by
``io.write_catalogue`` among them, is valid under the schema: an editor that
underlined a correct file would teach its user to ignore it. And every
problem of form the schema can express is refused by both, each case read by
the reader as well so the two cannot drift apart. The reference validator is
the ``jsonschema`` package, which also checks the schema itself against the
2020-12 metaschema; the file the documentation site publishes is held to a
fresh run of its generator.
"""

from __future__ import annotations

import copy
import dataclasses
import importlib
import json
import pathlib
import pkgutil
import sys
from collections.abc import Mapping
from typing import Any

import pytest
from jsonschema import Draft202012Validator

import phonometry
from phonometry import fluids, io, materials, solids
from phonometry._internal import catalogue as private
from phonometry.io import _catalogue

_SCRIPTS = str(pathlib.Path(__file__).resolve().parents[2] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import generate_catalogue_schema as generator  # noqa: E402

ROW_CLASSES = generator.published_row_classes()
SCHEMA = io.catalogue_schema(*ROW_CLASSES)
VALIDATOR = Draft202012Validator(SCHEMA)

_PROVENANCE: dict[str, Any] = {
    "kind": "datasheet",
    "document": "Panel 40 technical data sheet",
    "publisher": "Example Acoustics Ltd",
    "version": "Rev. 4",
    "issued": "2026-03",
    "consulted": "2026-09-23",
    "page": "2",
}

_PANEL_40: dict[str, Any] = {
    "schema": "phonometry-catalogue",
    "schema_version": 1,
    "catalogue": "panel-40",
    "row_type": "PorousMaterial",
    "about": "Core of the Panel 40 absorber as its data sheet gives it.",
    "provenance": _PROVENANCE,
    "basis": "declared",
    "rows": [
        {
            "key": "core-declared",
            "name": "Panel 40 core",
            "variant": "as declared",
            "thickness_mm": 40,
            "frame_density_kg_m3": 40,
            "ranges": {"flow_resistivity_kpa_s_m2": [5, None]},
            "bounded_below": ["flow_resistivity_kpa_s_m2"],
            "note": "the sheet prints the designation code AFr5",
            "x-product-code": "P40-C",
        },
        {
            "key": "core-lab",
            "name": "Panel 40 core",
            "variant": "40 mm specimen",
            "provenance": {
                "page": "3",
                "printed_table": "Table 2",
                "laboratory": "Example Lab",
                "report": "26-014",
                "test_standard": "ISO 9053-1:2018",
                "field_test_standards": {"porosity": "ISO 4638"},
            },
            "basis": {"row": "measured", "poisson_ratio": "estimated"},
            "flow_resistivity_pa_s_m2": 12500,
            "uncertainty": {"flow_resistivity_pa_s_m2": 900},
            "porosity": 0.97,
            "tortuosity": 1.02,
            "approximate": ["tortuosity"],
            "viscous_length_um": 95,
            "thermal_length_um": 190,
            "thickness_mm": 40,
            "youngs_modulus_pa": 140000,
            "poisson_ratio": 0.0,
            "unquantified": {"structural_loss_factor": "n.m."},
            "x-product-code": "P40-C",
            "x-batch": 17,
        },
    ],
}


def _panel() -> dict[str, Any]:
    """A fresh copy of the design's example document."""
    return copy.deepcopy(_PANEL_40)


def _problems(document: object) -> list[str]:
    """What the schema finds wrong with *document*, one line each."""
    return [
        f"{'/'.join(map(str, error.absolute_path))}: {error.message[:160]}"
        for error in VALIDATOR.iter_errors(document)
    ]


# ---------------------------------------------------------------------------
# The schema itself
# ---------------------------------------------------------------------------
def test_the_schema_is_a_valid_2020_12_schema() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    assert SCHEMA["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert SCHEMA["$id"] == "urn:phonometry:schema:catalogue:1"


def test_the_published_file_is_a_fresh_run_of_its_generator() -> None:
    """The file the site serves is the schema of every published row class."""
    assert generator.OUTPUT.read_text(encoding="utf-8") == generator.render()
    assert json.loads(generator.OUTPUT.read_text(encoding="utf-8")) == SCHEMA


def test_the_generator_check_passes_on_a_fresh_file_and_fails_on_a_stale_one(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stale = tmp_path / "schema.json"
    stale.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(generator, "OUTPUT", stale)
    monkeypatch.setattr(generator, "ROOT", tmp_path)
    assert generator.main(["--check"]) == 1
    assert generator.main([]) == 0
    assert generator.main(["--check"]) == 0
    assert stale.read_text(encoding="utf-8") == generator.render()


def test_the_walk_finds_every_published_row_class() -> None:
    names = [cls.__name__ for cls in ROW_CLASSES]
    assert names == sorted(names)
    assert {"CatalogueRow", "BandedRow", "PorousMaterial", "SolidMaterial"} <= set(
        names
    )
    assert len(names) >= 28
    assert SCHEMA["properties"]["row_type"]["enum"] == names


@pytest.mark.parametrize("cls", ROW_CLASSES, ids=lambda cls: cls.__name__)
def test_every_field_and_every_other_unit_of_a_class_is_a_property(
    cls: type[io.CatalogueRow],
) -> None:
    """What the reader takes in a row is what an editor offers to complete."""
    row = SCHEMA["$defs"][cls.__name__]
    kinds = private.field_kinds(cls)
    written = {"derived", "table", "source"}
    expected = {"key"} | (set(kinds) - written) | set(private.spellings(cls).aliases)
    assert set(row["properties"]) == expected
    assert row["additionalProperties"] is False
    assert row["required"] == ["key", "name"]
    fields = SCHEMA["$defs"][f"{cls.__name__}.fields"]["enum"]
    numeric = {name for name, kind in kinds.items() if kind in ("number", "whole")}
    assert set(fields) == numeric | set(private.spellings(cls).aliases)


def test_a_field_whose_unit_cannot_be_negative_is_held_to_it() -> None:
    row = SCHEMA["$defs"]["PorousMaterial"]["properties"]
    assert row["frame_density_kg_m3"] == {"$ref": "#/$defs/number_from_0"}
    assert row["porosity"] == {"$ref": "#/$defs/number_from_0_to_1"}
    assert row["tortuosity"] == {"$ref": "#/$defs/number"}
    assert row["thickness_cm"]["$ref"] == "#/$defs/number_from_0"
    limited = SCHEMA["$defs"]["number_from_0_to_1"]["anyOf"][1]
    assert limited == {"type": "number", "minimum": 0.0, "maximum": 1.0}


def test_each_call_returns_a_schema_of_its_own() -> None:
    first = io.catalogue_schema(materials.PorousMaterial)
    first["$defs"]["PorousMaterial"]["properties"].clear()
    first["properties"]["row_type"]["enum"].append("Nothing")
    again = io.catalogue_schema(materials.PorousMaterial)
    assert again["$defs"]["PorousMaterial"]["properties"]
    assert again["properties"]["row_type"]["enum"] == ["PorousMaterial"]


def test_a_class_given_twice_is_described_once() -> None:
    twice = io.catalogue_schema(materials.PorousMaterial, materials.PorousMaterial)
    assert twice == io.catalogue_schema(materials.PorousMaterial)
    reordered = io.catalogue_schema(solids.SolidMaterial, materials.PorousMaterial)
    assert reordered == io.catalogue_schema(
        materials.PorousMaterial, solids.SolidMaterial
    )


# ---------------------------------------------------------------------------
# What the caller may ask for
# ---------------------------------------------------------------------------
def test_a_schema_needs_a_row_class() -> None:
    with pytest.raises(TypeError, match=r"catalogue_schema\(\) needs at least one"):
        io.catalogue_schema()


@pytest.mark.parametrize(
    ("given", "said"),
    [
        (dict, "row_type is <class 'dict'>"),
        ("PorousMaterial", "row_type is 'PorousMaterial'"),
        (fluids.Fluid, "row_type=Fluid"),
    ],
    ids=["not-a-row-class", "a-name", "fluid"],
)
def test_anything_but_a_row_class_is_refused(given: object, said: str) -> None:
    with pytest.raises(TypeError, match=said):
        io.catalogue_schema(given)  # type: ignore[arg-type]


def _namesake() -> type[io.CatalogueRow]:
    """A caller's class that shares the name of a published one."""

    @dataclasses.dataclass(frozen=True, kw_only=True)
    class PorousMaterial(io.CatalogueRow):
        """A class of my own that happens to share a published name."""

        mass_g: float | None = None

    return PorousMaterial


def test_two_classes_that_share_a_name_are_refused() -> None:
    namesake = _namesake()
    with pytest.raises(TypeError, match="are both named 'PorousMaterial'"):
        io.catalogue_schema(materials.PorousMaterial, namesake)


@dataclasses.dataclass(frozen=True, kw_only=True)
class Plasterboard(io.CatalogueRow):
    """A board a catalogue of the library does not hold."""

    surface_density_kg_m2: float | None = None
    thickness_mm: float | None = None
    fire_class: str = ""
    layers: int | None = None


def test_a_class_of_your_own_is_described_with_its_fields() -> None:
    schema = io.catalogue_schema(Plasterboard)
    Draft202012Validator.check_schema(schema)
    row = schema["$defs"]["Plasterboard"]["properties"]
    assert row["surface_density_kg_m2"] == {"$ref": "#/$defs/number_from_0"}
    assert row["surface_density_g_m2"]["$ref"] == "#/$defs/number_from_0"
    assert row["layers"] == {"$ref": "#/$defs/whole"}
    assert row["fire_class"] == {"$ref": "#/$defs/text"}
    document = {
        **_panel(),
        "catalogue": "boards",
        "row_type": "Plasterboard",
        "rows": [
            {
                "key": "b12",
                "name": "Board 12.5",
                "surface_density_g_m2": 8600,
                "thickness_mm": 12.5,
                "fire_class": "A2-s1,d0",
                "layers": 1,
            }
        ],
    }
    del document["basis"]
    assert not list(Draft202012Validator(schema).iter_errors(document))
    read = io.parse_catalogue(document, row_type=Plasterboard)["boards/b12"]
    assert read.surface_density_kg_m2 == pytest.approx(8.6)
    fractional = copy.deepcopy(document)
    fractional["rows"][0]["layers"] = 1.5
    assert not Draft202012Validator(schema).is_valid(fractional)
    with pytest.raises(io.CatalogueError, match="whole number"):
        io.parse_catalogue(fractional, row_type=Plasterboard)


# ---------------------------------------------------------------------------
# What the reader reads, the schema accepts
# ---------------------------------------------------------------------------
def test_the_designs_example_is_valid() -> None:
    assert _problems(_panel()) == []
    io.parse_catalogue(_panel(), row_type=materials.PorousMaterial)


def test_a_schema_key_is_taken_by_both_and_read_by_neither() -> None:
    document = {"$schema": "./panel-40.schema.json", **_panel()}
    assert _problems(document) == []
    read = io.parse_catalogue(document, row_type=materials.PorousMaterial)
    assert read == io.parse_catalogue(_panel(), row_type=materials.PorousMaterial)


def _published_tables() -> list[tuple[str, str, dict[str, io.CatalogueRow]]]:
    """Every table of every published mapping of rows, as the writer test has it."""
    found: list[tuple[str, str, dict[str, io.CatalogueRow]]] = []
    for module in pkgutil.iter_modules(phonometry.__path__):
        if module.name.startswith("_") or not module.ispkg:
            continue
        package = importlib.import_module(f"phonometry.{module.name}")
        for name in getattr(package, "__all__", ()):
            value = getattr(package, name)
            if not (name.startswith("PUBLISHED_") and isinstance(value, Mapping)):
                continue
            tables: dict[str, dict[str, io.CatalogueRow]] = {}
            for key, row in value.items():
                if isinstance(row, io.CatalogueRow):
                    tables.setdefault(row.table, {})[key] = row
            found += [(name, table, rows) for table, rows in sorted(tables.items())]
    return found


TABLES = _published_tables()


def test_every_published_table_is_found() -> None:
    assert len(TABLES) >= 82


@pytest.mark.parametrize(
    ("mapping", "table", "rows"),
    TABLES,
    ids=[f"{mapping}-{table}" for mapping, table, _ in TABLES],
)
def test_every_published_table_written_out_is_valid(
    tmp_path: pathlib.Path,
    mapping: str,
    table: str,
    rows: dict[str, io.CatalogueRow],
) -> None:
    """Every row class and every hedge the packaged data uses, through the schema."""
    path = tmp_path / f"{table}.json"
    io.write_catalogue(
        rows, path, catalogue="copy-of-" + mapping.lower().replace("_", "-")
    )
    assert _problems(json.loads(path.read_text(encoding="utf-8"))) == []


def test_a_csv_files_header_is_valid(tmp_path: pathlib.Path) -> None:
    """The header beside a CSV file is a document with a dialect and no rows."""
    arau = {
        key: row
        for key, row in materials.PUBLISHED_ABSORPTION.items()
        if row.table == "arau-1999-table-6-1"
    }
    written = io.write_catalogue(
        arau,
        tmp_path / "template.csv",
        catalogue="template",
        delimiter=";",
        decimal=",",
    )
    header = json.loads(written[1].read_text(encoding="utf-8"))
    assert header["csv"] == {"delimiter": ";", "decimal": ","}
    assert "rows" not in header
    assert _problems(header) == []


@pytest.mark.parametrize("cls", ROW_CLASSES, ids=lambda cls: cls.__name__)
def test_every_other_unit_of_every_class_is_valid_as_a_value_and_as_a_key(
    cls: type[io.CatalogueRow],
) -> None:
    """Each alias the reader converts, written as a value and under a hedge."""
    aliases = private.spellings(cls).aliases
    rows: list[dict[str, Any]] = []
    for index, written in enumerate(sorted(aliases)):
        rows.append({"key": f"v{index}", "name": "Specimen", written: 1})
        rows.append(
            {
                "key": f"r{index}",
                "name": "Specimen",
                "ranges": {written: [1, 2]},
                "approximate": [written],
            }
        )
    rows = rows or [{"key": "a", "name": "Specimen"}]
    document = {
        **_panel(),
        "row_type": cls.__name__,
        "rows": rows,
    }
    del document["basis"]
    if cls is materials.AbsorptionAreaSpectrum:
        for row in rows:
            row["per"] = "per 1000 ft3"
    assert _problems(document) == []
    io.parse_catalogue(document, row_type=cls)


# ---------------------------------------------------------------------------
# What the schema refuses, the reader refuses
# ---------------------------------------------------------------------------
def _without(key: str) -> dict[str, Any]:
    document = _panel()
    del document[key]
    return document


def _with(path: tuple[Any, ...], value: object) -> dict[str, Any]:
    """The example with *value* put at *path*."""
    document = _panel()
    node: Any = document
    for step in path[:-1]:
        node = node[step]
    node[path[-1]] = value
    return document


REFUSED = {
    "an-unknown-top-level-key": _with(("tables",), []),
    "no-about": _without("about"),
    "a-blank-about": _with(("about",), "   "),
    "another-schema": _with(("schema",), "phonometry-sidecar"),
    "a-newer-version": _with(("schema_version",), 2),
    "a-version-in-text": _with(("schema_version",), "1"),
    "a-reserved-name": _with(("catalogue",), "acme-2026-rev4"),
    "a-name-in-capitals": _with(("catalogue",), "Panel 40"),
    "a-basis-outside-the-vocabulary": _with(("basis",), "guessed"),
    "a-convention-that-is-not-text": _with(("conventions",), [3]),
    "a-dialect-in-a-json-document": _with(("csv",), {"delimiter": ";", "decimal": ","}),
    "no-rows": _without("rows"),
    "an-empty-list-of-rows": _with(("rows",), []),
    "a-schema-key-that-is-not-text": _with(("$schema",), 1),
    "a-provenance-without-its-day": _with(
        ("provenance",), {k: v for k, v in _PROVENANCE.items() if k != "consulted"}
    ),
    "a-day-written-the-other-way": _with(("provenance", "consulted"), "23/09/2026"),
    "an-unknown-kind": _with(("provenance", "kind"), "brochure"),
    "an-empty-version": _with(("provenance", "version"), ""),
    "an-issue-date-in-words": _with(("provenance", "issued"), "March 2026"),
    "a-digest-that-is-not-one": _with(("provenance", "sha256"), "abc"),
    "an-unknown-provenance-member": _with(("provenance", "edition"), "3"),
    "a-standard-for-no-field": _with(
        ("provenance", "field_test_standards"), {"porosty": "ISO 4638"}
    ),
    "a-key-with-a-slash": _with(("rows", 0, "key"), "core/declared"),
    "a-key-with-a-space": _with(("rows", 0, "key"), "core declared"),
    "a-row-without-a-key": _with(("rows", 0), {"name": "Panel 40 core"}),
    "a-row-without-a-name": _with(("rows", 0), {"key": "a"}),
    "a-blank-name": _with(("rows", 0, "name"), " "),
    "a-control-character": _with(("rows", 0, "name"), "Panel\x0740"),
    "a-mark-that-reorders-text": _with(("rows", 0, "note"), "core ‮04"),
    "derived-written-by-hand": _with(("rows", 1, "derived"), {"porosity": "x"}),
    "a-table-written-by-hand": _with(("rows", 1, "table"), "panel-40"),
    "a-source-written-by-hand": _with(("rows", 1, "source"), "Panel 40 sheet"),
    "an-estimate-outside-basis": _with(("rows", 1, "estimated"), ["porosity"]),
    "an-unknown-field": _with(("rows", 1, "porosty"), 0.97),
    "an-unknown-unit": _with(("rows", 1, "thickness_inch"), 1.6),
    "text-where-a-number-goes": _with(("rows", 1, "porosity"), "0,97"),
    "a-flag-where-a-number-goes": _with(("rows", 1, "porosity"), value=True),
    "a-negative-density": _with(("rows", 1, "frame_density_kg_m3"), -40),
    "a-porosity-above-one": _with(("rows", 1, "porosity"), 1.5),
    "a-negative-thickness-in-another-unit": _with(("rows", 1, "thickness_cm"), -4),
    "a-hedge-on-no-field": _with(("rows", 1, "approximate"), ["tortuosty"]),
    "a-basis-word-for-a-field": _with(("rows", 1, "basis"), {"porosity": "typical"}),
    "a-basis-for-the-table": _with(("rows", 1, "basis"), {"table": "measured"}),
    "a-range-with-three-ends": _with(
        ("rows", 1, "ranges"), {"tortuosity": [1.0, 1.1, 1.2]}
    ),
    "a-range-end-in-text": _with(("rows", 1, "ranges"), {"tortuosity": ["1", 2]}),
    "no-readings": _with(("rows", 1, "reported"), {"tortuosity": []}),
    "a-negative-uncertainty": _with(
        ("rows", 1, "uncertainty"), {"flow_resistivity_pa_s_m2": -900}
    ),
    "a-converted-figure-without-its-unit": _with(
        ("rows", 1, "converted"), {"flow_resistivity_pa_s_m2": ["12.5"]}
    ),
    "a-blank-word": _with(("rows", 1, "unquantified"), {"structural_loss_factor": ""}),
    "a-column-of-your-own-holding-an-object": _with(("rows", 1, "x-product"), {}),
    "a-column-of-your-own-holding-a-flag": _with(("rows", 1, "x-product"), value=True),
    "a-column-name-that-is-not-one": _with(("rows", 1, "x-"), "P40"),
    "a-row-narrowing-its-document": _with(
        ("rows", 1, "provenance"), {"document": "Another sheet"}
    ),
    "a-row-narrowing-an-unknown-member": _with(
        ("rows", 1, "provenance"), {"pages": "3"}
    ),
}


@pytest.mark.parametrize("document", REFUSED.values(), ids=list(REFUSED))
def test_a_problem_of_form_is_refused_by_the_schema_and_by_the_reader(
    document: dict[str, Any],
) -> None:
    assert _problems(document)
    with pytest.raises(io.CatalogueError, match="<document>"):
        io.parse_catalogue(document, row_type=materials.PorousMaterial)


def test_a_header_without_its_dialect_is_refused_by_both(
    tmp_path: pathlib.Path,
) -> None:
    header = _without("rows")
    assert _problems(header)
    path = tmp_path / "panel.csv"
    path.write_text("key;name\na;Panel 40 core\n", encoding="utf-8")
    (tmp_path / "panel.csv.phonometry.json").write_text(
        json.dumps(header), encoding="utf-8"
    )
    with pytest.raises(io.CatalogueError, match="declares no dialect"):
        io.read_catalogue(path, row_type=materials.PorousMaterial)


@pytest.mark.parametrize(
    "dialect",
    [
        {"delimiter": ",", "decimal": ","},
        {"delimiter": "|", "decimal": "."},
        {"delimiter": ";"},
        {"delimiter": ";", "decimal": ",", "quote": '"'},
    ],
    ids=["comma-between-commas", "a-pipe", "no-decimal-mark", "an-unknown-member"],
)
def test_a_dialect_the_reader_refuses_is_refused_by_the_schema(
    dialect: dict[str, str], tmp_path: pathlib.Path
) -> None:
    header = {**_without("rows"), "csv": dialect}
    assert _problems(header)
    path = tmp_path / "panel.csv"
    path.write_text("key;name\na;Panel 40 core\n", encoding="utf-8")
    (tmp_path / "panel.csv.phonometry.json").write_text(
        json.dumps(header), encoding="utf-8"
    )
    with pytest.raises(io.CatalogueError, match="panel.csv"):
        io.read_catalogue(path, row_type=materials.PorousMaterial)


def test_a_header_holding_rows_is_refused_by_both(tmp_path: pathlib.Path) -> None:
    header = {**_panel(), "csv": {"delimiter": ";", "decimal": ","}}
    assert _problems(header)
    path = tmp_path / "panel.csv"
    path.write_text("key;name\na;Panel 40 core\n", encoding="utf-8")
    (tmp_path / "panel.csv.phonometry.json").write_text(
        json.dumps(header), encoding="utf-8"
    )
    with pytest.raises(io.CatalogueError, match="its header holds none"):
        io.read_catalogue(path, row_type=materials.PorousMaterial)


def test_the_limits_the_schema_states_are_the_readers() -> None:
    """The names, keys, lengths and counts are taken from the reader's own."""
    assert (
        SCHEMA["properties"]["catalogue"]["pattern"] == f"^{_catalogue._NAME.pattern}$"
    )
    assert (
        SCHEMA["properties"]["catalogue"]["not"]["pattern"]
        == f"^{_catalogue._RESERVED.pattern}"
    )
    key = SCHEMA["$defs"]["PorousMaterial"]["properties"]["key"]["pattern"]
    assert key == f"^{_catalogue._KEY.pattern}$"
    assert SCHEMA["properties"]["rows"]["maxItems"] == _catalogue._MAX_ROWS
    assert SCHEMA["$defs"]["text"]["maxLength"] == _catalogue._MAX_TEXT
    assert SCHEMA["$defs"]["prose"]["maxLength"] == _catalogue._MAX_PROSE
    assert set(SCHEMA["properties"]) == _catalogue._TOP_KEYS | {"csv"}
    row_provenance = SCHEMA["$defs"]["row_provenance"]["properties"]
    assert tuple(row_provenance) == _catalogue._ROW_PROVENANCE
    assert set(SCHEMA["$defs"]["provenance"]["properties"]) == {
        item.name for item in dataclasses.fields(io.Provenance)
    }


@dataclasses.dataclass(frozen=True, kw_only=True)
class _Undocumented(io.CatalogueRow):
    mass_kg: float | None = None


def test_a_class_is_described_by_its_docstring_or_its_name() -> None:
    schema = io.catalogue_schema(Plasterboard, _Undocumented)
    documented = schema["$defs"]["Plasterboard"]["description"]
    assert documented == "A board a catalogue of the library does not hold."
    assert schema["$defs"]["_Undocumented"]["description"] == "_Undocumented"
