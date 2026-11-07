#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The values a choice accepts are written in its ``:param:`` field.

A choice is typed with a ``Literal``, and a ``Literal`` written once and
reused is a type alias (``Mode = Literal["rms", "peak"]``) that the package
never publishes. Every module reads its annotations as text
(``from __future__ import annotations``), so ``help()`` and the signature a
notebook shows print ``mode: 'Mode' = 'rms'``: the name of an alias no
caller can look up, and not one of the values. Of the 1416 public
parameters typed with such an alias, 512 named in their ``:param:`` field,
or a record's ``:ivar:``, none or only some of the values they accept, 237
of them with no field at all, ``language`` on 202 plots among them. The
field lists them now, each written as the caller types it (style rule D24).
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
import re
import sys
import types
import typing
from functools import cache

import pytest

import phonometry


def _values(annotation: object, depth: int = 0) -> list[object]:
    """The values of a ``Literal``, through aliases and unions; empty for any other type."""
    if depth > 10:
        return []
    if isinstance(annotation, typing.TypeAliasType):
        return _values(annotation.__value__, depth + 1)
    origin = typing.get_origin(annotation)
    if origin is typing.Literal:
        return list(typing.get_args(annotation))
    if origin in {typing.Union, types.UnionType}:
        return [v for a in typing.get_args(annotation) for v in _values(a, depth + 1)]
    return []


@cache
def _imported(module: str) -> dict[str, object]:
    """Every name *module* imports, the ``TYPE_CHECKING`` blocks included."""
    found: dict[str, object] = {}
    loaded = sys.modules[module]
    tree = ast.parse(inspect.getsource(loaded))
    package = loaded.__package__ or ""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        source = (
            importlib.util.resolve_name("." * node.level + (node.module or ""), package)
            if node.level
            else node.module or ""
        )
        for alias in node.names:
            try:
                found[alias.asname or alias.name] = getattr(
                    importlib.import_module(source), alias.name
                )
            except (ImportError, AttributeError):
                continue
    return found


def _aliased_values(
    annotation: str, namespace: dict[str, object], module: str
) -> list[object]:
    """The values of every ``Literal`` alias *annotation* names."""
    values: list[object] = []
    for node in ast.walk(ast.parse(annotation, mode="eval")):
        if not isinstance(node, ast.Name):
            continue
        target = namespace.get(node.id, _imported(module).get(node.id))
        if isinstance(target, typing.TypeAliasType) or (
            typing.get_origin(target) is typing.Literal
        ):
            values += _values(target)
    return values


#: The fields a docstring's field list holds, each of which ends the one before
#: it; a role inside a field's text (``:func:``, ``:math:``) does not.
_FIELDS = (
    "param|ivar|cvar|var|return|returns|rtype|raises|raise|warns|type|vartype|yields"
)


def _field(docstring: str, name: str, kinds: str = "param") -> str | None:
    """The text of the ``:param name:`` field of *docstring*, or of one of *kinds*."""
    found = re.search(
        rf":(?:{kinds})\s+(?:[^:\n]*\s)?\*{{0,2}}{re.escape(name)}:"
        rf"(.*?)(?=\n\s*:(?:{_FIELDS})\b|\Z)",
        docstring,
        re.DOTALL,
    )
    return found.group(1) if found else None


def _docstring(
    function: typing.Callable[..., object], owner: type | None
) -> tuple[str, str]:
    """The docstring that documents *function*'s parameters, and the fields it uses.

    A record's ``__init__`` is written by :mod:`dataclasses` and documented by
    the class's ``:ivar`` fields; an ``__init__`` with no docstring of its own
    is documented by the class's.
    """
    code = inspect.unwrap(function).__code__
    if (
        owner is not None
        and function.__name__ == "__init__"
        and (code.co_filename == "<string>" or not function.__doc__)
    ):
        return inspect.getdoc(owner) or "", "ivar|param"
    return inspect.getdoc(function) or "", "param"


def _callables() -> dict[str, tuple[typing.Callable[..., object], type | None]]:
    """Every public function, and every public method of a public class, once."""
    found: dict[str, tuple[typing.Callable[..., object], type | None]] = {}
    seen: set[int] = set()
    for domain in phonometry.__all__:
        package = getattr(phonometry, domain)
        if not inspect.ismodule(package):
            continue
        for name in package.__all__:
            item = getattr(package, name)
            if id(item) in seen:
                continue
            seen.add(id(item))
            if inspect.isfunction(item):
                found[f"{domain}.{name}"] = (item, None)
            elif inspect.isclass(item) and item.__module__.startswith("phonometry"):
                for member, value in vars(item).items():
                    if member.startswith("_") and member != "__init__":
                        continue
                    function = getattr(value, "__func__", value)
                    if inspect.isfunction(function):
                        found[f"{domain}.{name}.{member}"] = (function, item)
    return found


def _undocumented_choices() -> list[str]:
    missing: list[str] = []
    for where, (function, owner) in sorted(_callables().items()):
        unwrapped = inspect.unwrap(function)
        namespace = unwrapped.__globals__
        docstring, kinds = _docstring(function, owner)
        for parameter in inspect.signature(
            function, eval_str=False
        ).parameters.values():
            if not isinstance(parameter.annotation, str):
                continue
            values = _aliased_values(
                parameter.annotation, namespace, namespace["__name__"]
            )
            text = _field(docstring, parameter.name, kinds) or ""
            absent = [
                value
                for value in dict.fromkeys(values)
                if not re.search(r"[`'\"]" + re.escape(str(value)) + r"[`'\"]", text)
            ]
            if absent:
                missing.append(f"{where}({parameter.name}): {absent}")
    return missing


@pytest.mark.whole_tree
def test_every_choice_typed_by_an_alias_lists_its_values() -> None:
    missing = _undocumented_choices()
    assert not missing, f"{len(missing)} parameters:\n" + "\n".join(missing)


def test_the_check_reads_an_alias_imported_for_the_type_checker_alone() -> None:
    """``Language`` reaches the plots under ``TYPE_CHECKING`` only, and is read."""
    plot = phonometry.filters.OctaveFilterResult.plot
    namespace = inspect.unwrap(plot).__globals__
    annotation = (
        inspect.signature(plot, eval_str=False).parameters["language"].annotation
    )
    assert _aliased_values(annotation, namespace, namespace["__name__"]) == ["en", "es"]
