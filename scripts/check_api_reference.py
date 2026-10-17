#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Coverage gate for the curated API quick table (``docs/reference/api/index.md``).

The hand-written table in ``docs/reference/api/index.md`` is the quick reference for
the GitHub/PyPI audience; the authoritative, generated reference lives on the
site (``make api-docs``). Being curated, the table can silently miss a newly
exported name. This gate closes that gap: it parses every backticked name in
the first column of the file's tables and fails when a public name has no row.
Public means what the library publishes since 4.0: the union of the domain
packages' ``__all__`` plus the four names the top level holds itself. Reading
``phonometry.__all__`` instead would see the twenty-four names the top level
publishes and call the other thirteen hundred private.

Rows for things ``__all__`` does not export are expected: methods
(``OctaveFilterBank.spectrogram``), namespace subpackages
(``phonometry.metrology``) and convention entries (``.plot()``). A row for a
plain name, one a reader would write after ``import``, is another matter: when
nothing publishes that name the row teaches an import that fails, which is
what a withdrawn name leaves behind if its row stays. :func:`stale_rows`
reports those; a ``convention`` row is exempt by its kind.

Two things a row *says* are checked, because both go stale in silence and
both send a reader the wrong way.

The **kind column** says what each name is, and a row calling a mapping a
``function`` tells the reader to call it. Twenty-one rows did: eight
dictionaries and a tuple and an array were ``function``, seven result
dataclasses were ``function`` too, and two functions were ``dataclass``. The
vocabulary is deliberately wider than Python's: ``constant`` is a better word
for a module-level float than ``float``, ``mapping`` than ``dict``, and a row
may name the concrete type (``Fluid``, ``Material``). So the check is not
equality: :func:`acceptable_kinds` works out every word that is true of the
object, and the row passes when it uses one of them. A cell naming two
(``dataclass`` / ``constant``, for a class and an instance of it sharing a
row) passes when either is true.

The **surface** behind the table is checked too, because a name with two
addresses, or one no reader can import, is a defect the table cannot show.
Every name has one public address: the domain package that publishes it, and
the module under it that defines it. :func:`surface_problems` walks every
public module and fails on five things:

* a module's ``__all__`` lists a name its domain package does not publish
  (an underscore name, or a constant the domain never took up), which is a
  public path to something private;
* a module re-exports, in its ``__all__``, a name it imports from another
  public module, which is a second address for the same object (a name a
  private module defines is published through the module that owns it,
  which is how private code gets its one public address);
* an ``__all__`` lists a type alias (``Literal[...]``, a union, ``type X``).
  No alias is public: publishing one later costs nothing, withdrawing one
  would break a release, and the reference prints each alias as its
  definition wherever a signature uses it;
* a domain publishes a function or a class under a name that is not its own
  (``partial_exposure = daily_exposure``), which is a second name for one
  object;
* two modules of one domain list the same name, which is two addresses for
  it whoever defines it: a name a private module defines and two public
  modules both import (``leak_ratio``, shared by ISO 11546 and ISO 11957) is
  published by one of them.

