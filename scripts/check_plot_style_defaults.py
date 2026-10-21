#!/usr/bin/env python3
"""Fail on a style default the caller cannot override.

Matplotlib aliases seven artist properties: ``color`` is also ``c``,
``linewidth`` is ``lw``, ``linestyle`` is ``ls``, ``markersize`` is ``ms``, and
the three marker-edge and marker-face properties have their own short forms.
Since matplotlib 3.3 a call that receives both spellings of one property is a
``TypeError`` ("Got both 'color' and 'c', which are aliases of one another").

A renderer that installs its own default before forwarding ``kwargs`` to an
artist therefore breaks every caller who used the other spelling. The defect is
invisible in review, because each line reads exactly like the hundred around it,
and invisible in the tests unless one happens to pass the short spelling.

It comes in three shapes, and all three are refused here:

* ``kwargs.setdefault("color", ...)``, which leaves both spellings in the
  mapping and makes the artist refuse the call;
* ``kwargs["color"]`` or ``kwargs.pop("color", ...)``, where a renderer reads
  its own default back to draw a second artist in the same style. The read
  raises ``KeyError`` under the short spelling, and the ``pop`` is worse: it
  silently draws the second artist in the library's colour and leaves the
  caller's on the first, a figure in two colours with nothing to say why;
* ``{"color": _C_PRIMARY, **kwargs}``, the same default written as a literal.

The three helpers of :mod:`phonometry._plot.common` are the fix:
:func:`style_default`, :func:`style_get` and :func:`style_pop`, and
:func:`styled` for the literal. Each honours both spellings.

In those three shapes only the aliased properties are refused.
``kwargs.setdefault("label", ...)`` and ``kwargs.setdefault("marker", ...)``
are fine, because matplotlib gives those no second name, and this says nothing
about them. The read-back and literal shapes are refused only on a mapping that
is the function's own ``**kwargs``: a local dictionary the caller never sees may
hold whatever it likes.

A fourth shape is refused for every property, aliased or not:
``ax.bar(x, h, zorder=3, **kwargs)``, a keyword the renderer writes beside the
caller's. A caller who passes ``zorder`` too gets ``TypeError: got multiple
values for keyword argument 'zorder'`` and no figure, although the renderer
documents its keywords as forwarded to that very call. The fix is the same
merge, ``ax.bar(x, h, **styled(kwargs, zorder=3))``. A keyword that names a
parameter of the function itself cannot be in ``**kwargs``, and a call to one
of the package's own helpers passes that helper its parameters beside the
caller's properties, so neither is refused.

Exit status 0 when no aliased property is defaulted or read back by hand and
no keyword is written beside the caller's, 1 otherwise.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterator

#: The repository, for paths a reader can click.
_REPO = Path(__file__).resolve().parent.parent

#: The package whose renderers forward keyword arguments to artists.
_ROOT = _REPO / "src" / "phonometry"

#: The long and the short spelling of every property matplotlib aliases, as
#: ``_STYLE_ALIASES`` in ``_plot/common.py`` writes them: the table
#: :func:`style_default` itself reads, compared with this one so the two
#: cannot drift apart.
_ALIAS_PAIRS: dict[str, str] = {
    "color": "c",
    "linestyle": "ls",
    "linewidth": "lw",
    "markeredgecolor": "mec",
    "markeredgewidth": "mew",
    "markerfacecolor": "mfc",
    "markersize": "ms",
}
#: Every spelling of every aliased property, long and short.
_ALIASED: frozenset[str] = frozenset(_ALIAS_PAIRS) | frozenset(_ALIAS_PAIRS.values())


def _kwarg_names(tree: ast.AST) -> set[str]:
    """The ``**kwargs`` parameter of every function in one module.

    Only those mappings reach an artist carrying whatever the caller wrote, so
    only those can hold the other spelling. A local dictionary is the
    renderer's own and is left alone.
    """
    return {
        node.args.kwarg.arg
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.args.kwarg
    }


def _aliased_key(node: ast.expr | None) -> str | None:
    """The aliased property a constant subscript or argument names, if any."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value if node.value in _ALIASED else None
    return None


