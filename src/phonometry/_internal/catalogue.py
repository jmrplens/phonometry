#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Reading a published table out of a data file, and the row every table holds.

A catalogue row is data, not code. Keeping the rows in JSON beside the module
that publishes them means a new table is a new file rather than a longer
literal, means one row per record in a diff, and means the provenance gate can
read the citation without importing anything.

The document is one published table: a ``source`` in the grammar
``scripts/check_published_sources.py`` enforces, an ``about`` paragraph saying
what the page is and how it was read, and ``rows``. Every row carries a ``key``
unique within the file, and the rest of its fields are named exactly as the
dataclass that will hold them, so a typo in the data is a ``TypeError`` at
import and not a silently missing column. The reader is strict about the text
itself too: a ``NaN`` or an ``Infinity``, which only CPython's reader accepts,
a name written twice in one object, which JSON resolves by keeping the last,
and a ``/`` in a row key, which separates the table from the row in every
catalogue, are each refused by name before any row is built.

:class:`CatalogueRow` is what every such dataclass inherits: the name, the
citation and the hedges a printed cell can carry instead of a number. A page
prints a range, or a ``~``, or three values from three studies, or a word, and
a catalogue that flattened any of those into a float would be claiming a
measurement the page does not make. The hedges are the same across the
catalogues because the pages are: a range in a table of solids is a range in
a table of porous materials. A row checks itself when it is built, whoever
builds it: a data file, a loader or a caller writing one by hand.