The **version row** shows the package version as a literal
(``phonometry.__version__  # '3.3.0'``). Nothing else re-reads that literal
after a release bump, so it is checked against the installed
``phonometry.__version__``. A page showing no literal fails too, so the check
cannot pass by finding nothing.

Usage::

    python scripts/check_api_reference.py

Exit status 0 when every public name has a row that says what it is, every
plain-name row names something public, every public name has one address and
none is an alias, and the page shows the current version; 1 otherwise.
"""

from __future__ import annotations

import ast
import dataclasses
import enum
import importlib
import importlib.util
import inspect
import pathlib
import pkgutil
import re
import sys
from collections.abc import Collection, Mapping
from typing import TYPE_CHECKING, TypeAliasType, get_origin

from api_taxonomy import public_names

if TYPE_CHECKING:
    from types import ModuleType

#: A backticked name inside a table cell, e.g. ```leq``` or ```.plot()```.
_BACKTICKED = re.compile(r"`([^`]+)`")

#: The version literal in the ``__version__`` row's usage cell, e.g.
#: ``phonometry.__version__  # '3.3.0'``.
_VERSION_LITERAL = re.compile(r"phonometry\.__version__\s*#\s*['\"]([^'\"]*)['\"]")


def table_names(markdown: str) -> set[str]:
    """Backticked names found in the first column of ``markdown`` tables.

    A cell may document several names at once (``| `a` / `b` | ...``); every
    backticked token in the first cell counts.

    :param markdown: Markdown source containing zero or more pipe tables.
    :return: The set of names, backticks stripped (e.g. ``{"leq", ".plot()"}``).
    """
    names: set[str] = set()
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        # Split on unescaped pipes only (``\|`` is a literal pipe in a cell).
        first_cell = re.split(r"(?<!\\)\|", stripped)[1]
        names.update(_BACKTICKED.findall(first_cell))
    return names


def missing_names(markdown: str, public: list[str]) -> list[str]:
    """Public names without a table row, in ``__all__`` order.

    :param markdown: The ``docs/reference/api/index.md`` source.
    :param public: Every public name (see :func:`api_taxonomy.public_names`).
    """
    documented = table_names(markdown)
    return [name for name in public if name not in documented]


#: Words the table uses for a value rather than for something to call. Any
#: of them is true of any module-level constant, so they are accepted together
#: and the concrete type name is added alongside.
_VALUE_WORDS = frozenset({"constant", "value"})

#: Words that are true of any callable the table lists.
_CALLABLE_WORDS = frozenset({"function", "method", "classmethod"})


def acceptable_kinds(obj: object) -> frozenset[str]:
    """Every word in the table's vocabulary that is true of *obj*.

    A row passes on any one of them, so this is deliberately generous about
    wording and strict about the distinction that matters: something a reader
    calls, versus something a reader reads.

    :param obj: The object the row's name resolves to.
    :return: The acceptable spellings of its kind, lowercased.
    """
    words: set[str] = set()
    if isinstance(obj, type):
        words.add("class")
        if issubclass(obj, Warning):
            words |= {"warning class", "warning"}
        if issubclass(obj, BaseException):
            words |= {"exception", "error"}
        if issubclass(obj, enum.Enum):
            words.add("enum")
        if dataclasses.is_dataclass(obj):
            words.add("dataclass")
        return frozenset(word.lower() for word in words)
    if inspect.isroutine(obj) or isinstance(obj, (staticmethod, classmethod)):
        return frozenset(_CALLABLE_WORDS)
    # Everything else is a value the reader reads: a constant, a table, a
    # prepared instance. The concrete type name is already in, so a row may
    # also say "dict", "tuple", "ndarray", "Fluid" or "Material".
    words |= _VALUE_WORDS
    words.add(type(obj).__name__)
    if isinstance(obj, Mapping):
        words |= {"dict", "mapping", "table"}
    if isinstance(obj, tuple):
        words.add("tuple")
    if hasattr(obj, "dtype") and hasattr(obj, "shape"):
        words.add("array")
    if dataclasses.is_dataclass(obj):
        words.add("dataclass")
    if isinstance(obj, enum.Enum):
        words.add("enum")
    return frozenset(word.lower() for word in words)


def _row_kinds(markdown: str) -> list[tuple[str, frozenset[str]]]:
    """``(name, declared kinds)`` for every table row, in reading order.

    A first cell may hold several names and a second cell several words; the
    row is read as every name being any of the words, which is how the shared
    rows are written.
    """
    rows: list[tuple[str, frozenset[str]]] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = re.split(r"(?<!\\)\|", stripped)
        if len(cells) < 3:
            continue
        declared = frozenset(
            word.strip().lower() for word in _BACKTICKED.findall(cells[2])
        )
        if not declared:
            continue
        rows.extend((name, declared) for name in _BACKTICKED.findall(cells[1]))
    return rows


#: A first-cell name a reader would write after ``import``. Methods
#: (``Result.plot``), subpackages (``phonometry.io``) and conventions
#: (``.plot()``) do not match.
_PLAIN_NAME = re.compile(r"[A-Za-z_]\w*")


def stale_rows(markdown: str, public: Collection[str]) -> list[str]:
    """Plain names with a row that nothing publishes, in reading order.

    A withdrawn name whose row stays teaches an import that fails, and
    :func:`missing_names` cannot see it: it asks whether every public name has
    a row, never whether every row names something public. A row whose kind is
    ``convention`` documents a habit of the library rather than an object, so
    it is left alone.

    :param markdown: The ``docs/reference/api/index.md`` source.
    :param public: Every public name (see :func:`api_taxonomy.public_names`).
    :return: One message per stale name.
    """
    problems: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = re.split(r"(?<!\\)\|", stripped)
        if len(cells) < 3:
            continue
        kinds = {word.strip().lower() for word in _BACKTICKED.findall(cells[2])}
        if "convention" in kinds:
            continue
        problems.extend(
            f"{name}: has a row, and nothing publishes it"
            for name in _BACKTICKED.findall(cells[1])
            if _PLAIN_NAME.fullmatch(name) and name not in public
        )
    return problems


def kind_problems(markdown: str, owners: dict[str, ModuleType]) -> list[str]:
    """Rows whose kind column is not true of the object they name.

    :param markdown: The ``docs/reference/api/index.md`` source.
    :param owners: Public name to the package that publishes it.
    :return: One message per wrong row, in reading order.
    """
    problems: list[str] = []
    for name, declared in _row_kinds(markdown):
        package = owners.get(name)
        if package is None:
            continue  # A method, a subpackage or a convention entry.
        obj = getattr(package, name, None)
        if obj is None:  # pragma: no cover - __all__ and the module agree.
            continue
        allowed = acceptable_kinds(obj)
        if not declared & allowed:
            said = " / ".join(sorted(declared))
            problems.append(f"{name}: says {said}, is {'/'.join(sorted(allowed))}")
    return problems


def is_type_alias(obj: object) -> bool:
    """Whether *obj* is a typing alias: ``Literal[...]``, a union, ``type X``.

    :param obj: The object a published name resolves to.
    """
    return get_origin(obj) is not None or isinstance(obj, TypeAliasType)


def _is_type_checking_block(statement: ast.stmt) -> bool:
    test = statement.test if isinstance(statement, ast.If) else None
    return (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
        isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
    )


def imported_from(module: ModuleType) -> dict[str, str]:
    """Each name ``module`` binds with ``from X import name``, mapped to ``X``.

    Only the imports that bind at run time count: an ``if TYPE_CHECKING:``
    block binds nothing a caller can import. Relative imports are resolved, so
    the value is always an absolute module name.

    :param module: An imported module whose source is available.
    :return: Bound name to the absolute name of the module it comes from.
    """
    try:
        tree = ast.parse(inspect.getsource(module))
    except (OSError, TypeError):
        return {}
    package = module.__package__ or module.__name__
    found: dict[str, str] = {}
    statements = list(tree.body)
    while statements:
        statement = statements.pop(0)
        if isinstance(statement, (ast.If, ast.Try)):
            if not _is_type_checking_block(statement):
                nested = [*statement.body, *statement.orelse]
                if isinstance(statement, ast.Try):
                    nested += [s for h in statement.handlers for s in h.body]
                statements[:0] = nested
        elif isinstance(statement, ast.ImportFrom):
            source = importlib.util.resolve_name(
                "." * statement.level + (statement.module or ""), package
            )
            for alias in statement.names:
                found[alias.asname or alias.name] = source
    return found


def _is_public_path(name: str) -> bool:
    return not any(part.startswith("_") for part in name.split("."))


def surface_problems(domains: list[ModuleType]) -> list[str]:
    """Every name a public module lists that gives it a second or a private address.

    :param domains: The domain packages the top level publishes.
    :return: One message per offending ``(module, name)``, in walking order.
    """
    problems: list[str] = []
    for domain in domains:
        for name in domain.__all__:
            obj = getattr(domain, name, None)
            where = f"{domain.__name__}.__all__ lists {name!r}"
            if is_type_alias(obj):
                problems.append(f"{where}, a type alias")
            elif (inspect.isroutine(obj) or inspect.isclass(obj)) and getattr(
                obj, "__name__", name
            ) != name:
                problems.append(f"{where}, a second name for {obj.__name__}")
        # The leaf module that listed each name first. A subpackage's
        # ``__init__`` gathers its leaves' names on purpose and is not one.
        listed_by: dict[str, str] = {}
        for info in pkgutil.walk_packages(domain.__path__, domain.__name__ + "."):
            if not _is_public_path(info.name):
                continue
            module = importlib.import_module(info.name)
            listed = getattr(module, "__all__", None)
            if listed is None:
                continue
            sources = {} if info.ispkg else imported_from(module)
            for name in listed:
                problem = _listing_problem(
                    module,
                    name,
                    domain,
                    sources,
                    None if info.ispkg else listed_by,
                )
                if problem:
                    problems.append(f"{info.name}.__all__ lists {name!r}, {problem}")
                elif not info.ispkg:
                    listed_by[name] = info.name
    return problems


def _listing_problem(
    module: ModuleType,
    name: str,
    domain: ModuleType,
    sources: Mapping[str, str],
    listed_by: Mapping[str, str] | None,
) -> str:
    """What is wrong with ``module`` listing ``name`` in its ``__all__``.

    :param module: A public module under ``domain``.
    :param name: One name of its ``__all__``.
    :param domain: The domain package ``module`` belongs to.
    :param sources: What :func:`imported_from` read from ``module``.
    :param listed_by: The leaf that listed each name first, or ``None`` for a
        subpackage, whose ``__init__`` gathers its leaves' names on purpose.
    :return: The problem in a few words, or ``""`` when there is none.
    """
    if is_type_alias(getattr(module, name, None)):
        return "a type alias"
    if name not in domain.__all__:
        return f"which {domain.__name__} does not publish"
    if _is_public_path(sources.get(name, "_")):
        return f"a second address for {sources[name]}.{name}"
    if listed_by is not None and name in listed_by:
        return f"which {listed_by[name]} lists too"
    return ""


def version_problems(markdown: str, version: str) -> list[str]:
    """Everything wrong with the version literals in ``markdown``.

    The ``__version__`` row spells the package version out as a literal, and
    a release bump has no reason to touch this file, so the literal goes
    stale silently. Showing none at all is the other half of the same
    defect: a check that finds nothing would pass while reporting a version
    the page does not actually show.

    :param markdown: The ``docs/reference/api/index.md`` source.
    :param version: ``phonometry.__version__``.
    :return: One message per problem, in order of appearance. Empty when the
        page shows the version and every literal agrees with it.
    """
    found = _VERSION_LITERAL.findall(markdown)
    if not found:
        return ["no `phonometry.__version__  # '...'` example to check"]
    return [f"shows {literal!r}" for literal in found if literal != version]


def main() -> int:
    """Run the gate against the working tree. Returns the exit status."""
    import phonometry

    public = sorted(public_names())
    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs"
        / "reference"
        / "api"
        / "index.md"
    )
    markdown = path.read_text(encoding="utf-8")
    missing = missing_names(markdown, public)
    if missing:
        print(f"docs/reference/api/index.md is missing {len(missing)} public name(s):")
        for name in missing:
            print(f"  - {name}")
        print("Add a table row for each name (see the file's existing style).")
        return 1
    stale = stale_rows(markdown, public)
    if stale:
        print(
            f"docs/reference/api/index.md has {len(stale)} row(s) for a name "
            "nothing publishes; a reader would import it and fail:"
        )
        for problem in stale:
            print(f"  - {problem}")
        print("Delete the row, or publish the name.")
        return 1
    wrong = kind_problems(markdown, public_names())
    if wrong:
        print(
            f"docs/reference/api/index.md misdescribes {len(wrong)} name(s); "
            "the kind column is what a reader acts on:"
        )
        for problem in wrong:
            print(f"  - {problem}")
        return 1
    domains = [
        getattr(phonometry, name)
        for name in phonometry.__all__
        if inspect.ismodule(getattr(phonometry, name))
    ]
    surface = surface_problems(domains)
    if surface:
        print(
            f"{len(surface)} public name(s) have a second or a private address; "
            "a leaf module lists what it defines and its domain publishes, and "
            "no type alias is public:"
        )
        for problem in surface:
            print(f"  - {problem}")
        return 1
    problems = version_problems(markdown, phonometry.__version__)
    if problems:
        print(
            "docs/reference/api/index.md does not show the current version "
            f"(phonometry.__version__ is {phonometry.__version__!r}):"
        )
        for problem in problems:
            print(f"  - {problem}")
        print("Update the __version__ row's example to the current version.")
        return 1
    print(
        f"docs/reference/api/index.md covers all {len(public)} public names, "
        f"says what each of them is, and shows version {phonometry.__version__}; "
        "every public name has one address and none is a type alias."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
