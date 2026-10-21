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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

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


def _fake_domain(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> types.ModuleType:
    package = tmp_path / name
    package.mkdir()
    for filename, source in _FAKE_DOMAIN.items():
        (package / filename).write_text(source, encoding="utf-8")
    monkeypatch.syspath_prepend(tmp_path)
    import importlib

    return importlib.import_module(name)


def test_every_second_or_private_address_is_reported(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Underscore names, re-exports, aliases, second names and second listings.

    What is not reported is as much the point. ``leaf`` lists ``Hidden``, which
    a private module defines and the domain publishes: that is how private code
    gets its one public address. ``leaf`` imports ``Typed`` from ``other`` only
    for the type checker, which binds nothing, so its ``Typed`` is its own.
    And ``other`` lists the ``Shared`` it defines although ``leaf`` listed it
    first: a listing already reported does not make the owner the second one.
    """
    domain = _fake_domain(tmp_path, monkeypatch, "fake_surface_domain")
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


def test_a_published_type_variable_or_protocol_is_reported(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``TypeVar`` or a ``Protocol`` in an ``__all__`` is refused like an alias.

    Both only describe types, and the guard knew it for the names a module
    leaves unlisted; a listed one passed as long as it was not an alias.
    """
    package = tmp_path / "fake_typing_domain"
    package.mkdir()
    (package / "__init__.py").write_text(
        "from .leaf import Proto, T, made\n__all__ = ['Proto', 'T', 'made']\n",
        encoding="utf-8",
    )
    (package / "leaf.py").write_text(
        "from typing import Protocol, TypeVar\n"
        "T = TypeVar('T')\n"
        "class Proto(Protocol):\n    def size(self) -> int: ...\n"
        "def made():\n    return 1\n"
        "__all__ = ['Proto', 'T', 'made']\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(tmp_path)
    import importlib

    domain = importlib.import_module("fake_typing_domain")
    assert gate.surface_problems([domain]) == [
        "fake_typing_domain.__all__ lists 'Proto', a Protocol",
        "fake_typing_domain.__all__ lists 'T', a TypeVar",
        "fake_typing_domain.leaf.__all__ lists 'Proto', a Protocol",
        "fake_typing_domain.leaf.__all__ lists 'T', a TypeVar",
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


# ---------------------------------------------------------------------------
# A module is reached by its name, and says what it publishes
# ---------------------------------------------------------------------------
_FAKE_MODULES = {
    "__init__.py": (
        "from . import listed, nested\n"
        "from ._kept import kept\n"
        "from .probe import probe\n"
        "from .bare import bare\n"
        "from .listed import TABLE\n"
        "__all__ = ['TABLE', 'bare', 'kept', 'listed', 'nested', 'probe']\n"
    ),
    "probe.py": "def probe():\n    return 1\n__all__ = ['probe']\n",
    "bare.py": "def bare():\n    return 2\n",
    "listed.py": (
        "from math import pi\n"
        "from typing import Literal, Protocol, TypeVar\n"
        "Mode = Literal['a', 'b']\n"
        "T = TypeVar('T')\n"
        "class Shaped(Protocol):\n    size: int\n"
        "TABLE = (1, 2)\n"
        "LIMIT = 3.0\n"
        "_OWN = 4.0\n"
        "def helper():\n    return pi\n"
        "__all__ = ['helper']\n"
    ),
    "_kept.py": "def kept():\n    return 4\n",
    "nested/__init__.py": "from .version import version\n__all__ = ['version']\n",
    "nested/version.py": "version = '1.0'\n__all__ = ['version']\n",
}


def _fake_package(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    files: dict[str, str],
) -> types.ModuleType:
    package = tmp_path / name
    for filename, source in files.items():
        path = package / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    monkeypatch.syspath_prepend(tmp_path)
    import importlib

    return importlib.import_module(name)


def test_a_module_hidden_behind_a_name_of_its_package_is_reported(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A function, or a constant, that takes a module's name hides the module.

    ``probe`` publishes a function of its own name, so ``import pkg.probe as m``
    binds the function. ``bare`` does the same and lists nothing as well, so it
    is reported twice. ``nested.version`` is hidden behind a string: whatever
    takes the name hides the module, not only a function. ``listed`` is
    reached by its name, and its ``__all__`` leaves out two things: ``TABLE``,
    which its package publishes, and ``LIMIT``, which nobody does. What stays
    quiet is as much the point: ``listed``'s alias, ``TypeVar`` and
    ``Protocol`` (typing constructs, never published), its ``_OWN``, the ``pi``
    it imports, and ``_kept``, which takes the name of the function it
    defines, which is how such a module is written: private, with its names
    reached through the package.
    """
    domain = _fake_package(tmp_path, monkeypatch, "fake_module_domain", _FAKE_MODULES)
    problems = gate.module_problems([domain])
    hidden = (
        "fake_module_domain.{leaf} is hidden behind fake_module_domain.{leaf}, "
        "a function: `import fake_module_domain.{leaf}` binds the function, so "
        "the module is private (_{leaf}) and its names are reached through "
        "fake_module_domain"
    )
    assert problems == [
        hidden.format(leaf="bare"),
        "fake_module_domain.bare declares no __all__, so nothing says which of "
        "its names are public",
        "fake_module_domain.listed defines 'TABLE', which fake_module_domain "
        "publishes, and its __all__ does not list it",
        "fake_module_domain.listed defines 'LIMIT' and its __all__ does not list "
        "it; a name its package does not publish is private (_LIMIT)",
        "fake_module_domain.nested.version is hidden behind "
        "fake_module_domain.nested.version, a str: `import "
        "fake_module_domain.nested.version` binds the str, so the module is "
        "private (_version) and its names are reached through "
        "fake_module_domain.nested",
        hidden.format(leaf="probe"),
    ]


def test_a_package_without_all_is_reported_like_any_module(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The domain package is walked too: it is the first module a reader meets."""
    files = {
        "__init__.py": "from .leaf import thing\n",
        "leaf.py": "def thing():\n    return 1\n__all__ = ['thing']\n",
    }
    domain = _fake_package(tmp_path, monkeypatch, "fake_bare_domain", files)
    assert gate.module_problems([domain]) == [
        "fake_bare_domain declares no __all__, so nothing says which of its "
        "names are public"
    ]


_STRAY_LEAF = {
    "__init__.py": "from ._impl import probe\n__all__ = ['probe']\n",
    "_impl.py": "def probe():\n    return 1\n__all__ = ['probe']\n",
    "probe.py": "def other():\n    return 2\n__all__ = ['other']\n",
}


def test_a_leaf_its_package_never_imports_is_still_found_hidden(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The package attribute is read before the walk imports the leaf.

    ``probe.py`` sits beside the ``probe`` the package publishes from
    ``_impl`` and nothing imports it. Importing it for the first time would
    bind the package attribute to the module, so a check that read the
    attribute afterwards saw a module and passed; and the walk would leave the
    library publishing the module instead of the function.
    """
    domain = _fake_package(tmp_path, monkeypatch, "fake_stray_domain", _STRAY_LEAF)
    published = domain.probe
    problems = gate.module_problems([domain])
    assert problems == [
        "fake_stray_domain.probe is hidden behind fake_stray_domain.probe, a "
        "function: `import fake_stray_domain.probe` binds the function, so the "
        "module is private (_probe) and its names are reached through "
        "fake_stray_domain"
    ]
    assert domain.probe is published


def test_a_leaf_another_import_reached_first_is_found_in_the_package_source(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Once something has imported the leaf, only the ``__init__`` source shows it.

    The import already replaced the published function with the module, so
    every attribute the walk can read says module. The package's own
    statement that gave the name to something else is still there to read.
    """
    import importlib

    domain = _fake_package(tmp_path, monkeypatch, "fake_early_domain", _STRAY_LEAF)
    importlib.import_module("fake_early_domain.probe")
    problems = gate.module_problems([domain])
    assert problems == [
        "fake_early_domain.probe is hidden behind fake_early_domain.probe: the "
        "package binds 'probe' by `from ._impl import probe`, so the module is "
        "private (_probe) and its names are reached through fake_early_domain"
    ]


_BINDINGS = {
    "from . import probe": None,
    "from fake_pkg import probe": None,
    "import fake_pkg.probe": None,
    "import fake_pkg.probe as probe": None,
    "import other_pkg.probe as probe": "import other_pkg.probe as probe",
    "from .probe import probe": "from .probe import probe",
    "from ._impl import run as probe": "from ._impl import run as probe",
    "import json as probe": "import json as probe",
    "def probe():\n    pass": "def probe",
    "class probe:\n    pass": "class probe",
    "probe = 1": "probe = ...",
    "if True:\n    probe: int = 1": "probe = ...",
    "try:\n    pass\nexcept ImportError:\n    probe = None": "probe = ...",
    "def other():\n    probe = 1": None,
}


def test_only_importing_the_submodule_itself_leaves_its_name_alone() -> None:
    """Every other statement of an ``__init__`` that binds the name hides it."""
    import ast

    for statement, binding in _BINDINGS.items():
        found = [
            gate._binding_other_than_submodule(node, "fake_pkg", "probe")
            for node in gate._module_level_statements(ast.parse(statement).body)
        ]
        first = next((text for text in found if text is not None), None)
        assert first == binding, statement


_NESTED_BINDINGS = {
    "from ..fake_pkg import probe": None,
    "from ..fake_pkg import run as probe": "from ..fake_pkg import run as probe",
    "from .. import probe": "from .. import probe",
    "from ...beyond import probe": "from ...beyond import probe",
}


def test_a_relative_import_is_read_from_where_it_resolves() -> None:
    """``from ..pkg import leaf`` inside ``outer.pkg`` names the package itself.

    Comparing the written source with the package name missed it, so a correct
    ``__init__`` failed the gate. ``from .. import probe`` reaches ``outer``
    instead, and an import that climbs past the top-level package resolves to
    nothing, so both still hide the module.
    """
    import ast

    for statement, binding in _NESTED_BINDINGS.items():
        (node,) = ast.parse(statement).body
        found = gate._binding_other_than_submodule(node, "outer.fake_pkg", "probe")
        assert found == binding, statement


def test_the_library_reaches_every_public_module_by_its_name() -> None:
    import inspect

    import phonometry

    domains = [
        getattr(phonometry, name)
        for name in phonometry.__all__
        if inspect.ismodule(getattr(phonometry, name))
    ]
    assert gate.module_problems(domains) == []


def test_an_exemption_is_keyed_by_location_and_cannot_go_stale(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An entry quiets the one name it names, and reports itself once unused."""
    files = {
        "__init__.py": "from .leaf import thing\n__all__ = ['thing']\n",
        "leaf.py": "LIMIT = 3.0\ndef thing():\n    return LIMIT\n__all__ = ['thing']\n",
    }
    domain = _fake_package(tmp_path, monkeypatch, "fake_exempt_domain", files)
    monkeypatch.setattr(
        gate,
        "UNLISTED_EXEMPTIONS",
        {
            "fake_exempt_domain.leaf.LIMIT": "read by thing only",
            "fake_exempt_domain.leaf.GONE": "no longer defined",
        },
    )
    assert gate.module_problems([domain]) == [
        "UNLISTED_EXEMPTIONS names fake_exempt_domain.leaf.GONE, which is no "
        "longer defined unlisted; drop the entry"
    ]


def test_defined_names_reads_what_the_module_binds_itself() -> None:
    """Imports and ``TYPE_CHECKING`` blocks define nothing; branches that run do."""
    module = types.ModuleType("fake_defined")
    source = (
        "from math import pi\n"
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    ONLY_TYPED = 1\n"
        "try:\n"
        "    import numpy\n"
        "    FAST = True\n"
        "except ImportError:\n"
        "    FAST = False\n"
        "A, (B, C) = 1, (2, 3)\n"
        "D: int\n"
        "E: int = 5\n"
        "type Alias = int\n"
        "class K:\n    pass\n"
        "def f():\n    return pi\n"
    )
    import linecache

    filename = "<fake_defined>"
    module.__file__ = filename
    linecache.cache[filename] = (
        len(source),
        None,
        source.splitlines(keepends=True),
        filename,
    )
    exec(compile(source, filename, "exec"), module.__dict__)
    try:
        assert gate.defined_names(module) == [
            "FAST",
            "A",
            "B",
            "C",
            "E",
            "Alias",
            "K",
            "f",
        ]
    finally:
        linecache.cache.pop(filename, None)


# ---------------------------------------------------------------------------
# A usage example calls the function the way its signature allows
# ---------------------------------------------------------------------------
def _measured(
    velocities: object, drops: object, area: object, *, thickness_m: object = None
) -> None:
    """A function whose last parameter is keyword-only."""


class _Drawn:
    """A record whose method the table shows on the class."""

    def plot_geometry(self, *, frequency_index: int = 0) -> None:
        """Draw it."""

    @classmethod
    def from_rows(cls, rows: object) -> None:
        """Build it."""


_EXAMPLES = (
    "| Name | Kind | What | Example |\n"
    "| :--- | :--- | :--- | :--- |\n"
    "| `measured` | `function` | prose | `res = fake.measured(u, dp, 0.01, 0.05)` |\n"
    "| `measured` | `function` | prose | `fake.measured(u, dp, 0.01, thickness_m=0.05)` |\n"
    "| `measured` | `function` | prose | `fake.measured(u, ..., thickness_m=...)` |\n"
    "| `measured` | `function` | prose | `fake.measured(u, dp, area=1, depth=...)` |\n"
    "| `measured` | `function` | prose | `fake.measured(u, dp, thickness_m=0.05, ...)` |\n"
    "| `_Drawn.plot_geometry` | `method` | prose | `_Drawn.plot_geometry(frequency_index=2)` |\n"
    "| `_Drawn.plot_geometry` | `method` | prose | `_Drawn.plot_geometry(2)` |\n"
    "| `_Drawn.from_rows` | `classmethod` | prose | `_Drawn.from_rows(rows)` |\n"
    "| `withdrawn` | `function` | prose | `fake.withdrawn(1)` |\n"
    "| `res.plot` | `method` | prose | `res.plot(ax, 1, 2, 3)`, `np.zeros(3, 4, 5, 6)` |\n"
    "| `grouped` | `function` | prose | `fake.measured(2 600.0, 1, 2, thickness_m=1)` |\n"
)


def test_an_example_its_function_refuses_is_reported() -> None:
    """A keyword-only parameter passed by position is the row a reader copies and fails on.

    What stays quiet matters as much: a call through a variable or a third
    party (``res.plot``, ``np.zeros``) is not the library's to check, an
    elided argument list (``...``) is held only to what it does write, a
    method shown on its class takes its instance for granted, and the page's
    digit grouping is read as one number.
    """
    roots = {"fake": types.SimpleNamespace(measured=_measured), "_Drawn": _Drawn}
    assert gate.example_problems(_EXAMPLES, roots) == [
        "measured: `res = fake.measured(u, dp, 0.01, 0.05)` calls fake.measured, "
        "which refuses it: too many positional arguments",
        "measured: `fake.measured(u, dp, area=1, depth=...)` calls fake.measured, "
        "which refuses it: got an unexpected keyword argument 'depth'",
        "_Drawn.plot_geometry: `_Drawn.plot_geometry(2)` calls "
        "_Drawn.plot_geometry, which refuses it: too many positional arguments",
        "withdrawn: `fake.withdrawn(1)` calls fake.withdrawn, which does not "
        "exist: fake has no attribute 'withdrawn'",
    ]


def test_every_example_in_the_curated_table_binds_to_its_signature() -> None:
    markdown = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs"
        / "reference"
        / "api"
        / "index.md"
    ).read_text(encoding="utf-8")
    assert gate.example_problems(markdown, gate.usage_roots()) == []