The reader stays private. :class:`CatalogueRow`, :class:`BandedRow`,
:class:`CatalogueError` and :data:`CATALOGUE_BASES` are public, from
:mod:`phonometry.io`, because every catalogue of the library hands out rows
built on them, and a caller has to be able to name the type of what it holds
and catch what the constructor raises. They are defined here and not there
because the domain packages that publish the rows import them, and
:mod:`phonometry.io` importing a domain would close a cycle.
"""

from __future__ import annotations

import json
import math
import numbers
import types
import typing
import weakref
from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field, fields
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar, NamedTuple, NoReturn

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

_REQUIRED = ("source", "about", "rows")

#: Everything a packaged table may hold at its top level: the three every
#: table needs, the printed legends two tables carry (``conventions``) and the
#: hedge the two fluid tables put on the whole table (``validity``).
_PACKAGED_KEYS = frozenset({*_REQUIRED, "conventions", "validity"})

#: What a source can say a value is, and nothing else: a test result it
#: gives (``"measured"``), a value, bound or class declared under a product
#: standard or a CE marking (``"declared"``), a figure it worked out itself,
#: by a standard's model, a program or a formula (``"calculated"``), its own
#: estimate (``"estimated"``), or the result of an extended application of a
#: test (``"extended"``). A source that does not say is left without an
#: entry rather than given one of these.
CATALOGUE_BASES: tuple[str, ...] = (
    "measured",
    "declared",
    "calculated",
    "estimated",
    "extended",
)


class CatalogueError(ValueError):
    """A catalogue that does not say what a reader needs to trust it.

    Raised for a table document that is missing what every table needs (a
    citation, an ``about``, rows, a key per row) or that holds what JSON
    does not (a ``NaN``, a name written twice in one object), and for a row
    that breaks the contract every row is held to when it is built: a
    numeric cell holding text or a ``NaN``, a hedge naming a field the row
    does not have, a bound with no printed end, a density below zero. A
    :class:`ValueError`, because the data is wrong and not the call, whether
    it came from a file or from a caller building a row by hand.
    """


def _reject(filename: str, what: str) -> NoReturn:
    """Name the file and the defect, because the caller cannot see either."""
    msg = f"{filename}: {what}"
    raise CatalogueError(msg)


# ---------------------------------------------------------------------------
# Reading a table: strict JSON, then the shape every packaged table has
# ---------------------------------------------------------------------------
class _Repeated(dict[str, Any]):
    """An object whose text names one member twice, with the names it repeats.

    JSON keeps the last of two members with one name and says nothing, so a
    row that typed a density twice would publish whichever came second. The
    reader marks the object instead of refusing on the spot, because at that
    point it does not yet know which row the object belongs to.
    """

    repeated: tuple[str, ...] = ()


class _Constant:
    """A ``NaN`` or an infinity in the text, kept only long enough to be found."""

    __slots__ = ("token",)

    def __init__(self, token: str) -> None:
        self.token = token


def _flaws(node: object, path: str, root: str) -> Iterator[str]:
    """What is wrong with *node* and everything under it, each with its path.

    :param node: A decoded value.
    :param path: Where *node* sits under the object the walk started from,
        empty for that object itself.
    :param root: What that object is called in a message, for a flaw at its
        own level: ``"the row"`` or ``"the document"``.
    """
    if isinstance(node, _Constant):
        yield (
            f"{path} is {node.token}, which is not JSON and not a number any "
            "page prints"
        )
    elif isinstance(node, dict):
        if isinstance(node, _Repeated):
            names = ", ".join(repr(name) for name in node.repeated)
            yield f"{path or root} names {names} twice, and JSON keeps only the last"
        for key, value in node.items():
            yield from _flaws(value, f"{path}.{key}" if path else key, root)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _flaws(value, f"{path}[{index}]", root)


def _refuse_flaws(document: object, label: str) -> NoReturn:
    """Refuse a document that holds a marked flaw, naming the row it sits in."""
    rows = document.get("rows") if isinstance(document, dict) else None
    for row in rows if isinstance(rows, list) else ():
        for flaw in _flaws(row, "", "the row"):
            key = row.get("key") if isinstance(row, dict) else None
            _reject(label, f"row {key!r}: {flaw}")
    for flaw in _flaws(document, "", "the document"):
        _reject(label, flaw)
    _reject(label, "the text holds something JSON does not")  # pragma: no cover


def _strict_json(text: str, label: str) -> object:
    """The document *text* holds, refusing what only CPython's reader accepts.

    :param text: The file's text.
    :param label: What names the file in a refusal.
    :return: The decoded document.
    :raises CatalogueError: for text that is not JSON, for a ``NaN`` or an
        infinity, and for a name written twice in one object.
    """
    flagged: list[object] = []

    def members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        obj = dict(pairs)
        if len(obj) == len(pairs):
            return obj
        seen: set[str] = set()
        twice: dict[str, None] = {}
        for name, _ in pairs:
            if name in seen:
                twice[name] = None
            seen.add(name)
        marked = _Repeated(obj)
        marked.repeated = tuple(twice)
        flagged.append(marked)
        return marked

    def constant(token: str) -> _Constant:
        marked = _Constant(token)
        flagged.append(marked)
        return marked

    try:
        document = json.loads(text, parse_constant=constant, object_pairs_hook=members)
    except json.JSONDecodeError as error:
        msg = f"{label}: this is not JSON ({error})"
        raise CatalogueError(msg) from error
    if flagged:
        _refuse_flaws(document, label)
    return document


def _check_packaged_rows(rows: object, label: str) -> None:
    """The rows of a packaged table, each an object with a key of its own."""
    if not isinstance(rows, list) or not rows:
        _reject(label, "a published table with no rows publishes nothing")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            _reject(label, f"every row is a JSON object, and one is {row!r}")
        key = row.get("key")
        if key is None:
            _reject(label, "every row needs a key of its own")
        if not isinstance(key, str):
            _reject(label, f"the key {key!r} is not text")
        if "/" in key:
            _reject(
                label,
                f"row {key!r}: a row key holds no '/', which separates the table "
                "from the row in every catalogue's keys",
            )
        if key in seen:
            _reject(label, f"two rows share the key {key!r}")
        seen.add(key)


def parse_packaged(text: str, label: str) -> dict[str, Any]:
    """One packaged table from its text, checked before any row is built.

    The shared reader of the packaged data files: JSON as a browser reads it,
    with no ``NaN``, no infinity and no name written twice in one object;
    the three top-level keys every table needs, and nothing at the top level
    but those, the printed ``conventions`` and a fluid table's
    ``validity``; and rows that are objects, each with a key of its own that
    holds no ``/``. What a row's fields mean is left to the dataclass that
    holds it, because the loader chooses that and a fluid table has none.

    :param text: The file's text.
    :param label: What names the file in a refusal, its file name.
    :return: The decoded document.
    :raises CatalogueError: naming the file, and the row when there is one,
        for any of the above.
    """
    document = _strict_json(text, label)
    if not isinstance(document, dict):
        _reject(label, "a published table is one JSON object")
    for key in _REQUIRED:
        if key not in document:
            _reject(label, f"a published table needs a top-level {key!r}")
    for key in document:
        if key not in _PACKAGED_KEYS:
            allowed = ", ".join(repr(name) for name in sorted(_PACKAGED_KEYS))
            _reject(
                label,
                f"a published table has no top-level {key!r}; it holds {allowed}",
            )
    _check_packaged_rows(document["rows"], label)
    return document


def read_packaged(package: str, filename: str) -> dict[str, Any]:
    """The whole of one published table from a package's ``data`` directory.

    For a loader that needs more of the document than its rows, as the fluid
    tables need the ``validity`` they put on the whole table; the text goes
    through :func:`parse_packaged` like every other packaged table.

    :param package: The package that owns the data, as ``phonometry.solids``.
        The file is read from its ``data`` subpackage.
    :param filename: The file name inside ``data``, including the extension.
    :return: The decoded document.
    :raises CatalogueError: for anything :func:`parse_packaged` refuses.
    """
    from importlib.resources import files

    text = (files(f"{package}.data") / filename).read_text(encoding="utf-8")
    return parse_packaged(text, filename)


def read_table(package: str, filename: str) -> tuple[str, tuple[dict[str, Any], ...]]:
    """Read one published table from a package's ``data`` directory.

    :param package: The package that owns the data, as ``phonometry.solids``.
        The file is read from its ``data`` subpackage.
    :param filename: The file name inside ``data``, including the extension.
    :return: The citation every row of the file shares, and the rows in the
        order the file lists them, each a plain dictionary ready to be passed
        to the dataclass that holds it.
    :raises CatalogueError: for anything :func:`parse_packaged` refuses: a
        missing or unknown top-level key, no rows, two rows sharing a key, a
        ``/`` in a key, a ``NaN`` or a name written twice.
    """
    document = read_packaged(package, filename)
    return document["source"], tuple(document["rows"])


def take(row: Mapping[str, Any]) -> dict[str, Any]:
    """The row as constructor keywords: everything but the ``key``.

    Nothing is converted here. A data file writes a set of field names as a
    list and an interval as a two-item list, because JSON has neither sets
    nor tuples, and the row freezes each field into the type its annotation
    names when it is built.

    :param row: One row as :func:`read_table` returned it.
    :return: The remaining fields, ready to splat into the dataclass.
    """
    return {name: value for name, value in row.items() if name != "key"}


# ---------------------------------------------------------------------------
# The row contract: what a row is checked for and frozen into when it is built
# ---------------------------------------------------------------------------
#: One field's check: it takes the value and where the value sits, for the
#: message, and returns the value as the row keeps it (frozen, for a set or a
#: mapping) or raises :class:`CatalogueError`.
type _Check = Callable[[object, str], object]

#: The two spellings of a union a resolved annotation can come back as.
_UNIONS = (typing.Union, types.UnionType)

#: The kinds of field that hold a number.
_NUMERIC = frozenset({"number", "whole"})

#: The one empty mapping every row holds for a hedge it does not use. Nothing
#: can reach the dict behind it, so sharing it is sharing nothing.
_NOTHING: Mapping[str, Any] = MappingProxyType({})

#: How much of a refused value a message quotes.
_QUOTED = 80

#: The words a hedge may use in place of a field name: the whole row, and,
#: for a credit, the whole table.
_ROW_WORDS: Mapping[str, frozenset[str]] = MappingProxyType(
    {"basis": frozenset({"row"}), "attributed_to": frozenset({"row", "table"})}
)

#: The hedges that say what a numeric cell holds instead of a value: a word,
#: why this library leaves it empty, several readings with no single one. A
#: value beside any of them would be served while the hedge says there is
#: none, and ``misprinted`` on a number says the same.
_HOLDS_NOTHING = ("unquantified", "not_derivable", "reported")

#: The unit suffixes of the quantities that cannot be negative: a density, a
#: mass per area, a mass, a molar mass, a speed, a pressure or modulus, a flow
#: resistivity, a specific flow resistance, a stiffness per area, a length in
#: millimetres, micrometres or metres, an area, a thickness-frequency product
#: and a count per centimetre. Named by the unit the field carries, which is a
#: physical limit and not a guard on how large a value may be. A refusal names
#: the suffix rather than a unit, because a field named for a compound unit
#: (``surface_density_g_m2``) ends in a shorter one (``_m2``) that is not its
#: own.
_NOT_NEGATIVE = (
    "_kg_m3",
    "_kg_m2",
    "_kg",
    "_kg_mol",
    "_m_s",
    "_pa",
    "_pa_s_m2",
    "_pa_s_m",
    "_n_m3",
    "_mm",
    "_um",
    "_m",
    "_m2",
    "_m_hz",
    "_per_cm",
)

#: The unit suffixes of quantities that can be negative, and which a shorter
#: suffix above would otherwise claim: a Celsius temperature, a decay rate
#: per metre (Attenborough's porosity profiles), and a level in decibels.
#: The longest suffix a field name ends in decides.
_SIGNED = ("_c", "_per_m", "_db")

#: The per-cent fields that are a share of a whole, and so run from 0 to 100.
#: Not every ``_percent``: a water content on a dry basis passes 100.
_SHARES = frozenset(
    {"shot_content_percent", "binder_content_percent", "adhered_area_percent"}
)


def _quote(value: object) -> str:
    """*value* as a message quotes it: its ``repr``, cut at a readable length."""
    text = repr(value)
    return text if len(text) <= _QUOTED else f"{text[: _QUOTED - 3]}..."


def _refuse(where: str, value: object, what: str) -> NoReturn:
    """Refuse *value* at *where* for not being *what* the field holds."""
    msg = f"{where} holds {_quote(value)}, which is not {what}"
    raise CatalogueError(msg)


def _text(value: object, where: str) -> object:
    if not isinstance(value, str):
        _refuse(where, value, "text")
    return value


def _flag(value: object, where: str) -> object:
    if not isinstance(value, bool):
        _refuse(where, value, "True or False")
    return value


def _whole(value: object, where: str) -> object:
    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        _refuse(where, value, "a whole number")
    return value


def _real(value: object, where: str) -> object:
    # ``float`` and ``int`` are what a data file holds, and checking them by
    # type first spares every packaged cell the slower abstract check.
    exact = type(value) is float or type(value) is int
    if not exact and (isinstance(value, bool) or not isinstance(value, numbers.Real)):
        _refuse(where, value, "a finite number")
    try:
        finite = math.isfinite(typing.cast("float", value))
    except OverflowError:
        finite = False
    if not finite:
        _refuse(where, value, "a finite number")
    return value


def _names(value: object, where: str) -> frozenset[str]:
    if isinstance(value, frozenset) and all(type(item) is str for item in value):
        return value
    if isinstance(value, (list, tuple, AbstractSet)) and not isinstance(value, str):
        return frozenset(
            typing.cast("str", _text(item, f"{where}[{index}]"))
            for index, item in enumerate(value)
        )
    _refuse(where, value, "a set of field names")


def _optional(check: _Check) -> _Check:
    def optional(value: object, where: str) -> object:
        return None if value is None else check(value, where)

    return optional


def _fixed(checks: tuple[_Check, ...]) -> _Check:
    def fixed(value: object, where: str) -> object:
        if not isinstance(value, (list, tuple)) or len(value) != len(checks):
            _refuse(where, value, f"a list of {len(checks)}")
        return tuple(
            check(item, f"{where}[{index}]")
            for index, (check, item) in enumerate(zip(checks, value, strict=True))
        )

    return fixed


def _any_length(check: _Check) -> _Check:
    def any_length(value: object, where: str) -> object:
        if not isinstance(value, (list, tuple)):
            _refuse(where, value, "a list")
        return tuple(
            check(item, f"{where}[{index}]") for index, item in enumerate(value)
        )

    return any_length


def _either(scalar: _Check, sequence: _Check) -> _Check:
    def either(value: object, where: str) -> object:
        if isinstance(value, (list, tuple)):
            return sequence(value, where)
        return scalar(value, where)

    return either


def _mapping_of(check: _Check) -> _Check:
    def mapping(value: object, where: str) -> object:
        if type(value) is dict or type(value) is MappingProxyType:
            if not value:
                return _NOTHING
        elif not isinstance(value, Mapping):
            _refuse(where, value, "a mapping")
        return MappingProxyType(
            {
                _text(key, f"{where} key"): check(item, f"{where}[{key!r}]")
                for key, item in value.items()
            }
        )

    return mapping


def _leaf(hint: object) -> _Check | None:
    """The check for a plain value annotated *hint*, if it is one."""
    if hint is str:
        return _text
    if hint is bool:
        return _flag
    if hint is int:
        return _whole
    if hint is float:
        return _real
    return None


def _tuple_check(args: tuple[object, ...]) -> _Check | None:
    """The check for ``tuple[...]`` over *args*, fixed or of any length."""
    if args[1:] == (Ellipsis,):
        item = _value_check(args[0])
        return None if item is None else _any_length(item)
    items = tuple(_value_check(arg) for arg in args)
    if not items or any(item is None for item in items):
        return None
    return _fixed(typing.cast("tuple[_Check, ...]", items))


def _union_check(args: tuple[object, ...]) -> _Check | None:
    """The check for a union: at most one plain value and one tuple, or None."""
    members = [arg for arg in args if arg is not type(None)]
    sequences = [arg for arg in members if typing.get_origin(arg) is tuple]
    scalars = [arg for arg in members if typing.get_origin(arg) is not tuple]
    if len(sequences) > 1 or len(scalars) > 1:
        return None
    scalar = _leaf(scalars[0]) if scalars else None
    sequence = _tuple_check(typing.get_args(sequences[0])) if sequences else None
    if (scalars and scalar is None) or (sequences and sequence is None):
        return None
    if scalar is not None and sequence is not None:
        check = _either(scalar, sequence)
    else:
        check = typing.cast("_Check", scalar or sequence)
    return _optional(check) if len(members) < len(args) else check


def _value_check(hint: object) -> _Check | None:
    """The check for a value held inside a mapping or a tuple."""
    leaf = _leaf(hint)
    if leaf is not None:
        return leaf
    origin = typing.get_origin(hint)
    if origin is tuple:
        return _tuple_check(typing.get_args(hint))
    if origin in _UNIONS:
        return _union_check(typing.get_args(hint))
    return None


def _field_check(hint: object) -> tuple[str, _Check] | None:
    """What kind of field *hint* annotates, and the check its value gets.

    The kinds are ``"number"`` (``float | None``), ``"whole"``
    (``int | None``), ``"flag"`` (``bool``), ``"text"`` (``str``), ``"set"``
    (``frozenset[str]``) and ``"mapping"`` (``Mapping[str, ...]`` of plain
    values and tuples of them). ``Optional[float]`` is ``float | None``, and
    on Python 3.14 the same object. Anything else answers ``None``, a bare
    ``float`` or ``int`` included: every quantity of a row may be missing,
    because the pages print different columns, and a row that could not say
    so would have no answer for :meth:`CatalogueRow.why_missing` to give.
    """
    if hint is bool:
        return "flag", _flag
    if hint is str:
        return "text", _text
    origin, args = typing.get_origin(hint), typing.get_args(hint)
    if origin is frozenset and args == (str,):
        return "set", _names
    if origin is Mapping and args[:1] == (str,):
        check = _value_check(args[-1])
        return None if check is None else ("mapping", _mapping_of(check))
    if origin not in _UNIONS or type(None) not in args:
        return None
    members = {arg for arg in args if arg is not type(None)}
    for kind, plain, leaf in (("number", float, _real), ("whole", int, _whole)):
        if members == {plain}:
            return kind, _optional(leaf)
    return None


def _limit(field_name: str) -> tuple[float, float | None, str] | None:
    """The physical bounds of a numeric field, from its name, if it has any."""
    if field_name == "porosity":
        return 0.0, 1.0, "a porosity is a fraction from 0 to 1"
    if field_name in _SHARES:
        return 0.0, 100.0, "a share of a whole runs from 0 to 100 per cent"
    suffix = max(
        (s for s in (*_NOT_NEGATIVE, *_SIGNED) if field_name.endswith(s)),
        key=len,
        default="",
    )
    if suffix in _NOT_NEGATIVE:
        return 0.0, None, f"a quantity whose name ends in {suffix} is never negative"
    return None


class _Shape(NamedTuple):
    """What the contract needs to know about one row class, worked out once."""

    #: Every field in declaration order, with the check its value gets.
    checks: tuple[tuple[str, _Check], ...]
    #: The fields that hold a number, an ``int`` included.
    numeric: frozenset[str]
    #: The fields that hold a value of any kind: numbers, flags and text.
    values: frozenset[str]
    #: What a hedge that may name text may name: the numbers and the text
    #: fields, but not the citation or the table the row was read from, which
    #: are not cells of the page.
    cells: frozenset[str]
    #: The fields that hold text.
    texts: frozenset[str]
    #: ``(field, low, high, why)`` for each numeric field with a physical limit.
    limits: tuple[tuple[str, float, float | None, str], ...]


#: The shape of every row class built so far. Weakly keyed, so a caller's
#: subclass is not kept alive by having been built once.
_SHAPES: weakref.WeakKeyDictionary[type, _Shape] = weakref.WeakKeyDictionary()


def _shape(cls: type) -> _Shape:
    """The shape of *cls*, classified the first time a row of it is built.

    The classification is cached per class, which is what keeps the check of
    the packaged rows at import to a single pass over their values.
    """
    shape = _SHAPES.get(cls)
    if shape is None:
        shape = _SHAPES[cls] = _classify(cls)
    return shape


def _classify(cls: type) -> _Shape:
    """Classify every field of *cls* from its resolved annotations.

    ``typing.get_type_hints`` resolves each annotation in the module that
    wrote it, and the catalogue modules import ``Mapping`` for the type
    checker only, so it is supplied here.

    :raises TypeError: for an annotation that does not resolve, or that no
        check exists for, naming the class and the field: a field the
        contract cannot classify would reach every caller unchecked.
    """
    try:
        hints = typing.get_type_hints(cls, localns={"Mapping": Mapping})
    except (NameError, SyntaxError, TypeError) as error:
        msg = (
            f"{cls.__qualname__}: an annotation does not resolve ({error}); a "
            "catalogue row's annotations have to resolve at run time"
        )
        raise TypeError(msg) from error
    checks: list[tuple[str, _Check]] = []
    kinds: dict[str, str] = {}
    for item in fields(cls):
        classified = _field_check(hints[item.name])
        if classified is None:
            msg = (
                f"{cls.__qualname__}.{item.name} is annotated "
                f"{hints[item.name]!r}, which a catalogue row cannot check: a "
                "field is float | None, int | None, bool, str, frozenset[str] "
                "or a Mapping[str, ...] of those, and a quantity is never a "
                "bare float or int, because every cell of a row may be missing"
            )
            raise TypeError(msg)
        kinds[item.name], check = classified
        checks.append((item.name, check))
    numeric = frozenset(name for name, kind in kinds.items() if kind in _NUMERIC)
    texts = frozenset(name for name, kind in kinds.items() if kind == "text")
    flags = frozenset(name for name, kind in kinds.items() if kind == "flag")
    limits = tuple(
        (name, *bounds) for name in sorted(numeric) if (bounds := _limit(name))
    )
    values = numeric | texts | flags
    cells = (numeric | texts) - {"source", "table"}
    return _Shape(tuple(checks), numeric, values, cells, texts, limits)


def _spell(entry: float | tuple[float, float]) -> str:
    """One listed value or interval, the way the page would read it aloud."""
    if isinstance(entry, tuple):
        low, high = entry
        return f"{low:g} to {high:g}"
    return f"{entry:g}"


@dataclass(frozen=True, kw_only=True)
class CatalogueRow:
    """One row of a published table, with what each cell said.

    The quantities are the subclass's business; this holds what surrounds
    them. A numeric field of the subclass is ``None`` whenever the page had
    something other than a single number there, and the hedges below say
    what: an interval in :attr:`ranges`, a list of values in
    :attr:`reported`, a word in :attr:`unquantified`. :meth:`why_missing`
    reads them back in the page's own terms, so a caller who gets ``None``
    is not left to guess whether the material has no such property, whether
    the book left the cell empty, or whether it printed three numbers.

    Every row of every published catalogue is one of these, a frozen and
    keyword-only dataclass. A subclass written to hold a quantity no
    catalogue of the library publishes is the same, and it leaves out
    ``slots=True``: on the Python 3.13 releases that predate the fix, a
    slotted dataclass that calls ``super()`` without arguments, as a
    ``__post_init__`` does, raises :class:`TypeError` when it is built.

    **A row checks itself when it is built**, whoever builds it, and refuses
    with :class:`CatalogueError` rather than holding a cell nothing
    downstream can read. The check is the same for a packaged row, a row a
    reader builds from a file and a row written by hand:

    1. :attr:`name` and :attr:`source` are text that is not empty, and so is
       every text a hedge holds: :meth:`why_missing` hands a
       :attr:`misprinted` or :attr:`not_derivable` text back as it is, and
       an empty one would answer as a cell that is not missing at all.
    2. A numeric field holds ``None`` or a finite number, never a ``bool``, a
       text or a ``NaN``; an ``int`` field a whole number; a ``bool`` field
       ``True`` or ``False``; a text field text.
    3. A set of field names (:attr:`approximate` and the bounds) is frozen
       into a ``frozenset``, whatever it was written as.
    4. Every mapping is frozen, all the way down: its pairs into tuples.
    5. Every key of a hedge names a numeric field of the row. :attr:`basis`
       and :attr:`attributed_to` also take the ``"row"``, and a credit the
       ``"table"``; :attr:`derived`, :attr:`carried` and :attr:`misprinted`
       may name a text field too (but not :attr:`source` or :attr:`table`,
       which are not cells of the page), because a page misprints a name or
       gives a description by reference to another row.
    6. :attr:`bounded_above` and :attr:`bounded_below` name only fields that
       have a range.
    7. A range's ends are finite, the low one no higher than the high one,
       and the end the page printed is there; an interval among the
       readings of :attr:`reported` runs from low to high as well.
    8. A list in :attr:`reported` holds at least one reading, and its
       readings are finite; an :attr:`uncertainty` is finite and not below
       zero.
    9. A field in :attr:`unquantified`, :attr:`not_derivable` or
       :attr:`reported`, or a numeric field in :attr:`misprinted`, holds no
       value; a field in :attr:`converted` or :attr:`carried` holds
       something: a value, a range or a list.
    10. :attr:`basis` holds only the words of :data:`CATALOGUE_BASES`.
    11. A quantity whose unit cannot be negative is not: a field ending in
        ``_kg_m3``, ``_kg_m2``, ``_kg``, ``_kg_mol``, ``_m_s``, ``_pa``,
        ``_pa_s_m2``, ``_pa_s_m``, ``_n_m3``, ``_mm``, ``_um``, ``_m``,
        ``_m2``, ``_m_hz`` or ``_per_cm``, in its value, its range and its
        readings. A ``porosity`` runs from 0 to 1, and the per-cent fields
        that are a share of a whole (``shot_content_percent``,
        ``binder_content_percent`` and ``adhered_area_percent``) from 0 to
        100.
        Nothing else is bounded: a Celsius temperature, a decay rate per
        metre and a level in decibels can be negative, and a size is never
        a reason to refuse a number.

    The fields are told apart by their resolved annotations, once per
    class, so a subclass annotates each of its own fields as one of
    ``float | None`` (``Optional[float]`` is the same annotation),
    ``int | None``, ``bool``, ``str``, ``frozenset[str]`` or
    ``Mapping[str, ...]`` of those; any other annotation, a bare ``float``
    or ``int`` included, raises :class:`TypeError` the first time the class
    is built, rather than letting a field through unchecked.

    :ivar name: The material as the table names it, attribution stripped.
    :ivar variant: Which specimen or condition this row is, when the page
        prints several under one name: ``"chemically pure"``, ``"direction
        x"``, ``"0.68 mm diameter"``. Empty when the page prints one.
    :ivar source: Document, table, PDF page and printed folio.
    :ivar table: The data file this row was read from, without the
        extension, which is also the first half of its key in the catalogue
        that holds it.
    :ivar basis: What the source says a value is: a field name, or ``"row"``
        for the whole row, to one of :data:`CATALOGUE_BASES`. Hopkins marks
        most of his Poisson ratios "Estimate", and those cells hold
        ``"estimated"``; a datasheet that declares a class under a product
        standard would hold ``"declared"``. A field with no entry takes the
        row's, and a row with neither is one whose source does not say,
        which is a different answer from any of the five. :meth:`basis_of`
        reads it. Independent of :attr:`derived`: this is what the source
        claims for a cell, that is what this library computed.
    :ivar approximate: Fields the page prints with a ``~``. Not an estimate
        and not an interval: a number the author rounded on purpose.
    :ivar derived: Field to how it was computed, for the ones this library
        worked out from the cells the page did print. A derived value is never
        stored as if it had been read, and it always follows again from the
        row's own cells. A value converted from the unit the page prints is
        not derived (:attr:`converted` holds it), and neither is one the page
        gives by reference to another of its rows (:attr:`carried` does).
    :ivar converted: Field to ``(figure, unit)``, the page's figure and the
        unit it is in, for a value this row holds in a unit the page does
        not use. Ver and Beranek print their damping materials in degrees
        Fahrenheit and pounds per square inch, and the row holds degrees
        Celsius and pascals, so ``("3e5", "psi")`` sits beside a modulus in
        pascals. The figure is kept as the page writes it, so the cell can
        always be read back in the page's own terms. The unit is the one the
        page prints with the figure or over its column. Long prints the
        figures of his musician bare, and the sabins recorded for them are a
        reading of the table, which is set in inches and pounds and names
        sabins on the next row; that row's note says so. A figure a
        packaged table prints with another SI prefix, such as the megapascals
        of Rossing Table 15.5, is held in the base unit with no entry here,
        and the table's ``about`` says so.
    :ivar carried: Field to where the page gives it from, for a value the
        page gives by reference to another of its rows rather than on this
        one: a cell left blank under a block whose first row prints the
        figure, as in Ver and Beranek Table 8.7, or a description that reads
        "Parecido al anterior" and prints no row number, as three rows of
        Harris Chapter 32 do, which refers to the row above it. The value is
        the page's, and this says which of its rows gives it.
    :ivar ranges: ``(low, high)`` for each field the page prints as an
        interval rather than a value. One end is ``None`` only for a bound
        whose open side the quantity has no limit on; the end the page prints
        is always a number, and a two-sided interval has two.
    :ivar bounded_above: The subset of :attr:`ranges` the page prints as
        ``< x`` or ``<= x``, where the low end is a floor and not a
        measurement.
    :ivar bounded_below: The subset of :attr:`ranges` the page prints as
        ``> x`` or ``>= x``, where the high end is the ceiling the quantity
        cannot pass and not a measurement: Cox gives an aerogel a porosity of
        ``>0.75``, and the 1 beside it is what a porosity is, not what anybody
        measured. A quantity with no such ceiling leaves that end ``None``
        rather than borrowing a number for it: ASHRAE prints ``>45`` for a
        duct wall whose radiated sound the background swamped, and a
        transmission loss has no value it cannot pass, so the open end is
        empty. It is never an infinity, which is not a number the page has
        and not a token JSON can carry.
    :ivar reported: Field to the values the page lists for it, for a cell that
        prints several with no single one: ``"25, 207, 230"`` or ``"96,
        200-450"``, readings from as many studies. Each entry is a number or
        a ``(low, high)`` pair. Not a range, because the page did not print
        one, and not variants, because the page does not say which is which.
    :ivar unquantified: Field to what the page printed in place of a number,
        for a cell that is neither empty nor numeric: ``"Varies with
        frequency"``, ``"model"``, ``"…"`` for a row of dots. What the page
        printed, and never a sentence about why the number is missing:
        :meth:`why_missing` composes that sentence around it, so a caller and
        a published table both get the cell as it reads on the page.
    :ivar uncertainty: Field to the plus-or-minus the page prints beside the
        value, in the same unit. Cox prints an effective flow resistivity of
        ``(540 +/- 92) x 10^3``, and two of his rows print an uncertainty as
        large as the value itself. What the interval means is not stated on
        the page, so it is not stated here either: it is the number the page
        prints beside the value and nothing more.
    :ivar misprinted: Field to what the page prints there and why it cannot be
        that, for a cell whose defect is confirmed and registered in
        ``docs/ERRATA.md``. The number is not served, because a catalogue that
        handed it over would put a value its own registry calls wrong behind
        every calculation downstream; it is not dropped either, because a
        reader reproducing the book needs to see what the book says. This is
        the narrowest of the hedges and the one that costs most to claim: a
        cell earns it only when the defect follows from the page itself or
        from something as settled as the molar mass of a named molecule, and
        never from one book disagreeing with another.
    :ivar not_derivable: Field to why this library leaves it empty although
        the arithmetic would reach it. Bies leaves the speed of his aluminium
        honeycomb panels blank, and the modulus and the density beside it are
        effective ones, so ``sqrt(E/rho)`` would put a one-dimensional speed
        on a panel that has none. A row says so here, and nothing fills the
        cell afterwards.
    :ivar attributed_to: Credit for a cell the book takes from someone else.
        Keyed by field name, or by ``"row"`` or ``"table"`` when the credit
        covers all of one.
    :ivar group: The heading of the block this row sits under, when the table
        prints its rows in named groups: Cox files each material under
        ``"Fibrous materials"``, ``"Cellular materials"``,
        ``"Granular materials"`` or ``"Other"``. Empty for a table that prints
        one list.
    :ivar note: What the page says about this row beyond its numbers.
    """

    #: The hedges whose keys name a numeric field: what the page printed in
    #: place of a number or beside it, what the source claims it is, and who
    #: it is credited to (these two also take the ``"row"``, and a credit the
    #: ``"table"``). A subclass with a hedge of its own extends it, as
    #: :class:`~phonometry.solids.SolidMaterial` does with ``borrowed``.
    _number_hedges: ClassVar[tuple[str, ...]] = (
        "approximate",
        "converted",
        "ranges",
        "bounded_above",
        "bounded_below",
        "reported",
        "unquantified",
        "uncertainty",
        "not_derivable",
        "basis",
        "attributed_to",
    )
    #: The hedges whose keys may name a text field as well as a numeric one,
    #: because a page prints them there: Harris prints a misspelt material
    #: name, and three of his descriptions give their row by reference to the
    #: one above.
    _value_hedges: ClassVar[tuple[str, ...]] = ("derived", "carried", "misprinted")

    name: str
    source: str
    table: str = ""
    variant: str = ""
    basis: Mapping[str, str] = field(default_factory=dict)
    approximate: frozenset[str] = frozenset()
    derived: Mapping[str, str] = field(default_factory=dict)
    converted: Mapping[str, tuple[str, str]] = field(default_factory=dict)
    carried: Mapping[str, str] = field(default_factory=dict)
    ranges: Mapping[str, tuple[float | None, float | None]] = field(
        default_factory=dict
    )
    bounded_above: frozenset[str] = frozenset()
    bounded_below: frozenset[str] = frozenset()
    reported: Mapping[str, tuple[float | tuple[float, float], ...]] = field(
        default_factory=dict
    )
    unquantified: Mapping[str, str] = field(default_factory=dict)
    uncertainty: Mapping[str, float] = field(default_factory=dict)
    not_derivable: Mapping[str, str] = field(default_factory=dict)
    misprinted: Mapping[str, str] = field(default_factory=dict)
    attributed_to: Mapping[str, str] = field(default_factory=dict)
    group: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        """Hold the row to the contract every row is held to, and freeze it.

        ``frozen=True`` refuses to rebind a field and says nothing about what
        the field points at, so a set left a list, or a mapping left a dict,
        would be editable in place while the row around it was not. The
        catalogue is one object shared by every caller, and provenance one of
        them can rewrite is worth less than none. The eleven rules the class
        docstring lists run here, the field checks first, so the first
        broken one is the one named.

        :raises CatalogueError: naming the row, the field and what it holds,
            for the first rule the row breaks.
        :raises TypeError: for a subclass field whose annotation the contract
            cannot classify.
        """
        shape = _shape(type(self))
        try:
            for field_name, check in shape.checks:
                value = getattr(self, field_name)
                kept = check(value, field_name)
                if kept is not value:
                    object.__setattr__(self, field_name, kept)
        except CatalogueError as error:
            msg = f"{self.name!r}: {error}"
            raise CatalogueError(msg) from None
        self._check_name_and_source()
        self._check_hedge_keys(shape)
        self._check_hedge_texts()
        self._check_bounds_have_ranges()
        self._check_range_ends()
        self._check_reported()
        self._check_uncertainty()
        self._check_cells_that_hold_nothing(shape)
        self._check_cells_that_hold_something(shape)
        self._check_basis()
        self._check_limits(shape)

    def _check_name_and_source(self) -> None:
        """Refuse a row with no name or no citation.

        A row is found by its name and trusted for its source, and a row
        with neither is a number nobody can look up or check.

        :raises CatalogueError: naming the one that is empty.
        """
        for field_name in ("name", "source"):
            if not getattr(self, field_name).strip():
                msg = (
                    f"a catalogue row needs a name and a source, and the row "
                    f"{self.name!r} from {self.source!r} has no {field_name}"
                )
                raise CatalogueError(msg)

    def _check_hedge_keys(self, shape: _Shape) -> None:
        """Refuse a hedge keyed by a name that is not a field of this row.

        A hedge on a misspelt field hedges nothing: the cell it meant keeps
        answering as a plain number, and the hedge is never read.

        :raises CatalogueError: naming the hedge, the key and the class.
        """
        for hedges, allowed, what in (
            (self._number_hedges, shape.numeric, "a numeric field"),
            (self._value_hedges, shape.cells, "a field"),
        ):
            for hedge in hedges:
                keys = getattr(self, hedge)
                if not keys:
                    continue
                words = _ROW_WORDS.get(hedge, frozenset())
                for key in keys:
                    if key not in allowed and key not in words:
                        msg = (
                            f"{self.name!r}: {hedge} names {key!r}, which is not "
                            f"{what} of {type(self).__name__}"
                        )
                        raise CatalogueError(msg)

    def _check_hedge_texts(self) -> None:
        """Refuse a hedge whose text says nothing.

        :meth:`why_missing` hands a :attr:`misprinted` or
        :attr:`not_derivable` text back as it is, so an empty one answers
        ``""``, which is the answer of a cell that holds its value, and hides
        the defect the hedge was written to record. An empty word, credit,
        source row or printed figure says as little. :attr:`basis` is left
        to :meth:`_check_basis`, whose five words already leave out the
        empty one.

        :raises CatalogueError: naming the hedge and the field.
        """
        for hedge in (*self._number_hedges, *self._value_hedges):
            held = getattr(self, hedge)
            if hedge == "basis" or not held or not isinstance(held, Mapping):
                continue
            for key, value in held.items():
                texts = value if isinstance(value, tuple) else (value,)
                if any(isinstance(text, str) and not text.strip() for text in texts):
                    msg = (
                        f"{self.name!r}: {hedge} holds no text for {key!r}; a "
                        "hedge that says nothing reads as a cell with nothing "
                        "to explain"
                    )
                    raise CatalogueError(msg)

    def _check_bounds_have_ranges(self) -> None:
        """Refuse a bound on a field that has no range to bound.

        A bound is a range the page prints one end of, and the end is what
        :attr:`ranges` holds; a bound without it has no number at all.

        :raises CatalogueError: naming the bound and the field.
        """
        for hedge in ("bounded_above", "bounded_below"):
            for key in getattr(self, hedge):
                if key not in self.ranges:
                    msg = (
                        f"{self.name!r}: {hedge} names {key!r}, which has no "
                        "range; a bound is a range the page prints one end of"
                    )
                    raise CatalogueError(msg)

    def _check_reported(self) -> None:
        """Refuse an empty list of readings, or a reading interval backwards.

        A list with nothing in it is not several values: :meth:`why_missing`
        would say the page lists nothing, and a ``converted`` or ``carried``
        cell would count it as something to describe. An interval among the
        readings is an interval like any other, and one stored high to low
        reads back as a reading nobody printed.

        :raises CatalogueError: naming the field, and the interval.
        """
        for field_name, entries in self.reported.items():
            if not entries:
                msg = (
                    f"{self.name!r}: reported lists nothing for {field_name!r}; "
                    "a list of readings holds at least one"
                )
                raise CatalogueError(msg)
            for entry in entries:
                if isinstance(entry, tuple) and entry[0] > entry[1]:
                    msg = (
                        f"{self.name!r}: a reading of {field_name!r} runs from "
                        f"{entry[0]!r} down to {entry[1]!r}; the low end comes "
                        "first"
                    )
                    raise CatalogueError(msg)

    def _check_uncertainty(self) -> None:
        """Refuse a plus-or-minus below zero.

        :raises CatalogueError: naming the field and the value.
        """
        for key, spread in self.uncertainty.items():
            if spread < 0:
                msg = (
                    f"{self.name!r}: the uncertainty of {key!r} is {spread!r}, "
                    "and a plus-or-minus is never below zero"
                )
                raise CatalogueError(msg)

    def _check_cells_that_hold_nothing(self, shape: _Shape) -> None:
        """Refuse a value beside a hedge that says there is none to serve.

        A value is served before any hedge is read, so a number beside
        ``misprinted`` would go on being handed out while the row calls it
        wrong, and one beside a word or a list would contradict the cell the
        page printed.

        :raises CatalogueError: naming the field, its value and the hedge.
        """
        hedged = [
            (hedge, key) for hedge in _HOLDS_NOTHING for key in getattr(self, hedge)
        ]
        hedged += [
            ("misprinted", key) for key in self.misprinted if key in shape.numeric
        ]
        for hedge, key in hedged:
            value = getattr(self, key)
            if value is not None:
                msg = (
                    f"{self.name!r}: {key} holds {_quote(value)}, and {hedge} "
                    "says the page has no value to serve there"
                )
                raise CatalogueError(msg)

    def _check_cells_that_hold_something(self, shape: _Shape) -> None:
        """Refuse a conversion or a carried cell with nothing behind it.

        ``converted`` says what the page printed for the value the row
        holds, and ``carried`` which row the page gives it from; with no
        value, range or list beside them there is nothing they describe.

        :raises CatalogueError: naming the hedge and the field.
        """
        for hedge in ("converted", "carried"):
            for key in getattr(self, hedge):
                value = getattr(self, key)
                if key in shape.texts:
                    held = bool(value)
                else:
                    held = (
                        value is not None or key in self.ranges or key in self.reported
                    )
                if not held:
                    msg = (
                        f"{self.name!r}: {hedge} names {key!r}, which holds "
                        "nothing: no value, no range and no list"
                    )
                    raise CatalogueError(msg)

    def _readings(self, field_name: str) -> Iterator[tuple[str, float]]:
        """Every number the row holds for one field, with what it is."""
        value = getattr(self, field_name)
        if value is not None:
            yield field_name, value
        for end in self.ranges.get(field_name, ()):
            if end is not None:
                yield f"an end of the range of {field_name}", end
        for entry in self.reported.get(field_name, ()):
            for number in entry if isinstance(entry, tuple) else (entry,):
                yield f"a reading of {field_name}", number

    def _check_limits(self, shape: _Shape) -> None:
        """Refuse a number outside what its quantity can physically be.

        :raises CatalogueError: naming the field, the number and the limit.
        """
        for field_name, low, high, why in shape.limits:
            for what, number in self._readings(field_name):
                if number < low or (high is not None and number > high):
                    msg = f"{self.name!r}: {what} is {number!r}, and {why}"
                    raise CatalogueError(msg)

    def _check_basis(self) -> None:
        """Refuse a basis outside :data:`CATALOGUE_BASES`.

        The catalogue page and every reader of :meth:`basis_of` act on these
        five words only, so any other one would reach them as a claim nobody
        can read, and a misspelt ``"estimate"`` would publish an estimate as
        a printed number.

        :raises CatalogueError: naming the field and the word.
        """
        for field_name, basis in self.basis.items():
            if basis not in CATALOGUE_BASES:
                msg = (
                    f"{self.name!r}: the basis of {field_name!r} is {basis!r}, "
                    f"which is not one of {', '.join(CATALOGUE_BASES)}"
                )
                raise CatalogueError(msg)

    def _check_range_ends(self) -> None:
        """Refuse a range missing the end the page printed.

        The open side of a bound may be empty, because a quantity with no
        ceiling has nothing to put there. The printed side never may: a bound
        whose own number is missing would read back as a cell the page left
        blank, which is the one thing this class exists to tell apart.

        Nor may the ends run backwards: a range printed low to high and
        stored high to low reads back as an interval nobody printed.

        :raises CatalogueError: when a bound has no printed end, when a
            two-sided interval is missing either of them, or when its low end
            is above its high one.
        """
        for field_name, (low, high) in self.ranges.items():
            if field_name in self.bounded_above:
                missing = high is None
            elif field_name in self.bounded_below:
                missing = low is None
            else:
                missing = low is None or high is None
            if missing:
                msg = (
                    f"{self.name!r}: the range of {field_name!r} is missing an end "
                    "the page prints; only the open side of a bound may be empty"
                )
                raise CatalogueError(msg)
            if low is not None and high is not None and low > high:
                msg = (
                    f"{self.name!r}: the range of {field_name!r} runs from "
                    f"{low!r} down to {high!r}; the low end comes first"
                )
                raise CatalogueError(msg)

    def is_approximate(self, field_name: str) -> bool:
        """Whether the page prints this field with a ``~``.

        :param field_name: One of the numeric field names of this class.
        :return: ``True`` when the page rounded the cell on purpose.
        """
        return field_name in self.approximate

    def is_derived(self, field_name: str) -> bool:
        """Whether this library computed this field instead of reading it.

        :param field_name: One of the numeric field names of this class.
        :return: ``True`` when the page did not print it and the value follows
            from cells that it did. :attr:`derived` says how. A value the
            page prints in another unit, or gives by reference to another of
            its rows, answers ``False``: the number is the page's, and
            :attr:`converted` or :attr:`carried` says so.
        """
        return field_name in self.derived

    def basis_of(self, field_name: str) -> str:
        """What the source says this field is, one of :data:`CATALOGUE_BASES`.

        The five are ``measured``, ``declared``, ``calculated``, ``estimated``
        and ``extended``.

        :param field_name: One of the field names of this class.
        :return: The field's own entry in :attr:`basis`, else the row's, else
            the empty string, which means the source does not say.
        """
        return self.basis.get(field_name, self.basis.get("row", ""))

    def printed(self, field_name: str, *, wanted_by: str = "the caller") -> float:
        """One quantity this page prints, or a refusal that says what it had.

        Every quantity of a row is optional, because the pages print different
        columns, so a caller passing one into a function that requires a float
        has to narrow it. Doing it here beats an assertion at each call site:
        the refusal names the field, who wanted it and what the page had in
        that cell, which is the difference between a cell the book left empty
        and a cell holding the word "model".

        :param field_name: The quantity wanted.
        :param wanted_by: What wants it, named in the message.
        :return: The value, as a float.
        :raises ValueError: when the page did not print a number there.
        """
        value = getattr(self, field_name)
        if value is None:
            msg = (
                f"{self.name!r} has no {field_name}, which {wanted_by!r} needs: "
                f"{self.why_missing(field_name)} ({self.source})."
            )
            raise ValueError(msg)
        return float(value)

    def why_missing(self, field_name: str) -> str:
        """Why this field is ``None``, in the page's own terms.

        A catalogue that answers ``None`` and stops is asking the caller to
        guess whether the material has no such property, whether the book
        measured it and printed a dash, or whether the cell holds something
        that is not a number. Each of those is a different answer.

        :param field_name: One of the numeric field names of this class.
        :return: What the page had in that cell, or the empty string when the
            field is not missing at all. A field the page has no column for
            and this library cannot derive, because the cells it would need
            are themselves a range, answers that it does not follow.
        :raises AttributeError: for a name this class does not have, because a
            misspelt field would otherwise answer as if the cell were empty.
        """
        if getattr(self, field_name) is not None:
            return ""
        if field_name in self.misprinted:
            return self.misprinted[field_name]
        if field_name in self.unquantified:
            return (
                f"the page prints “{self.unquantified[field_name]}” "
                f"where the number would be"
            )
        if field_name in self.not_derivable:
            return self.not_derivable[field_name]
        if field_name in self.ranges:
            low, high = self.ranges[field_name]
            if high is not None and field_name in self.bounded_above:
                return f"the page prints an upper bound of {high:g} and no value"
            if low is not None and field_name in self.bounded_below:
                return f"the page prints a lower bound of {low:g} and no value"
            if low is not None and high is not None:
                return f"the page prints {low:g} to {high:g} and no value"
        if field_name in self.reported:
            listed = ", ".join(_spell(entry) for entry in self.reported[field_name])
            return f"the page lists {listed} and no single value"
        return "the page does not give it, and it does not follow from the cells that it does"


@dataclass(frozen=True, kw_only=True)
class BandedRow(CatalogueRow):
    """One row of a table that prints its quantity once per frequency band.

    The catalogues of this library that hold a spectrum read off a page keep
    one field per band rather than an array, because every hedge
    of :class:`CatalogueRow` is keyed by field name and a cell the page left
    empty has to say so the way any other cell does. What they then need is
    the same three things: which bands this row filled, the row as a spectrum,
    and a lookup that refuses rather than answering zero for a band the page
    did not print. That is what this holds.

    A subclass declares the bands its tables can print and how its band fields
    are spelled, and defines the reading method under the name its own domain
    uses, because ``row.transmission_loss_db(500)`` reads better than a generic
    verb and says what comes back.
    """

    #: The band centre frequencies a table of this quantity can print, in
    #: hertz. A table prints a subset.
    _bands_hz: ClassVar[tuple[int, ...]] = ()
    #: The band field for a centre frequency is this, the frequency, and
    #: :attr:`_band_suffix`: ``"absorption_coefficient_"`` and ``""`` give
    #: ``absorption_coefficient_500``.
    _band_prefix: ClassVar[str] = ""
    _band_suffix: ClassVar[str] = ""
    #: What these tables call their bands, for the wording of a refusal.
    _band_kind: ClassVar[str] = "octave"
    #: What the tables are of, for the wording of a refusal.
    _table_kind: ClassVar[str] = "published"

    @classmethod
    def _band_field(cls, band_hz: int) -> str:
        """The field name that holds one band of this row."""
        return f"{cls._band_prefix}{band_hz}{cls._band_suffix}"

    def bands(self) -> tuple[int, ...]:
        """The bands this row prints a value for, in hertz."""
        return tuple(
            band
            for band in self._bands_hz
            if getattr(self, self._band_field(band)) is not None
        )

    def spectrum(self) -> dict[int, float]:
        """The row as ``{band_hz: value}`` over the bands it prints.

        A band the page left empty, or printed as something other than a
        number, is left out rather than filled with a zero;
        :meth:`~CatalogueRow.why_missing` on that band's field says which it
        was.
        """
        return {
            band: float(getattr(self, self._band_field(band))) for band in self.bands()
        }

    def _in_band(self, band_hz: int) -> float:
        """One band of this row, or a refusal that says what the page had.

        :param band_hz: A centre frequency from the bands this class declares.
        :return: The printed value, as a float.
        :raises ValueError: when the page has no number in that band, naming
            the row, the band and what the cell held instead; or when
            *band_hz* is not a band these tables print.
        """
        if band_hz not in self._bands_hz:
            msg = (
                f"{band_hz} Hz is not {self._band_kind} band a "
                f"{self._table_kind} table prints; the bands are {self._bands_hz}"
            )
            raise ValueError(msg)
        return self.printed(
            self._band_field(band_hz), wanted_by=f"the {band_hz} Hz band"
        )
