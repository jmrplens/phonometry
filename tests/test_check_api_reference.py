#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The kind column of the curated API table, and what it is allowed to say.

``docs/reference/api/index.md`` is the quick reference the GitHub and PyPI
audience reads, and its second column says what each name is. A row calling a
mapping a ``function`` tells the reader to call it; twenty-one rows did, eight
dictionaries and a tuple and an array among them. The gate closes that, and
these tests fix where the line falls.

The vocabulary is deliberately wider than Python's -- ``constant`` is a better
word for a module-level float than ``float``, ``mapping`` than ``dict``, and a
row may name the concrete type -- so the check is not equality. It asks whether
the row uses any word that is true of the object.
"""

from __future__ import annotations

import dataclasses
import enum
import pathlib
import sys
import types

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_api_reference as gate


class _Colour(enum.StrEnum):
    RED = "red"


@dataclasses.dataclass(frozen=True)
class _Result:
    value: float = 1.0


class _Plain:
    pass


class _Shouted(Warning):
    pass


def _fn() -> None:
    """A function."""


def test_a_callable_is_only_ever_a_callable() -> None:
    """The distinction the gate exists for: called, versus read."""
    words = gate.acceptable_kinds(_fn)
    assert "function" in words
    for value in ("constant", "dataclass", "mapping", "tuple", "class"):
        assert value not in words


def test_a_value_is_never_a_function() -> None:
    """The eight rows that sent a reader to call a table of coefficients."""
    for value in ({"a": 1.0}, (63.0, 125.0), 3.14, "s"):
        assert "function" not in gate.acceptable_kinds(value)


def test_a_mapping_may_be_called_a_mapping_a_dict_or_a_constant() -> None:
    """Wording is the table's to choose; only the meaning is checked."""
    words = gate.acceptable_kinds({"steel": 7800.0})
    assert {"mapping", "dict", "table", "constant"} <= words


def test_a_read_only_mapping_is_still_a_mapping() -> None:
    """``MappingProxyType`` is what a published table is usually wrapped in."""
    assert "mapping" in gate.acceptable_kinds(types.MappingProxyType({"a": 1}))


def test_a_dataclass_class_and_an_instance_of_it_differ() -> None:
    """One row often carries both, which is why a cell may name two kinds."""
    assert "dataclass" in gate.acceptable_kinds(_Result)
    assert "class" in gate.acceptable_kinds(_Result)
    instance = gate.acceptable_kinds(_Result())
    assert {"dataclass", "constant"} <= instance
    assert "class" not in instance


def test_a_warning_class_answers_to_both_of_its_names() -> None:
    assert {"warning class", "warning", "class"} <= gate.acceptable_kinds(_Shouted)


def test_an_enum_is_an_enum_and_a_class() -> None:
    assert {"enum", "class"} <= gate.acceptable_kinds(_Colour)


def test_a_plain_class_is_not_a_dataclass() -> None:
    words = gate.acceptable_kinds(_Plain)
    assert "class" in words
    assert "dataclass" not in words


def test_a_row_passes_on_any_word_that_is_true() -> None:
    """A shared row names every kind it holds, and each name takes its own."""
    markdown = (
        "| Name | Kind | What |\n"
        "| :--- | :--- | :--- |\n"
        "| `thing` / `TABLE` | `function` / `mapping` | prose |\n"
    )
    owners = {"thing": _Owner(thing=_fn), "TABLE": _Owner(TABLE={"a": 1.0})}
    assert gate.kind_problems(markdown, owners) == []


def test_a_row_that_calls_a_table_a_function_is_reported() -> None:
    markdown = (
        "| Name | Kind | What |\n"
        "| :--- | :--- | :--- |\n"
        "| `TABLE` | `function` | prose |\n"
    )
    (problem,) = gate.kind_problems(markdown, {"TABLE": _Owner(TABLE={"a": 1.0})})
    assert problem.startswith("TABLE: says function")


def test_a_row_for_something_the_library_does_not_publish_is_left_alone() -> None:
    """Methods, subpackages and convention entries have rows and no object."""
    markdown = (
        "| Name | Kind | What |\n"
        "| :--- | :--- | :--- |\n"
        "| `.plot()` | `convention` | prose |\n"
    )
    assert gate.kind_problems(markdown, {}) == []