def _findings(path: Path) -> list[tuple[int, str]]:
    """Every hand-rolled style default in one file, with its line and reason."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    kwargs_of = _kwarg_names(tree)
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            name = _aliased_key(node.args[0]) if node.args else None
            if name is None:
                continue
            if node.func.attr == "setdefault":
                found.append(
                    (node.lineno, f"setdefault of the aliased property {name!r}")
                )
            elif (
                node.func.attr in {"get", "pop"}
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in kwargs_of
            ):
                found.append(
                    (node.lineno, f"{node.func.attr} of the aliased property {name!r}")
                )
        elif (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id in kwargs_of
            and isinstance(node.ctx, ast.Load)
        ):
            name = _aliased_key(node.slice)
            if name is not None:
                found.append(
                    (node.lineno, f"read-back of the aliased property {name!r}")
                )
        elif isinstance(node, ast.Dict) and node.keys and node.keys[-1] is None:
            spread = node.values[-1]
            if not isinstance(spread, ast.Name) or spread.id not in kwargs_of:
                continue
            named = {
                key.value
                for key in node.keys[:-1]
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            }
            found.extend(
                (node.lineno, f"literal default of the aliased property {name!r}")
                for name in sorted(named & set(_ALIASED))
            )
    found.extend(_unoverridable(tree))
    return sorted(found)


def _own_names(tree: ast.AST) -> set[str]:
    """What one module defines, or imports from the package, by name.

    A call to one of them passes a helper of the package its parameters beside
    the caller's properties, which is not a default the caller could override.
    ``cls`` and ``self`` reach the class being defined, which is the package's
    too.
    """
    names: set[str] = {"cls", "self"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.ImportFrom) and (
            node.level > 0 or (node.module or "").startswith("phonometry")
        ):
            names.update(alias.asname or alias.name for alias in node.names)
    return names


def _call_root(func: ast.expr) -> str:
    """The name a call starts from: ``ax`` for ``ax.bar``, ``f`` for ``f``."""
    while isinstance(func, (ast.Attribute, ast.Subscript, ast.Call)):
        func = func.func if isinstance(func, ast.Call) else func.value
    return func.id if isinstance(func, ast.Name) else ""


def _unoverridable(tree: ast.AST) -> set[tuple[int, str]]:
    """Every keyword written beside a function's own ``**kwargs`` in one call.

    :param tree: One parsed module.
    :return: ``(line, reason)`` per keyword, for the calls that do not go to
        one of the package's own helpers.
    """
    own = _own_names(tree)
    found: set[tuple[int, str]] = set()
    for function in ast.walk(tree):
        if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.update(_written_beside(function, own))
    return found


def _written_beside(
    function: ast.FunctionDef | ast.AsyncFunctionDef, own: set[str]
) -> Iterator[tuple[int, str]]:
    """The keywords one function writes beside the caller's keywords.

    The caller's keywords arrive in the function's ``**kwargs``, or, in a
    helper a renderer hands them on to, in a parameter named ``kwargs`` (or
    ``..._kwargs``). They travel on in every mapping the function builds from
    them (``options = dict(kwargs)``). A keyword that names a parameter of a
    function with ``**kwargs`` cannot be in them. Nor can one the function
    takes out (``kwargs.pop("zorder", 3)``, ``del kwargs["zorder"]``,
    :func:`style_pop`) or refuses by name (:func:`refuse_fixed_keywords`),
    provided it does so before the call, on the very mapping the call spreads
    or on one that mapping was copied from afterwards. None of those can
    collide, and they are left alone.
    """
    seeds = _seeds(function)
    if not seeds:
        return
    lineage = _lineage(function, seeds)
    arguments = function.args
    bound: set[str] = set()
    if arguments.kwarg is not None:
        bound = {
            arg.arg
            for arg in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
        }
    removals = _removals(function, lineage)
    for call in ast.walk(function):
        if not isinstance(call, ast.Call) or _call_root(call.func) in own:
            continue
        spread = _spread_carriers(call, lineage)
        if not spread:
            continue
        callee = ast.unparse(call.func)
        for keyword in call.keywords:
            if keyword.arg is None or keyword.arg in bound:
                continue
            if _removed_before(keyword.arg, call.lineno, spread, removals, lineage):
                continue
            yield (
                call.lineno,
                f"{keyword.arg!r} written beside **kwargs in {callee}(), "
                "so a caller cannot pass it",
            )


def _seeds(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """The names the caller's keywords arrive under in ``function``."""
    arguments = function.args
    seeds = {
        arg.arg
        for arg in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
        if arg.arg == "kwargs" or arg.arg.endswith("_kwargs")
    }
    if arguments.kwarg is not None:
        seeds.add(arguments.kwarg.arg)
    return seeds


