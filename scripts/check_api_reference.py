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

The **usage examples** are checked as well, because no snippet gate runs
this page and a signature moves under them: a parameter turned keyword-only
left ``static_airflow_resistance(..., 0.01, 0.05)`` raising ``TypeError`` for
the reader who copied it, and thirteen rows had gone the same way.
:func:`example_problems` binds every call that starts from something the
library publishes to that callable's signature, without running it.

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
* an ``__all__`` lists a type alias (``Literal[...]``, a union, ``type X``),
  a ``TypeVar`` or a ``Protocol``. None of them is public: publishing one later costs nothing, withdrawing one
  would break a release, and the reference prints each alias as its
  definition wherever a signature uses it;
* a domain publishes a function or a class under a name that is not its own
  (``partial_exposure = daily_exposure``), which is a second name for one
  object;
* two modules of one domain list the same name, which is two addresses for
  it whoever defines it: a name a private module defines and two public
  modules both import (``leak_ratio``, shared by ISO 11546 and ISO 11957) is
  published by one of them.

The **modules** themselves are held to two more rules by
:func:`module_problems`, because a module is an address too:

* no public module shares its name with something else its package holds.
  ``phonometry.signals`` publishes the function ``correlation``, so a module
  ``signals/correlation.py`` is hidden behind it: ``import
  phonometry.signals.correlation as m`` binds the function, and
  ``signals.correlation.time_delay`` raises ``AttributeError`` although the
  reference has a page under that address. Such a module is private
  (``_correlation.py``) and its names are reached through the package;
* every public module declares ``__all__``, and the list is the whole truth.
  A module without one says nothing about which of its names are public, so a
  constant it defines for its own use looks as public as its functions, and
  none of the rules above can see it. A module with one lists every name it
  defines that its package publishes, and every other public-looking name it
  defines is either a typing construct (a type alias, a ``TypeVar``, a
  ``Protocol``, none of them published) or takes a leading underscore. An
  exception is keyed by location in :data:`UNLISTED_EXEMPTIONS`, with its
  reason, and an entry that no longer applies is reported.

