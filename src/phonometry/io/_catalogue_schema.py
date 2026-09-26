#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The JSON Schema of a catalogue document, for an editor to complete it.

A catalogue file is typed by hand, and an editor that knows its shape
completes a field's name, offers the words ``basis`` takes and marks a text
where a number goes while the file is written, long before the reader sees
it. JSON Schema is how an editor learns a shape, so :func:`catalogue_schema`
writes one, in the 2020-12 dialect, from the row classes themselves: every
field a class has, under every name the reader takes it, with every hedge
naming the fields it may name.

The reader does not use it. :func:`~phonometry.io.read_catalogue` holds a
file to the whole contract of a row, and a schema can hold it to the form
alone: which keys a document, a provenance and a row may have, what kind of
value each takes, the patterns of a name and a key, the words of the closed
vocabularies, the limits the unit of a field sets on its value. What depends
on two cells at once (a value beside a hedge that says there is none, a bound
on a field with no range, the end of a range a bound needs) and the notes a
reader keeps are the reader's alone, so a document the schema accepts can
still be refused, and the refusal says why. A document the reader accepts is
never refused by the schema.
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from .._internal.catalogue import (
    _NUMERIC,
    CATALOGUE_BASES,
    PROVENANCE_KINDS,
    CatalogueRow,
    _limit,
)
from ._catalogue import (
    _EXTRA,
    _HEDGE_WORDS,
    _KEY,
    _MAX_PROSE,
    _MAX_ROWS,
    _MAX_TEXT,
    _NAME,
    _PROSE,
    _RESERVED,
    _ROW_PROVENANCE,
    _TEXT_HEDGES,
    _UNSAFE,
    CATALOGUE_SCHEMA,
    CATALOGUE_SCHEMA_VERSION,
    _check_row_type,
    _Names,
)
from ._catalogue_csv import _DECIMALS, _DELIMITERS

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

#: The dialect of JSON Schema the document is written in.
_DIALECT = "https://json-schema.org/draft/2020-12/schema"
#: What names the schema, which a document's ``$schema`` may point at. A URN
#: rather than a web address, so that it does not change when the site that
#: publishes the file moves.
SCHEMA_ID = f"urn:phonometry:schema:catalogue:{CATALOGUE_SCHEMA_VERSION}"

#: A text no reader should see: the control characters the reader refuses,
#: taken from its own pattern so the two cannot drift apart.
_SAFE = f"^[^{_UNSAFE.pattern[1:-1]}]*$"
#: A text that holds something but white space.
_FILLED = r"\S"
#: A day as ``YYYY-MM-DD``, and a date at the precision a document prints.
_DAY = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
_PRINTED_DATE = r"^([0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?)?$"
#: A SHA-256 digest in hexadecimal, or nothing.
_DIGEST = r"^([0-9a-fA-F]{64})?$"
#: The fields a row never writes: the library's to write, and the citation
#: the reader composes from the provenance.
_NEVER_WRITTEN = frozenset({"derived", "table", "source"})


def _ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/$defs/{name}"}


def _anchored(pattern: str) -> str:
    return f"^{pattern}$"


def _pair(item: dict[str, Any]) -> dict[str, Any]:
    """Two values in a list, as an interval or a converted figure writes them."""
    return {"type": "array", "prefixItems": [item, item], "minItems": 2, "maxItems": 2}


def _common() -> dict[str, Any]:
    """The definitions every row class shares."""
    return {
        "text": {
            "type": "string",
            "maxLength": _MAX_TEXT,
            "pattern": _SAFE,
            "description": (
                "Text, with no control character but the tab and the line feed "
                "and no mark that reorders it."
            ),
        },
        "prose": {
            "type": "string",
            "maxLength": _MAX_PROSE,
            "pattern": _SAFE,
            "description": "A paragraph or more of text.",
        },
        "filled": {"allOf": [_ref("text"), {"pattern": _FILLED}]},
        "number": {"type": ["number", "null"]},
        "whole": {"type": ["integer", "null"]},
        "reading": {
            "anyOf": [{"type": "number"}, _pair({"type": "number"})],
            "description": "One reading: a number, or an interval [low, high].",
        },
        "provenance": _document_provenance(),
        "row_provenance": _row_provenance(),
        "csv": _dialect(),
    }


