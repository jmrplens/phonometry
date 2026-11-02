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
    assert ast_scan.binding_of(outer, method, "keep") == ("binding", outer)
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


_LIVE = """
def first(x):
    return x


def first(x):
    return x.copy()


if FAST:

    def branch(x):
        return x

else:

    def branch(x):
        return x.copy()


def then(x):
    return x


if FAST:

    def then(x):
        return x.copy()


try:

    def tried(x):
        return x

    def tried(x):
        return x.copy()

except ImportError:
    pass


def caller(values):
    def helper(v):
        return v.copy()

    if values:

        def helper(v):
            return v

    a = helper(values)

    def helper(v):
        return v + 1

    b = helper(values)
    if values:

        def other(v):
            return v

        c = other(values)
    else:

        def other(v):
            return v.copy()

        d = other(values)
    e = other(values)
    for item in values:
        f = late(item)

        def late(v):
            return v

    g = [helper(item) for item in values]
"""


def _definitions(root: ast.AST, name: str) -> list[ast.FunctionDef]:
    """Every ``def`` of *name* under *root*, in the order of the source."""
    found = [
        node
        for node in ast.walk(root)
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    return sorted(found, key=lambda node: node.lineno)


def _call_stored_in(root: ast.AST, target: str) -> ast.Call:
    """The call whose result the assignment to *target* stores."""
    for node in ast.walk(root):
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == target
        ):
            found = [
                part for part in ast.walk(node.value) if isinstance(part, ast.Call)
            ]
            return found[0]
    raise AssertionError(target)


def test_a_later_def_replaces_an_earlier_one_where_it_always_runs_after() -> None:
    """Once the module has run, a name holds the ``def`` no later one replaces.

    A later ``def`` in the same block replaces an earlier one; one in each
    branch of an ``if`` is either; one inside an ``if`` after an
    unconditional one may or may not have replaced it; and two in the body
    of a ``try`` are both kept, since an exception may leave the first.
    """
    tree = ast.parse(textwrap.dedent(_LIVE))
    first, second = _definitions(tree, "first")
    assert ast_scan.live_bindings(tree, [first, second]) == [second]
    for name in ("branch", "then", "tried"):
        both = _definitions(tree, name)
        assert ast_scan.live_bindings(tree, both) == both, name


def test_a_call_reaches_the_defs_that_may_run_before_it() -> None:
    """A call reaches each ``def`` that may have run before it and that no
    later one replaced on the way: the one written last before it, and one
    inside an ``if`` written after that one.

    The function-local reading kept the last ``def`` before the call in a
    block the call sits in alone, so a ``def`` inside an ``if`` between it
    and the call, which may have run, was never read.
    """
    tree = ast.parse(textwrap.dedent(_LIVE))
    caller = next(node for node in tree.body if getattr(node, "name", "") == "caller")
    one, two, three = _definitions(caller, "helper")
    either, other = _definitions(caller, "other")
    (late,) = _definitions(caller, "late")
    expected = {
        "a": [one, two],
        "b": [three],
        "c": [either],
        "d": [other],
        "e": [either, other],
        "f": [late],
        "g": [three],
    }
    for target, reached in expected.items():
        call = _call_stored_in(caller, target)
        assert isinstance(call.func, ast.Name)
        bindings = _definitions(caller, call.func.id)
        assert ast_scan.live_bindings(tree, bindings, call) == reached, target


def _held_at(source: str, name: str, *, call: str | None = None) -> list[int]:
    """The ``def``s of *name* in *source* the name may hold, by the number
    each returns: at the call stored in *call* (the one call of *name* when
    it is empty), or once the module has run.
    """
    tree = ast.parse(textwrap.dedent(source))
    bindings = _definitions(tree, name)
    point = _call_stored_in(tree, call) if call else None
    if call == "":
        point = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == name
        )
    live = ast_scan.live_bindings(tree, bindings, point)
    values = []
    for binding in live:
        returned = binding.body[0]
        assert isinstance(returned, ast.Return)
        assert isinstance(returned.value, ast.Constant)
        values.append(returned.value.value)
    return values