class _Owner(types.SimpleNamespace):
    """A stand-in for the package a name is published by."""


# ---------------------------------------------------------------------------
# One address per public name
# ---------------------------------------------------------------------------
_FAKE_DOMAIN = {
    "__init__.py": (
        "from ._private import Hidden\n"
        "from .leaf import Owned, Typed, owned, second\n"
        "from .other import Shared\n"
        "__all__ = ['Hidden', 'Owned', 'Shared', 'Typed', 'owned', 'second', 'Mode']\n"
        "from .leaf import Mode\n"
    ),
    "leaf.py": (
        "from typing import TYPE_CHECKING, Literal\n"
        "from ._private import Hidden\n"
        "from .other import Shared\n"
        "if TYPE_CHECKING:\n"
        "    from .other import Typed\n"
        "Mode = Literal['a', 'b']\n"
        "class Owned:\n    pass\n"
        "class Typed:\n    pass\n"
        "def owned():\n    return 1\n"
        "second = owned\n"
        "_TABLE = (1, 2)\n"
        "__all__ = ['Hidden', 'Mode', 'Owned', 'Shared', 'Typed', '_TABLE', 'owned']\n"
    ),
    "other.py": "class Shared:\n    pass\n__all__ = ['Shared']\n",
    "twin.py": "from ._private import Hidden\n__all__ = ['Hidden']\n",
    "_private.py": "class Hidden:\n    pass\n",
}


def _fake_domain(tmp_path: pathlib.Path, name: str) -> types.ModuleType:
    package = tmp_path / name
    package.mkdir()
    for filename, source in _FAKE_DOMAIN.items():
        (package / filename).write_text(source, encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    try:
        import importlib

        return importlib.import_module(name)
    finally:
        sys.path.remove(str(tmp_path))


def test_every_second_or_private_address_is_reported(tmp_path: pathlib.Path) -> None:
    """Underscore names, re-exports, aliases, second names and second listings.

    What is not reported is as much the point. ``leaf`` lists ``Hidden``, which
    a private module defines and the domain publishes: that is how private code
    gets its one public address. ``leaf`` imports ``Typed`` from ``other`` only
    for the type checker, which binds nothing, so its ``Typed`` is its own.
    And ``other`` lists the ``Shared`` it defines although ``leaf`` listed it
    first: a listing already reported does not make the owner the second one.
    """
    domain = _fake_domain(tmp_path, "fake_surface_domain")
    problems = gate.surface_problems([domain])
    assert problems == [
        "fake_surface_domain.__all__ lists 'second', a second name for owned",
        "fake_surface_domain.__all__ lists 'Mode', a type alias",
        "fake_surface_domain.leaf.__all__ lists 'Mode', a type alias",
        "fake_surface_domain.leaf.__all__ lists 'Shared', a second address for "
        "fake_surface_domain.other.Shared",
        "fake_surface_domain.leaf.__all__ lists '_TABLE', which "
        "fake_surface_domain does not publish",
        "fake_surface_domain.twin.__all__ lists 'Hidden', which "
        "fake_surface_domain.leaf lists too",
    ]


def test_a_plain_name_row_must_name_something_public() -> None:
    """A withdrawn name whose row stayed teaches an import that fails."""
    markdown = (
        "| Name | Kind | What |\n"
        "| :--- | :--- | :--- |\n"
        "| `leq` | `function` | prose |\n"
        "| `Withdrawn` | `constant` | prose |\n"
        "| `Result.plot` / `phonometry.io` | `method` | prose |\n"
        "| `.plot()` | `convention` | prose |\n"
        "| `language` | `convention` | prose |\n"
    )
    assert gate.stale_rows(markdown, {"leq"}) == [
        "Withdrawn: has a row, and nothing publishes it"
    ]


def test_the_curated_table_has_no_row_for_a_withdrawn_name() -> None:
    from api_taxonomy import public_names

    markdown = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs"
        / "reference"
        / "api"
        / "index.md"
    ).read_text(encoding="utf-8")
    assert gate.stale_rows(markdown, public_names()) == []


def test_the_library_gives_every_public_name_one_address() -> None:
    import inspect

    import phonometry

    domains = [
        getattr(phonometry, name)
        for name in phonometry.__all__
        if inspect.ismodule(getattr(phonometry, name))
    ]
    assert gate.surface_problems(domains) == []