def _provenance_properties() -> dict[str, Any]:
    """Every member a provenance may have, as the document writes it."""
    text = _ref("text")
    return {
        "kind": {
            "enum": list(PROVENANCE_KINDS),
            "description": "What kind of document the cells were read from.",
        },
        "document": {
            "allOf": [text, {"pattern": _FILLED}],
            "description": "The document's title as it prints it.",
        },
        "version": {
            "anyOf": [{"allOf": [text, {"pattern": _FILLED}]}, {"type": "null"}],
            "description": (
                'The revision the document prints ("Rev. 4"), or null when it '
                "prints none."
            ),
        },
        "consulted": {
            "type": "string",
            "pattern": _DAY,
            "format": "date",
            "description": "The day the document was read, as YYYY-MM-DD.",
        },
        "publisher": {**text, "description": "Who issues the document."},
        "issued": {
            "type": "string",
            "pattern": _PRINTED_DATE,
            "description": (
                "When the document says it was issued: YYYY, YYYY-MM or "
                "YYYY-MM-DD, at the precision it prints."
            ),
        },
        "url": {
            **text,
            "description": "Where the document was found. Never opened by the reader.",
        },
        "sha256": {
            "type": "string",
            "pattern": _DIGEST,
            "description": "The SHA-256 digest of the file that was read, in hexadecimal.",
        },
        "page": {**text, "description": "The page the cells are on."},
        "printed_table": {
            **text,
            "description": "The label of the table on the page, as it prints it.",
        },
        "laboratory": {**text, "description": "The laboratory that made the test."},
        "accreditation": {
            **text,
            "description": "The laboratory's accreditation, as printed.",
        },
        "report": {**text, "description": "The number of the test report."},
        "test_date": {**text, "description": "When the test was made, as printed."},
        "test_standard": {
            **text,
            "description": "The standard the test followed, as printed.",
        },
        "field_test_standards": {
            "type": "object",
            "additionalProperties": _ref("filled"),
            "description": (
                "Field to the standard the document cites for that field, where "
                "it cites one per property."
            ),
        },
    }


def _document_provenance() -> dict[str, Any]:
    return {
        "type": "object",
        "description": "Which document the cells were read from, and how.",
        "required": ["kind", "document", "version", "consulted"],
        "properties": _provenance_properties(),
        "additionalProperties": False,
    }


def _row_provenance() -> dict[str, Any]:
    members = _provenance_properties()
    return {
        "type": "object",
        "description": (
            "Where on the document this row's cells are and who tested them: "
            "never which document it is, which is another file."
        ),
        "properties": {name: members[name] for name in _ROW_PROVENANCE},
        "additionalProperties": False,
    }


def _dialect() -> dict[str, Any]:
    return {
        "type": "object",
        "description": (
            "How the CSV file beside this header writes its cells. Only the "
            "header of a CSV file declares it."
        ),
        "required": ["delimiter", "decimal"],
        "properties": {
            "delimiter": {"enum": list(_DELIMITERS)},
            "decimal": {"enum": list(_DECIMALS)},
        },
        "additionalProperties": False,
        "not": {
            "required": ["delimiter", "decimal"],
            "properties": {"delimiter": {"const": ","}, "decimal": {"const": ","}},
        },
    }