def test_a_later_def_in_a_finally_or_an_else_replaces_an_earlier_one() -> None:
    """Only the body of a ``try`` may be left between two ``def``s by an
    exception the ``try`` catches: its ``finally`` and its ``else`` run on.

    Every block of a ``try`` was read as the body, so two ``def``s of one name
    in a ``finally`` were both kept and a guard read the union of the two.
    """
    finally_block = """
    try:
        pass
    finally:

        def helper():
            return 1

        def helper():
            return 2
    """
    else_block = """
    try:
        pass
    except ValueError:
        pass
    else:

        def helper():
            return 1

        def helper():
            return 2
    """
    handler_then_finally = """
    try:
        pass
    except ValueError:

        def helper():
            return 1

        fail()

        def helper():
            return 2

    finally:
        a = helper()
    """
    assert _held_at(finally_block, "helper") == [2]
    assert _held_at(else_block, "helper") == [2]
    assert _held_at(handler_then_finally, "helper", call="a") == [1, 2]


def test_a_def_may_be_skipped_by_what_leaves_the_block_between() -> None:
    """A later ``def`` replaces an earlier one only where nothing between the
    two leaves their block and still reaches the point: a ``try`` or a
    ``with`` around them, however deep, a ``break`` or a ``continue``.
    """
    nested_try = """
    try:
        if FAST:

            def helper():
                return 1

            fail()

            def helper():
                return 2

    except ValueError:
        pass
    a = helper()
    """
    within_with = """
    with suppress(ValueError):

        def helper():
            return 1

        fail()

        def helper():
            return 2

    a = helper()
    """
    broken = """
    for item in items:

        def helper():
            return 1

        if item:
            break

        def helper():
            return 2

    a = helper()
    """
    continued = """
    for item in items:

        def helper():
            return 1

        if item:
            continue

        def helper():
            return 2

    a = helper()
    """
    for source in (nested_try, within_with, broken, continued):
        assert _held_at(source, "helper", call="a") == [1, 2], source


def test_a_def_after_a_call_in_a_loop_reaches_it_on_the_next_turn() -> None:
    """A ``def`` written after a call in the body of a loop runs before that
    call on the next turn, so the call may reach it as well as the one before
    the loop; one written before the call in the body always runs first.

    A binding after the call was read only when none ran before it, so the
    call kept the ``def`` before the loop alone.
    """
    after = """
    def helper():
        return 1

    for item in items:
        a = helper()

        def helper():
            return 2
    """
    before_each_turn = """
    for item in items:

        def helper():
            return 1

        a = helper()

        def helper():
            return 2
    """
    replaced_each_turn = """
    for item in items:
        a = helper()

        def helper():
            return 1

        def helper():
            return 2
    """
    inner_loop = """
    for row in rows:

        def helper():
            return 1

        for item in row:
            a = helper()

            def helper():
                return 2
    """
    while_test = """
    def helper():
        return 1

    while helper():

        def helper():
            return 2
    """
    assert _held_at(after, "helper", call="a") == [1, 2]
    assert _held_at(before_each_turn, "helper", call="a") == [1]
    assert _held_at(replaced_each_turn, "helper", call="a") == [2]
    assert _held_at(inner_loop, "helper", call="a") == [1, 2]
    assert _held_at(while_test, "helper", call="") == [1, 2]


def test_block_statements_reads_every_block_of_every_compound_statement() -> None:
    """The one walker the guards share reads each block a compound statement
    holds, in the order of the source, and nothing of any other node.
    """
    source = """
    if a:
        b1 = 1
    else:
        b2 = 2
    for x in y:
        b3 = 3
    else:
        b4 = 4
    async def f():
        async for x in y:
            b5 = 5
        async with z:
            b6 = 6
    while a:
        b7 = 7
    try:
        b8 = 8
    except* ValueError:
        b9 = 9
    else:
        b10 = 10
    finally:
        b11 = 11
    with z:
        b12 = 12
    match a:
        case 1:
            b13 = 13
        case _:
            b14 = 14
    """
    tree = ast.parse(textwrap.dedent(source))
    found = []
    for node in ast.walk(tree):
        for statement in ast_scan.block_statements(node):
            if isinstance(statement, ast.Assign):
                target = statement.targets[0]
                assert isinstance(target, ast.Name)
                found.append(target.id)
    assert sorted(found, key=lambda name: int(name[1:])) == [
        f"b{index}" for index in range(1, 15)
    ]
    function = next(
        node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
    )
    assert ast_scan.block_statements(function) == []
