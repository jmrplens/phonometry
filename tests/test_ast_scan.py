#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What a scope binds of its own, as the guards that follow a call read it.

``scripts/ast_scan.py`` reads, once for every guard that looks a name up as
Python does, which names a function, a lambda, a class body, a comprehension
or the module binds itself, and which scope a name read at a node reaches.
These are the rules each of those guards got wrong on its own before it
read them here: a comprehension's loop target is the comprehension's, an
assignment expression in it binds the scope around it, a nested function or
lambda binds for itself, a class body is no scope of its methods, and a
``global`` or ``nonlocal`` statement sends the name out.
"""

from __future__ import annotations

import ast
import pathlib
import sys
import textwrap

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import ast_scan

_SOURCE = """
def outer(keep, x):
    global shared
    seen = [keep for keep in x]
    total = [(last := item) for item in x]
    shared = 1

    def inner():
        hidden = 1
        return hidden

    class Holder:
        keep = 2

        def method(self):
            return keep()

    def through_global():
        global keep
        return keep()

    def through_nonlocal():
        nonlocal x
        return x()

    show = lambda: (lent := keep)
    return [keep(i) for keep in x], keep(1), Holder.keep, [keep(j) for j in keep()]
"""


def _outer() -> ast.FunctionDef:
    tree = ast.parse(textwrap.dedent(_SOURCE))
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    return function


def _calls(root: ast.AST, name: str) -> list[ast.Call]:
    calls = [
        node
        for node in ast.walk(root)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
    ]
    return sorted(calls, key=lambda call: (call.lineno, call.col_offset))


def test_a_scope_binds_what_runs_in_it_alone() -> None:
    names = ast_scan.own_names(_outer())
    assert names.parameters == {"keep", "x"}
    assert names.defined == {"inner", "Holder", "through_global", "through_nonlocal"}
    # The walrus of the comprehension binds here; its loop targets, and what
    # the nested function and the lambda bind, do not.
    assert names.stored == {"seen", "total", "last", "shared", "show"}
    assert names.declared_global == {"shared"}
    assert not names.binds("shared")
    assert not names.binds("item")
    assert not names.binds("hidden")
    assert not names.binds("lent")


def test_a_name_reaches_the_scope_python_reads_it_in() -> None:
    outer = _outer()
    method, through_global, comprehension, beside, element, first = _calls(
        outer, "keep"
    )
    # A method does not see its class body: the parameter of ``outer``.
    assert ast_scan.binding_of(outer, method, "keep")[0] == "binding"
    assert ast_scan.binding_of(outer, through_global, "keep") == ("global", None)
    how, scope = ast_scan.binding_of(outer, comprehension, "keep")
    assert (how, type(scope)) == ("binding", ast.ListComp)
    assert ast_scan.binding_of(outer, beside, "keep") == ("binding", outer)
    # A comprehension that binds another name passes this one on, and its
    # first iterable runs in the scope around it.
    assert ast_scan.binding_of(outer, element, "keep") == ("binding", outer)
    assert ast_scan.binding_of(outer, first, "keep") == ("binding", outer)
    (nonlocal_call,) = _calls(outer, "x")
    assert ast_scan.binding_of(outer, nonlocal_call, "x") == ("binding", outer)


def test_a_global_name_the_scope_rebinds_is_no_module_function() -> None:
    """``global keep`` with ``keep = make()`` in the same scope rebinds the module's
    name: a call may reach what the scope put there, not the module's function.
    """
    tree = ast.parse("def f():\n    global keep\n    keep = make()\n    keep()\n")
    function = tree.body[0]
    (call,) = _calls(function, "keep")
    assert ast_scan.own_names(function).rebinds("keep")
    assert ast_scan.binding_of(function, call, "keep") == ("binding", function)


def test_a_name_bound_two_ways_names_no_one_binding() -> None:
    tree = ast.parse("def f():\n    def g(): pass\n    g = make()\n")
    function = tree.body[0]
    assert ast_scan.own_names(function).how("g") == "binding"