class _RowSchema:
    """The definitions one row class adds: its row, and the names it takes."""

    def __init__(self, row_type: type[CatalogueRow]) -> None:
        self.row_type = row_type
        self.name = row_type.__name__
        self.names = _Names(row_type)
        spellings = self.names.spellings
        self.aliases = {
            written: target
            for written, (target, _) in sorted(spellings.aliases.items())
        }
        numeric = sorted(self.names.numeric)
        self.fields = [*numeric, *self.aliases]
        cells = sorted(self.names.cells)
        self.cells = [*cells, *(a for a, t in self.aliases.items() if t in cells)]
        #: The limited values the class's fields use, filled as its row is.
        self.limits: dict[str, Any] = {}

    def definitions(self) -> dict[str, Any]:
        """The row, and the two lists of names its hedges may use."""
        row = self.row()
        return {
            **self.hedges(),
            **self.limits,
            self.name: row,
            f"{self.name}.fields": {
                "enum": self.fields,
                "description": f"A numeric field of {self.name}, or another unit of one.",
            },
            f"{self.name}.cells": {
                "enum": self.cells,
                "description": f"A field of {self.name} that holds a cell of the page.",
            },
        }

    def row(self) -> dict[str, Any]:
        cls = self.row_type
        properties: dict[str, Any] = {
            "key": {
                "type": "string",
                "pattern": _anchored(_KEY.pattern),
                "description": (
                    "The row's key in the catalogue, the half of "
                    '"<catalogue>/<key>" after the slash.'
                ),
            }
        }
        for item in dataclasses.fields(cls):
            if item.name in _NEVER_WRITTEN:
                continue
            properties[item.name] = self.field(item.name)
        for written, target in self.aliases.items():
            alias = self.names.spellings.aliases[written][1]
            properties[written] = {
                **self.value(target),
                "description": (
                    f"{target} written in {alias.unit}; the reader converts the "
                    "figure on its digits and keeps it in converted."
                ),
            }
        return {
            "type": "object",
            "title": self.name,
            "description": self.summary(),
            "required": ["key", *self.names_required()],
            "properties": properties,
            "patternProperties": {
                _anchored(_EXTRA.pattern): {
                    "anyOf": [_ref("text"), {"type": "number"}],
                    "description": (
                        "A column of your own, kept as text beside the row and "
                        "never read by any calculation."
                    ),
                }
            },
            "additionalProperties": False,
        }

    def summary(self) -> str:
        """The first line of the class's docstring, or its name without one.

        A dataclass with no docstring of its own is given its signature as
        one, which describes nothing an editor should show.
        """
        lines = (self.row_type.__doc__ or "").strip().splitlines()
        if not lines or lines[0].startswith(f"{self.name}("):
            return self.name
        return lines[0]

    def names_required(self) -> list[str]:
        return [
            item.name
            for item in dataclasses.fields(self.row_type)
            if item.default is dataclasses.MISSING
            and item.default_factory is dataclasses.MISSING
            and item.name not in _NEVER_WRITTEN
        ]

    def value(self, name: str) -> dict[str, Any]:
        """The value a numeric field takes, within its physical limits."""
        whole = self.names.kinds[name] == "whole"
        bounds = _limit(name)
        if bounds is None:
            return _ref("whole" if whole else "number")
        limited = _limited_name(bounds, whole=whole)
        self.limits[limited] = _limited(bounds, whole=whole)
        return _ref(limited)

    def field(self, name: str) -> dict[str, Any]:
        """The schema of one field of the class, as a document writes it."""
        kind = self.names.kinds[name]
        if name == "provenance":
            # A row narrows the standard of a field of its own class, as the
            # document does, so the names are held to the class here too.
            return {
                "allOf": [
                    _ref("row_provenance"),
                    {
                        "properties": {
                            "field_test_standards": {
                                "propertyNames": _ref(f"{self.name}.fields")
                            }
                        }
                    },
                ]
            }
        if name in self.names.hedges:
            return self.hedge(name)
        if kind in _NUMERIC:
            return self.value(name)
        if kind == "flag":
            return {"type": "boolean"}
        if kind == "text":
            if name == "name":
                return _ref("filled")
            return _ref("prose" if name in _PROSE else "text")
        if kind == "set":
            return {"type": "array", "items": _ref("text")}
        return {"type": "object"}

    def hedges(self) -> dict[str, Any]:
        """The shape of each hedge of the class, whatever fields it names."""
        return {
            f"hedge.{hedge}": _hedge_shape(hedge, self.names.kinds[hedge])
            for hedge in sorted(self.names.hedges - _NEVER_WRITTEN)
        }

    def hedge(self, hedge: str) -> dict[str, Any]:
        """One hedge of the class: its shape, and the fields it may name."""
        numeric_only = hedge in self.row_type._number_hedges
        names = _ref(f"{self.name}.fields" if numeric_only else f"{self.name}.cells")
        if self.names.kinds[hedge] == "set":
            return {**_ref(f"hedge.{hedge}"), "items": names}
        words = _HEDGE_WORDS.get(hedge)
        keys = {"anyOf": [names, {"enum": sorted(words)}]} if words else names
        return {**_ref(f"hedge.{hedge}"), "propertyNames": keys}


def _limited_name(bounds: tuple[float, float | None, str], *, whole: bool) -> str:
    """The name of the definition of a value within *bounds*."""
    low, high, _ = bounds
    kind = "whole" if whole else "number"
    upper = "" if high is None else f"_to_{high:g}"
    return f"{kind}_from_{low:g}{upper}"