class _Lineage(NamedTuple):
    """Which names carry the caller's keywords, from where and since when."""

    #: The line each carrier is first bound on, 0 for the ones it arrives in.
    born: dict[str, int]
    #: The carriers each carrier was built from.
    parents: dict[str, set[str]]


def _lineage(
    function: ast.FunctionDef | ast.AsyncFunctionDef, seeds: set[str]
) -> _Lineage:
    """``seeds`` and every name the function binds to something built from them."""
    born = dict.fromkeys(seeds, 0)
    parents: dict[str, set[str]] = {seed: set() for seed in seeds}
    grew = True
    while grew:
        grew = False
        for node in ast.walk(function):
            if not isinstance(node, ast.Assign):
                continue
            read = _names(node.value) & set(born)
            if not read:
                continue
            for target in node.targets:
                for name in _names(target) - set(born):
                    born[name] = node.lineno
                    parents[name] = read
                    grew = True
    return _Lineage(born, parents)


def _names(expression: ast.AST) -> set[str]:
    """Every name ``expression`` reads or binds."""
    return {node.id for node in ast.walk(expression) if isinstance(node, ast.Name)}


def _spread_carriers(call: ast.Call, lineage: _Lineage) -> set[str]:
    """The carriers ``call`` unpacks with ``**``, in any expression.

    The caller's keywords arrive as much through ``**kwargs`` as through
    ``**{"label": ..., **kwargs}``, ``**styled(kwargs, ...)`` or a copy the
    function made.
    """
    return {
        name
        for keyword in call.keywords
        if keyword.arg is None
        for name in _names(keyword.value) & set(lineage.born)
    }


def _removals(
    function: ast.FunctionDef | ast.AsyncFunctionDef, lineage: _Lineage
) -> list[tuple[str, str, int]]:
    """``(mapping, key, line)`` for each key the function takes out or refuses.

    ``kwargs.pop("width", 0.7)``, ``del kwargs["width"]``, ``style_pop(kwargs,
    "color", ...)`` (both spellings) and ``refuse_fixed_keywords(kwargs, ...,
    "bottom")``, on a carrier of the caller's keywords.
    """
    removals: list[tuple[str, str, int]] = []
    for node in ast.walk(function):
        if isinstance(node, ast.Delete):
            removals.extend(
                (target.value.id, target.slice.value, node.lineno)
                for target in node.targets
                if isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id in lineage.born
                and isinstance(target.slice, ast.Constant)
                and isinstance(target.slice.value, str)
            )
        elif isinstance(node, ast.Call):
            removals.extend(_removed_by(node, lineage))
    return removals


def _removed_by(call: ast.Call, lineage: _Lineage) -> list[tuple[str, str, int]]:
    """The keys one call takes out of a carrier of the caller's keywords."""
    called = _called(call)
    if called == "pop" and isinstance(call.func, ast.Attribute):
        mapping = call.func.value
        keys = _strings(call.args[:1])
    elif called in {"style_pop", "refuse_fixed_keywords"} and call.args:
        mapping = call.args[0]
        if called == "style_pop":
            keys = {
                spelling
                for name in _strings(call.args[1:2])
                for spelling in (name, *_alias_of(name))
            }
        else:
            keys = _strings(call.args[1:])
    else:
        return []
    if not isinstance(mapping, ast.Name) or mapping.id not in lineage.born:
        return []
    return [(mapping.id, key, call.lineno) for key in sorted(keys)]


def _removed_before(
    key: str,
    line: int,
    spread: set[str],
    removals: list[tuple[str, str, int]],
    lineage: _Lineage,
) -> bool:
    """Whether ``key`` is out of every mapping a call on ``line`` spreads.

    It is when it was taken out before the call, of the mapping spread, or of
    a mapping that one was copied from after the removal.
    """
    return any(
        removed == key
        and at < line
        and all(_inherits(name, mapping, at, lineage) for name in spread)
        for mapping, removed, at in removals
    )