The **version row** shows the package version as a literal
(``phonometry.__version__  # '3.3.0'``). Nothing else re-reads that literal
after a release bump, so it is checked against the installed
``phonometry.__version__``. A page showing no literal fails too, so the check
cannot pass by finding nothing.

Usage::

    python scripts/check_api_reference.py

Exit status 0 when every public name has a row that says what it is, every
plain-name row names something public, every usage example calls the library
the way its signatures allow, every public name has one address and
none is an alias, every public module is reached by its name and declares an
``__all__`` that lists all it publishes, and the page shows the current
version; 1 otherwise.
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
from typing import TYPE_CHECKING, TypeAliasType, TypeVar, get_origin

from api_taxonomy import public_names

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import ModuleType

#: What a package held under a name before anything was imported there.
_NOTHING = object()

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


#: The page's grouping space inside a number (``2\u202f600.0``), which
#: Python does not read.
_GROUPED_DIGITS = re.compile(r"(?<=\d)\u202f(?=\d)")

#: ``, ...)`` closing a call, "and the rest of its arguments", which the page
#: also writes after keywords, where Python refuses it.
_ELIDED_TAIL = re.compile(r",\s*\.\.\.\s*\)")


def usage_roots() -> dict[str, object]:
    """What a usage example may start a call from, by the name it is written with.

    The examples call through a domain package (``materials.porosity(...)``)
    or name a published object directly (``OctaveFilterBank(...)``,
    ``Signal.from_file(...)``); anything else they start from is a variable
    of the example or a third party, and is not the library's to check.

    :return: Written name to the object it reaches.
    """
    import phonometry

    owners = public_names()
    roots: dict[str, object] = {
        name: getattr(package, name) for name, package in owners.items()
    }
    for name in phonometry.__all__:
        if inspect.ismodule(getattr(phonometry, name)):
            roots[name] = getattr(phonometry, name)
    roots["phonometry"] = phonometry
    return roots


def example_problems(markdown: str, roots: Mapping[str, object]) -> list[str]:
    """Usage examples that call the library in a way its signatures refuse.

    The table is the one page no snippet gate runs, so a parameter that turns
    keyword-only, or a function that is renamed, leaves an example a reader
    copies and fails on. Every call in a row's usage cell (the last one; the
    description names functions as ``info()`` without calling them) that
    starts from something the library publishes is bound to that callable's
    signature with :meth:`inspect.Signature.bind`, which counts the arguments
    and checks the keywords without running anything. An argument list the
    example elides (``f(x, ...)``) is held only to what it writes.

    :param markdown: The ``docs/reference/api/index.md`` source.
    :param roots: What a call may start from (see :func:`usage_roots`).
    :return: One message per refused call, in reading order.
    """
    problems: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = re.split(r"(?<!\\)\|", stripped)
        if len(cells) < 6:
            continue  # Not a row of the four-column name table.
        row = " / ".join(_BACKTICKED.findall(cells[1]))
        problems.extend(
            f"{row}: `{fragment}` calls {problem}"
            for fragment in _BACKTICKED.findall(cells[-2])
            for problem in _fragment_problems(fragment, roots)
        )
    return problems


def _fragment_problems(fragment: str, roots: Mapping[str, object]) -> Iterator[str]:
    """Each call in one backticked fragment that its target refuses.

    :param fragment: The text between two backticks of a usage cell.
    :param roots: What a call may start from.
    :return: ``"<dotted name>, which ..."`` per refused call; nothing for a
        fragment that is not Python (``.plot()``, ``10 lg(...)``).
    """
    source = _GROUPED_DIGITS.sub("", fragment)
    elided = bool(_ELIDED_TAIL.search(source))
    source = _ELIDED_TAIL.sub(")", source)
    if source.rstrip().endswith(":"):
        source += " pass"  # ``with simulation.use(...):`` opens a block.
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        parts = _dotted_name(call.func)
        target = _call_target(parts, roots) if parts else None
        if target is None:
            continue
        dotted = ".".join(parts)
        if isinstance(target, str):
            yield f"{dotted}, which does not exist: {target}"
            continue
        callee, takes_self = target
        if refusal := _refusal(call, callee, takes_self=takes_self, elided=elided):
            yield f"{dotted}, which refuses it: {refusal}"


def _dotted_name(func: ast.expr) -> list[str]:
    """``["a", "b", "c"]`` for a call written ``a.b.c(...)``; empty otherwise."""
    parts: list[str] = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if not isinstance(func, ast.Name):
        return []
    parts.append(func.id)
    return parts[::-1]


def _call_target(
    parts: list[str], roots: Mapping[str, object]
) -> tuple[object, bool] | str | None:
    """The callable a dotted call reaches, and whether it still needs its instance.

    :param parts: The dotted name of the call, root first.
    :param roots: What a call may start from.
    :return: ``(callable, takes_self)``; a message when a link of the name is
        missing; ``None`` when the root is not the library's. ``takes_self`` is
        true for a method the example shows on its class
        (``Result.plot_geometry()``), which a reader calls on an instance.
    """
    owner: object = None
    target = roots.get(parts[0], _NOTHING)
    if target is _NOTHING:
        return None
    for depth, attribute in enumerate(parts[1:], start=1):
        owner, target = target, getattr(target, attribute, _NOTHING)
        if target is _NOTHING:
            return f"{'.'.join(parts[:depth])} has no attribute {attribute!r}"
    takes_self = inspect.isclass(owner) and inspect.isfunction(
        inspect.getattr_static(owner, parts[-1], None)
    )
    return target, takes_self


def _refusal(call: ast.Call, target: object, *, takes_self: bool, elided: bool) -> str:
    """Why ``target``'s signature refuses ``call``, or ``""`` when it binds.

    :param call: The call as the example writes it.
    :param target: The callable it reaches.
    :param takes_self: Whether the call leaves out the instance a method takes.
    :param elided: Whether the fragment elides arguments after its keywords.
    :return: The :class:`TypeError` text :meth:`inspect.Signature.bind` raises.
    """
    if any(isinstance(arg, ast.Starred) for arg in call.args) or any(
        keyword.arg is None for keyword in call.keywords
    ):
        return ""  # ``*args`` and ``**options`` hide what they pass.
    if not callable(target):
        return ""
    try:
        signature = inspect.signature(target)
    except ValueError:
        return ""  # A builtin with no signature to read.
    positional = list(call.args)
    for index, arg in enumerate(positional):
        if isinstance(arg, ast.Constant) and arg.value is Ellipsis:
            positional, elided = positional[:index], True
            break
    keywords = dict.fromkeys(keyword.arg for keyword in call.keywords if keyword.arg)
    bind = signature.bind_partial if elided else signature.bind
    try:
        bind(*[None] * (len(positional) + takes_self), **keywords)
    except TypeError as error:
        return str(error)
    return ""


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
            if kind := typing_kind(obj):
                problems.append(f"{where}, {kind}")
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
            module, _ = _import_public(info.name)
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
    if kind := typing_kind(getattr(module, name, None)):
        return kind
    if name not in domain.__all__:
        return f"which {domain.__name__} does not publish"
    if _is_public_path(sources.get(name, "_")):
        return f"a second address for {sources[name]}.{name}"
    if listed_by is not None and name in listed_by:
        return f"which {listed_by[name]} lists too"
    return ""


#: A public-looking name a public module defines and does not list, allowed
#: here for a reason, keyed ``"<module>.<name>"``. An entry whose name the
#: module no longer defines unlisted is reported, so the table cannot go stale.
UNLISTED_EXEMPTIONS: Mapping[str, str] = {}


def defined_names(module: ModuleType) -> list[str]:
    """Every name ``module``'s own statements bind at import, in source order.

    A ``def``, a ``class``, an assignment or a ``type`` statement at module
    level, also inside an ``if`` or a ``try`` that runs; an import binds a name
    too but defines nothing, and an ``if TYPE_CHECKING:`` block binds nothing a
    caller can reach. An annotation without a value binds nothing either.

    :param module: An imported module whose source is available.
    :return: The bound names, each once, in the order the source binds them.
    """
    try:
        tree = ast.parse(inspect.getsource(module))
    except (OSError, TypeError):
        return []
    found: dict[str, None] = {}
    statements = list(tree.body)
    while statements:
        statement = statements.pop(0)
        if isinstance(statement, (ast.If, ast.Try)):
            if not _is_type_checking_block(statement):
                nested = [*statement.body, *statement.orelse]
                if isinstance(statement, ast.Try):
                    nested += [s for h in statement.handlers for s in h.body]
                    nested += statement.finalbody
                statements[:0] = nested
        elif isinstance(
            statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            found[statement.name] = None
        elif isinstance(statement, ast.TypeAlias):
            found[statement.name.id] = None
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            if isinstance(statement.target, ast.Name):
                found[statement.target.id] = None
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                for node in ast.walk(target):
                    if isinstance(node, ast.Name):
                        found[node.id] = None
    return list(found)


def typing_kind(obj: object) -> str:
    """Which construct that only describes types *obj* is, in a few words.

    :param obj: The object a module-level name resolves to.
    :return: ``"a type alias"``, ``"a TypeVar"``, ``"a Protocol"``, or ``""``
        for anything else.
    """
    if is_type_alias(obj):
        return "a type alias"
    if isinstance(obj, TypeVar):
        return "a TypeVar"
    if inspect.isclass(obj) and getattr(obj, "_is_protocol", False):
        return "a Protocol"
    return ""


def is_typing_construct(obj: object) -> bool:
    """Whether *obj* only describes types: an alias, a ``TypeVar``, a ``Protocol``.

    None of them is published (an alias reads as its definition in the
    reference), and none is a value or a callable a reader would reach for.

    :param obj: The object a module-level name resolves to.
    """
    return bool(typing_kind(obj))


def module_problems(domains: list[ModuleType]) -> list[str]:
    """Every public module a reader cannot reach by its name, or that hides what it holds.

    A module whose name its package gives to something else (a function, a
    class, a constant) is reachable only by a ``from`` import of its file
    path: the package attribute of that name is the other object, so ``import
    a.b.c as m`` binds it and ``a.b.c.name`` fails. A public module with no
    ``__all__`` publishes nothing it can be held to. And a module that does
    declare one says what it publishes only if the list is the whole truth: a
    name it defines and its package publishes is in it, and a public-looking
    name it defines is in it or is a typing construct (a type alias, a
    ``TypeVar`` or a ``Protocol``, none of which is published). Anything else
    a module defines for its own use takes a leading underscore. The domain
    packages are walked too: each is a public module like any other.

    :param domains: The domain packages the top level publishes.
    :return: One message per offending module or name, in walking order.
    """
    problems: list[str] = []
    seen_exemptions: set[str] = set()
    for domain in domains:
        for name, module, held in _public_modules(domain):
            parent_name, _, leaf = name.rpartition(".")
            parent = sys.modules.get(parent_name)
            binding = _package_binding(parent, leaf)
            if not inspect.ismodule(held):
                kind = "class" if inspect.isclass(held) else type(held).__name__
                problems.append(
                    f"{name} is hidden behind {parent_name}.{leaf}, a {kind}: "
                    f"`import {name}` binds the {kind}, so the module is private "
                    f"(_{leaf}) and its names are reached through {parent_name}"
                )
            elif binding is not None:
                problems.append(
                    f"{name} is hidden behind {parent_name}.{leaf}: the package "
                    f"binds {leaf!r} by `{binding}`, so the module is private "
                    f"(_{leaf}) and its names are reached through {parent_name}"
                )
            if "__all__" not in vars(module):
                problems.append(
                    f"{name} declares no __all__, so nothing says which of its "
                    "names are public"
                )
                continue
            problems.extend(
                _unlisted_problems(name, module, parent, parent_name, seen_exemptions)
            )
    problems.extend(
        f"UNLISTED_EXEMPTIONS names {key}, which is no longer defined unlisted; "
        "drop the entry"
        for key in UNLISTED_EXEMPTIONS
        if key not in seen_exemptions
        and any(key.startswith(d.__name__ + ".") for d in domains)
    )
    return problems


def _public_modules(
    domain: ModuleType,
) -> Iterator[tuple[str, ModuleType, object]]:
    """Every public module of ``domain`` with what its package held under its name.

    The package attribute is read *before* the module is imported, because
    importing a submodule for the first time binds the package attribute of its
    name to the module: read afterwards, a function the package published under
    that name would already have been replaced, and the hidden module would
    pass. When the import did replace something, the package gets it back, so
    walking the tree leaves the library as it found it.

    :param domain: A domain package the top level publishes.
    :return: ``(dotted name, module, object the package held)`` in walking
        order, the domain itself first; the held object is the module when
        the package held nothing under that name.
    """
    yield domain.__name__, domain, domain
    for info in pkgutil.walk_packages(domain.__path__, domain.__name__ + "."):
        if _is_public_path(info.name):
            module, held = _import_public(info.name)
            yield info.name, module, held


def _import_public(name: str) -> tuple[ModuleType, object]:
    """Import the module ``name`` and say what its package held under its name.

    :param name: A dotted module name whose package is already imported.
    :return: The module, and the object the package held under the module's
        last name component before the import (the module itself when it held
        nothing). An object the import replaced is put back on the package.
    """
    parent_name, _, leaf = name.rpartition(".")
    parent = sys.modules.get(parent_name)
    before = vars(parent).get(leaf, _NOTHING) if parent is not None else _NOTHING
    module = importlib.import_module(name)
    if before is _NOTHING:
        return module, module
    if before is not module and getattr(parent, leaf, None) is module:
        setattr(parent, leaf, before)
    return module, before


def _package_binding(parent: ModuleType | None, leaf: str) -> str | None:
    """The statement of ``parent``'s ``__init__`` that gives ``leaf`` to something else.

    Reading the package source closes what reading its attributes cannot: a
    module that some other import reached first has already replaced the
    published object, and then the attribute shows the module. Only importing
    the submodule itself (``from . import leaf``, ``import pkg.leaf``) binds
    the name to it; any other import, assignment, function or class of that
    name hides it.

    :param parent: The package, or ``None`` for a top-level module.
    :param leaf: The last component of the module's dotted name.
    :return: The offending statement as source text, or ``None``.
    """
    source_path = getattr(parent, "__file__", None)
    if parent is None or source_path is None or not source_path.endswith("__init__.py"):
        return None
    tree = ast.parse(pathlib.Path(source_path).read_text(encoding="utf-8"))
    for node in _module_level_statements(tree.body):
        binding = _binding_other_than_submodule(node, parent.__name__, leaf)
        if binding is not None:
            return binding
    return None


def _module_level_statements(body: list[ast.stmt]) -> Iterator[ast.stmt]:
    """The statements that run at import time, inside ``if``/``try``/``with`` too."""
    for node in body:
        yield node
        for field in ("body", "orelse", "finalbody", "handlers"):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                break
            for child in getattr(node, field, ()):
                if isinstance(child, ast.ExceptHandler):
                    yield from _module_level_statements(child.body)
                elif isinstance(child, ast.stmt):
                    yield from _module_level_statements([child])


def _binding_other_than_submodule(
    node: ast.stmt, package: str, leaf: str
) -> str | None:
    """How ``node`` binds ``leaf`` in ``package`` to anything but the submodule.

    :param node: A statement of the package's ``__init__``.
    :param package: The package's dotted name.
    :param leaf: The name of one of its submodules.
    :return: The binding written as source (``from ._impl import probe``,
        ``def probe``, ``probe = ...``), or ``None`` when ``node`` leaves the
        name alone or binds it to the submodule itself.
    """
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return f"def {leaf}" if node.name == leaf else None
    if isinstance(node, ast.ClassDef):
        return f"class {leaf}" if node.name == leaf else None
    if isinstance(node, ast.ImportFrom):
        source = "." * node.level + (node.module or "")
        submodule_itself = source in {".", package}
        for alias in node.names:
            if (alias.asname or alias.name) == leaf and not (
                submodule_itself and alias.name == leaf
            ):
                renamed = f" as {alias.asname}" if alias.asname else ""
                return f"from {source} import {alias.name}{renamed}"
        return None
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.asname == leaf:
                return f"import {alias.name} as {leaf}"
        return None
    targets: list[ast.expr] = []
    if isinstance(node, ast.Assign):
        targets = list(node.targets)
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        targets = [node.target]
    if any(
        isinstance(sub, ast.Name) and sub.id == leaf
        for target in targets
        for sub in ast.walk(target)
    ):
        return f"{leaf} = ..."
    return None


def _unlisted_problems(
    name: str,
    module: ModuleType,
    parent: ModuleType | None,
    parent_name: str,
    seen_exemptions: set[str],
) -> list[str]:
    """The names ``module`` defines that its ``__all__`` should say and does not.

    :param name: The module's dotted name.
    :param module: A public module that declares ``__all__``.
    :param parent: The package it belongs to, if any.
    :param parent_name: That package's dotted name.
    :param seen_exemptions: Collects the :data:`UNLISTED_EXEMPTIONS` keys used.
    :return: One message per name, in source order.
    """
    listed = set(module.__all__)
    published = set(getattr(parent, "__all__", ()))
    problems: list[str] = []
    for defined in defined_names(module):
        if defined.startswith("_") or defined in listed:
            continue
        obj = getattr(module, defined, None)
        if defined in published and getattr(parent, defined, None) is obj:
            problems.append(
                f"{name} defines {defined!r}, which {parent_name} publishes, and "
                "its __all__ does not list it"
            )
            continue
        if is_typing_construct(obj):
            continue
        key = f"{name}.{defined}"
        if key in UNLISTED_EXEMPTIONS:
            seen_exemptions.add(key)
            continue
        problems.append(
            f"{name} defines {defined!r} and its __all__ does not list it; a "
            f"name its package does not publish is private (_{defined})"
        )
    return problems


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
    refused = example_problems(markdown, usage_roots())
    if refused:
        print(
            f"docs/reference/api/index.md shows {len(refused)} call(s) the "
            "library refuses; a reader copies the example and it fails:"
        )
        for problem in refused:
            print(f"  - {problem}")
        print("Write each call the way the signature takes it.")
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
    modules = module_problems(domains)
    if modules:
        print(
            f"{len(modules)} public module problem(s); a module is never hidden "
            "behind a name of its package, and every public module says what it "
            "publishes:"
        )
        for problem in modules:
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
        f"says what each of them is, calls each the way its signature allows, "
        f"and shows version {phonometry.__version__}; "
        "every public name has one address and none is a type alias, and every "
        "public module is reached by its name and lists all it publishes."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