def _limited(bounds: tuple[float, float | None, str], *, whole: bool) -> dict[str, Any]:
    """A value within the physical limits the name of its field sets."""
    low, high, _ = bounds
    limited: dict[str, Any] = {"type": "integer" if whole else "number", "minimum": low}
    if high is not None:
        limited["maximum"] = high
    said = (
        "A number that is never negative, as no quantity in the unit its "
        "field's name ends in is, or null."
        if high is None
        else f"A number from {low:g} to {high:g}, the values the quantity its "
        "field names can take, or null."
    )
    return {"anyOf": [{"type": "null"}, limited], "description": said}


def _hedge_shape(hedge: str, kind: str) -> dict[str, Any]:
    """What one hedge holds, and what it says, for every class that has it."""
    described = {"description": _HEDGES[hedge]} if hedge in _HEDGES else {}
    if kind == "set":
        return {"type": "array", **described}
    return {"type": "object", "additionalProperties": _entry(hedge), **described}


def _entry(hedge: str) -> dict[str, Any]:
    """The shape of one entry of *hedge*."""
    if hedge == "ranges":
        return _pair({"type": ["number", "null"]})
    if hedge == "reported":
        return {"type": "array", "minItems": 1, "items": _ref("reading")}
    if hedge == "uncertainty":
        return {"type": "number", "minimum": 0}
    if hedge == "converted":
        return _pair(_ref("filled"))
    if hedge == "basis":
        return {"enum": list(CATALOGUE_BASES)}
    if hedge in _TEXT_HEDGES:
        return _ref("filled")
    return {}


#: What each hedge says, for the editor to show beside it.
_HEDGES: Mapping[str, str] = MappingProxyType(
    {
        "basis": (
            "What the source says a value is: field (or row) to measured, "
            "declared, calculated, estimated or extended."
        ),
        "approximate": "The fields the page prints with a ~.",
        "converted": (
            "Field to [figure, unit] the page prints, for a value you converted "
            "from a unit the reader has no alias for."
        ),
        "carried": (
            "Field to where the page gives it from, for a cell it prints blank and "
            "carries from another row."
        ),
        "ranges": (
            "Field to [low, high] for a cell the page prints as an interval; null "
            "for an open end."
        ),
        "bounded_above": "The fields of ranges the page prints as <= x or < x.",
        "bounded_below": "The fields of ranges the page prints as >= x or > x.",
        "reported": (
            "Field to the readings the page lists, with no single value: numbers "
            "or intervals [low, high]."
        ),
        "unquantified": "Field to what the page prints where the number would be.",
        "uncertainty": "Field to the plus-or-minus the page prints beside the value.",
        "not_derivable": "Field to why it is left empty although it could be worked out.",
        "misprinted": "Field to what the page prints there and why it cannot be served.",
        "attributed_to": "Field (or row, or table) to whom the page credits it.",
        "borrowed": "Field to the material the page takes the value from.",
    }
)


def _document(schemas: list[_RowSchema]) -> dict[str, Any]:
    """The top level of the document, over the row classes *schemas* covers."""
    names = [schema.name for schema in schemas]
    text = _ref("text")
    conditions: list[dict[str, Any]] = [
        {
            "if": {"required": ["csv"]},
            "then": {"not": {"required": ["rows"]}},
            "else": {"required": ["rows"]},
        }
    ]
    conditions += [
        {
            "if": {
                "required": ["row_type"],
                "properties": {"row_type": {"const": name}},
            },
            "then": {
                "properties": {
                    "rows": {"items": _ref(name)},
                    "provenance": {
                        "properties": {
                            "field_test_standards": {
                                "propertyNames": _ref(f"{name}.fields")
                            }
                        }
                    },
                }
            },
        }
        for name in names
    ]
    return {
        "type": "object",
        "required": [
            "schema",
            "schema_version",
            "catalogue",
            "row_type",
            "about",
            "provenance",
        ],
        "properties": {
            "$schema": {
                **text,
                "description": (
                    "Where an editor finds this schema. The reader never reads it."
                ),
            },
            "schema": {"const": CATALOGUE_SCHEMA},
            "schema_version": {"const": CATALOGUE_SCHEMA_VERSION},
            "catalogue": {
                "type": "string",
                "pattern": _anchored(_NAME.pattern),
                "not": {"pattern": f"^{_RESERVED.pattern}"},
                "description": (
                    "The catalogue's name, the first half of every key: never a "
                    "four-digit year followed by a word, which is the form of the "
                    "packaged tables' names."
                ),
            },
            "row_type": {
                "enum": names,
                "description": "The row class every row of the document is read into.",
            },
            "about": {
                "allOf": [_ref("prose"), {"pattern": _FILLED}],
                "description": (
                    "What the document is, how it was read and in which units it "
                    "prints."
                ),
            },
            "provenance": _ref("provenance"),
            "basis": {
                "enum": list(CATALOGUE_BASES),
                "description": "The basis of every row that does not give its own.",
            },
            "conventions": {
                "type": "array",
                "items": text,
                "description": (
                    "The notes and legends the document prints for the whole table."
                ),
            },
            "csv": _ref("csv"),
            "rows": {"type": "array", "minItems": 1, "maxItems": _MAX_ROWS},
            "phonometry_version": {
                **text,
                "description": "The version that wrote the file. Never read.",
            },
        },
        "additionalProperties": False,
        "allOf": conditions,
    }


