#!/usr/bin/env python3
"""Fail on a style default that ignores the other spelling of its property.

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

Only the aliased properties are refused. ``kwargs.setdefault("label", ...)`` and
``kwargs.setdefault("marker", ...)`` are fine, because matplotlib gives those no
second name, and this says nothing about them. The read-back and literal shapes
are refused only on a mapping that is the function's own ``**kwargs``: a local
dictionary the caller never sees may hold whatever it likes.

Exit status 0 when no aliased property is defaulted or read back by hand,
1 otherwise.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

#: The repository, for paths a reader can click.
_REPO = Path(__file__).resolve().parent.parent

#: The package whose renderers forward keyword arguments to artists.
_ROOT = _REPO / "src" / "phonometry"

#: Every spelling of every property matplotlib aliases, long and short. Taken
#: from ``_STYLE_ALIASES`` in ``_plot/common.py``, which is the table
#: :func:`style_default` itself reads, so the two cannot drift apart.
_ALIASED: frozenset[str] = frozenset(
    {
        "color",
        "c",
        "linestyle",
        "ls",
        "linewidth",
        "lw",
        "markeredgecolor",
        "mec",
        "markeredgewidth",
        "mew",
        "markerfacecolor",
        "mfc",
        "markersize",
        "ms",
    }
)


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
    return sorted(found)


def _aliases_agree() -> str | None:
    """Whether this gate's table still matches the one ``style_default`` reads.

    The gate refuses exactly the properties the helper knows how to default. If
    someone teaches the helper an eighth alias and not this file, the gate would
    go on passing the very line the helper was extended to replace, so the two
    tables are compared rather than trusted.
    """
    sys.path.insert(0, str(_REPO / "src"))
    from phonometry._plot.common import _STYLE_ALIASES

    helper = set(_STYLE_ALIASES) | set(_STYLE_ALIASES.values())
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
            f"{bad} style default(s) would collide with the caller's own "
            "spelling. Use style_default, style_get, style_pop or styled from "
            "phonometry._plot.common, each of which reads and writes both "
            "spellings of the property."
        )
        return 1
    print(f"No style default collides with its alias: {files} modules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