def _inherits(name: str, mapping: str, at: int, lineage: _Lineage) -> bool:
    """Whether ``name`` is ``mapping``, or was built from it after line ``at``."""
    if name == mapping:
        return True
    return lineage.born[name] > at and any(
        _inherits(parent, mapping, at, lineage) for parent in lineage.parents[name]
    )


def _alias_of(name: str) -> tuple[str, ...]:
    """The other spelling of an aliased property, or nothing."""
    pairs = (
        *_ALIAS_PAIRS.items(),
        *((short, long) for long, short in _ALIAS_PAIRS.items()),
    )
    return tuple(other for one, other in pairs if one == name)


def _called(call: ast.Call) -> str:
    """The last name of what ``call`` calls: ``f`` for ``f()`` and ``m.f()``."""
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    return func.id if isinstance(func, ast.Name) else ""


def _strings(nodes: list[ast.expr]) -> set[str]:
    """The string constants among ``nodes``."""
    return {
        node.value
        for node in nodes
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _helper_aliases() -> set[str] | None:
    """Every spelling in ``_STYLE_ALIASES``, read off the helper's source.

    Read rather than imported. Importing the module would pull numpy in behind
    it, and this gate runs in the step that installs nothing, next to the other
    check that walks the tree as text. It is also the honest way round: what
    this compares itself against is the table as written, not as some
    environment happens to build it.
    """
    source = (_ROOT / "_plot" / "common.py").read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.AnnAssign | ast.Assign):
            continue
        targets = [node.target] if isinstance(node, ast.AnnAssign) else node.targets
        names = {t.id for t in targets if isinstance(t, ast.Name)}
        if "_STYLE_ALIASES" not in names or not isinstance(node.value, ast.Dict):
            continue
        pairs: list[tuple[str, str]] = []
        for key, value in zip(node.value.keys, node.value.values, strict=True):
            if (
                isinstance(key, ast.Constant)
                and isinstance(key.value, str)
                and isinstance(value, ast.Constant)
                and isinstance(value.value, str)
            ):
                pairs.append((key.value, value.value))
        if len(pairs) != len(node.value.keys):
            return None
        return {long for long, _ in pairs} | {short for _, short in pairs}
    return None


def _aliases_agree() -> str | None:
    """Whether this gate's table still matches the one ``style_default`` reads.

    The gate refuses exactly the properties the helper knows how to default. If
    someone teaches the helper an eighth alias and not this file, the gate would
    go on passing the very line the helper was extended to replace, so the two
    tables are compared rather than trusted.
    """
    helper = _helper_aliases()
    if helper is None:
        return (
            "_STYLE_ALIASES could not be read from src/phonometry/_plot/common.py "
            "as a literal table of strings, so this gate cannot tell whether it "
            "still refuses what the helper defaults."
        )
    if helper == set(_ALIASED):
        return None
    missing = ", ".join(sorted(helper - set(_ALIASED))) or "none"
    extra = ", ".join(sorted(set(_ALIASED) - helper)) or "none"
    return (
        "the alias table of this gate and the one style_default reads have "
        f"drifted apart: the helper knows {missing} and this does not; this "
        f"refuses {extra} and the helper does not."
    )


def main() -> int:
    """Report every style default that could collide with its own alias."""
    drift = _aliases_agree()
    if drift is not None:
        print(f"scripts/{Path(__file__).name}: {drift}")
        return 1
    bad = 0
    files = 0
    for path in sorted(_ROOT.rglob("*.py")):
        files += 1
        for line, why in _findings(path):
            bad += 1
            relative = path.relative_to(_REPO)
            print(f"{relative}:{line}: {why}")
    if bad:
        print()
        print(
            f"{bad} style default(s) would collide with what the caller passes. "
            "Use style_default, style_get, style_pop or styled from "
            "phonometry._plot.common, each of which lets the caller's keyword "
            "win under either spelling of the property."
        )
        return 1
    print(
        "No style default collides with its alias or with the caller's own "
        f"keyword: {files} modules."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