def catalogue_schema(*row_types: type[CatalogueRow]) -> dict[str, Any]:
    """The JSON Schema of a catalogue document whose rows are one of *row_types*.

    An editor that is given it completes a document as it is typed: the
    top-level keys, the provenance and its kinds, every field of the row
    class under its own name and under each other unit the reader converts
    from (``thickness_m`` beside ``thickness_mm``), the fields each hedge may
    name, the words of ``basis``, and a CSV file's header with its dialect.
    It marks what the reader would refuse for its form: a text where a number
    goes, a key the class does not have, a name of the reserved form, a
    density below zero. What depends on two cells at once, such as a value
    beside a hedge that says there is none, is the reader's to refuse, so a
    document the schema accepts may still be refused, and one the reader
    reads is never refused by the schema.

    The schema is written in the 2020-12 dialect and named
    ``urn:phonometry:schema:catalogue:1``. The one the documentation site
    publishes covers every row class the library publishes; a schema of a
    row class of your own covers its fields too.

    :param row_types: One or more subclasses of :class:`CatalogueRow`, a
        caller's own among them.
    :return: A new mapping, ready for :func:`json.dump`.
    :raises TypeError: when no class is given, for anything that is not a
        row class (a :class:`~phonometry.fluids.Fluid` among them), or for two
        classes that share a name, which a document's ``row_type`` could not
        tell apart.
    """
    if not row_types:
        msg = (
            "catalogue_schema() needs at least one row class, such as "
            "materials.PorousMaterial"
        )
        raise TypeError(msg)
    classes: dict[str, type[CatalogueRow]] = {}
    for row_type in _unique(row_types):
        checked = _check_row_type(row_type)
        held = classes.setdefault(checked.__name__, checked)
        if held is not checked:
            msg = (
                f"{held.__module__}.{held.__qualname__} and "
                f"{checked.__module__}.{checked.__qualname__} are both named "
                f"{checked.__name__!r}, and a document's row_type names its class "
                "by that name alone"
            )
            raise TypeError(msg)
    schemas = [_RowSchema(classes[name]) for name in sorted(classes)]
    definitions = _common()
    for schema in schemas:
        definitions.update(schema.definitions())
    return {
        "$schema": _DIALECT,
        "$id": SCHEMA_ID,
        "title": f"phonometry catalogue document, schema version {CATALOGUE_SCHEMA_VERSION}",
        "description": (
            "A catalogue of your own: the rows of one table of a data sheet, a "
            "declaration of performance, a test report or a measurement, which "
            "phonometry.io.read_catalogue reads into rows of the named class; or "
            "the header beside a CSV file, which declares its dialect and holds "
            "no rows. Written by phonometry.io.catalogue_schema. The reader holds "
            "a document to more than its form: what depends on two cells at "
            "once is its alone."
        ),
        **_document(schemas),
        "$defs": dict(sorted(definitions.items())),
    }


def _unique(row_types: Iterable[type[CatalogueRow]]) -> list[type[CatalogueRow]]:
    """*row_types* in order, each once."""
    seen: list[type[CatalogueRow]] = []
    for row_type in row_types:
        if row_type not in seen:
            seen.append(row_type)
    return seen
