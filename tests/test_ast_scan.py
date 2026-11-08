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

import pytest

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


def _line(node: ast.AST) -> int:
    """The line a binding node the scanner hands back is written on."""
    assert isinstance(node, ast.stmt | ast.expr)
    return node.lineno


def _calls(root: ast.AST, name: str) -> list[ast.Call]:
    calls = [
        node
        for node in ast.walk(root)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
    ]
    return sorted(calls, key=lambda call: (call.lineno, call.col_offset))


def test_an_argument_lands_from_the_lowest_place_the_stars_before_it_allow() -> None:
    """A ``*`` argument may hand nothing, so the lowest place an argument may
    fill is the number of plain arguments before it, and a star, and every
    argument after one, may fill any place from there on; one with no star
    at or before it fills its own place alone.
    """
    call = ast.parse("f(a, *head, 1, value, *rest, last)", mode="eval").body
    assert isinstance(call, ast.Call)
    assert ast_scan.argument_places(call.args) == [
        (0, False),
        (1, True),
        (1, True),
        (2, True),
        (3, True),
        (3, True),
    ]
    plain = ast.parse("f(a, b)", mode="eval").body
    assert isinstance(plain, ast.Call)
    assert ast_scan.argument_places(plain.args) == [(0, False), (1, False)]


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


_HOMES = """
def outer(items):
    [(last := item) for item in items]
    pattern = "a"

    def strict():
        nonlocal pattern
        pattern = "b"

    def setup():
        global shared
        shared = "c"

    class Holder:
        pattern = "d"

        def method(self):
            return pattern
"""


def test_a_write_or_a_read_reaches_the_scope_python_binds_the_name_in() -> None:
    """The scope whose binding a name written or read at a node reaches: the
    function around a comprehension for ``:=``, the function that binds a
    name declared ``nonlocal``, the module for one declared ``global`` or
    bound nowhere, and never a class body from a method.
    """
    tree = ast.parse(textwrap.dedent(_HOMES))
    outer = tree.body[0]
    assert isinstance(outer, ast.FunctionDef)
    stores = {
        (node.id, node.lineno): node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }
    walrus, nonlocal_write = stores["last", 3], stores["pattern", 8]
    global_write, read_in_method = stores["shared", 12], stores["pattern", 18]
    assert ast_scan.binding_scope(tree, walrus, "last") is outer
    assert ast_scan.binding_scope(tree, nonlocal_write, "pattern") is outer
    assert ast_scan.binding_scope(tree, global_write, "shared") is tree
    assert ast_scan.binding_scope(tree, read_in_method, "pattern") is outer
    assert ast_scan.binding_scope(tree, read_in_method, "nowhere") is tree


def test_forgetting_the_trees_empties_what_the_scopes_keep() -> None:
    """A guard that reads each file once lets go of its tree when it is done."""
    tree = ast.parse(textwrap.dedent(_HOMES))
    ast_scan.binding_scope(tree, tree.body[0], "items")
    assert ast_scan.own_names.cache_info().currsize > 0
    ast_scan.forget_trees()
    assert ast_scan.own_names.cache_info().currsize == 0


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


def test_a_default_holds_no_binding_of_its_scope_before_any_has_run() -> None:
    """A ``def``'s default runs where it is written: before any binding of
    the name at the top of the module, it holds none of them (the builtin),
    after one it holds that one, and a later one replaces neither.

    :func:`ast_scan.live_bindings` takes every binding for what a read before
    them may meet, which a call inside a function may; a default never does.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            def early(levels, float=float):
                return float(levels)

            float = print

            def late(levels, float=float):
                return float(levels)

            float = str
            """
        )
    )
    first, second = ast_scan.bindings_by_name(tree)["float"]
    early, late = (
        node.args.defaults[0] for node in tree.body if isinstance(node, ast.FunctionDef)
    )
    assert ast_scan.held_before(tree, [first, second], early) == []
    assert ast_scan.held_before(tree, [first, second], late) == [first]
    assert ast_scan.live_bindings(tree, [first, second], early) == [first, second]


def test_a_default_holds_no_binding_only_the_type_checker_makes() -> None:
    """A binding an ``if TYPE_CHECKING:`` block holds never runs, so a default
    read after it holds none of the scope's bindings, at the top of a module
    and in a class body, even where nothing else binds the name; what reads
    annotations through :func:`ast_scan.live_bindings` still finds it.

    :func:`ast_scan.held_before` kept the block's binding whenever it was the
    only one, as :func:`ast_scan.live_bindings` does, so a caller that handed
    it every binding of the name read ``open`` as the import the type
    checker reads instead of the builtin.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                from os.path import exists as open

            def read(path, opener=open):
                return opener(path)

            class Reader:
                if TYPE_CHECKING:
                    from os.path import exists as open

                def read(self, path, opener=open):
                    return opener(path)
            """
        )
    )
    reader = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    for scope in (tree, reader):
        (binding,) = ast_scan.bindings_by_name(scope)["open"]
        function = next(
            node for node in scope.body if isinstance(node, ast.FunctionDef)
        )
        default = function.args.defaults[0]
        assert ast_scan.held_before(tree, [binding], default) == []
        assert ast_scan.live_bindings(tree, [binding], default) == [binding]
    ast_scan.forget_trees()


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
    values: list[int] = []
    for binding in live:
        returned = binding.body[0]
        assert isinstance(returned, ast.Return)
        assert isinstance(returned.value, ast.Constant)
        assert isinstance(returned.value.value, int)
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


def test_a_def_replaces_an_earlier_one_for_a_read_later_in_its_own_block() -> None:
    """A read later in the block of the later ``def`` is reached only through
    it: what leaves the block between the two ``def``s, an exception a
    ``try`` or a ``with`` around them catches, a ``break`` or a
    ``continue``, leaves the read behind too.

    The reading asked only whether the block could be left, and kept the
    earlier ``def`` at a read the later one always runs before.
    """
    within_try = """
    try:

        def helper():
            return 1

        fail()

        def helper():
            return 2

        a = helper()
    except ValueError:
        pass
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
    deeper = """
    with suppress(ValueError):

        def helper():
            return 1

        fail()

        def helper():
            return 2

        if item:
            a = helper()
    """
    for source in (within_try, within_with, continued, deeper):
        assert _held_at(source, "helper", call="a") == [2], source


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


def _met_from(source: str, name: str, reader: str) -> list[int]:
    """The ``def``s of *name* in *source* that a call of the function
    *reader* may meet, by the number each returns.
    """
    tree = ast.parse(textwrap.dedent(source))
    (point,) = _definitions(tree, reader)
    met = ast_scan.bindings_from(tree, _definitions(tree, name), point)
    values: list[int] = []
    for binding in met:
        returned = binding.body[0]
        assert isinstance(returned, ast.Return)
        assert isinstance(returned.value, ast.Constant)
        assert isinstance(returned.value.value, int)
        values.append(returned.value.value)
    return values


def test_a_function_meets_every_binding_from_its_def_on() -> None:
    """A function reads a name of the scope around it when it is called,
    which may be at once or after a later binding: it meets the binding that
    stands where the ``def`` runs and every one that may run after it.

    Not one that a later binding replaces before the ``def``, nor one in the
    other branch of the ``if`` that holds the ``def``; one on an earlier
    turn of a loop, called between two bindings on the next turn, is met.
    """
    later = """
    def helper():
        return 1

    def reader():
        return helper()

    def helper():
        return 2
    """
    replaced_before = """
    def helper():
        return 1

    def helper():
        return 2

    def reader():
        return helper()
    """
    other_branch = """
    def helper():
        return 0

    if FAST:

        def reader():
            return helper()

    else:

        def helper():
            return 1
    """
    next_turn = """
    for item in items:

        def helper():
            return 1

        if item:
            early = reader()

        def helper():
            return 2

        def reader():
            return helper()
    """
    assert _met_from(later, "helper", "reader") == [1, 2]
    assert _met_from(replaced_before, "helper", "reader") == [2]
    assert _met_from(other_branch, "helper", "reader") == [0]
    assert _met_from(next_turn, "helper", "reader") == [1, 2]
    tree = ast.parse(textwrap.dedent(later))
    bindings = _definitions(tree, "helper")
    assert ast_scan.bindings_from(tree, bindings, None) == [bindings[1]]


def test_a_call_in_a_nested_scope_is_read_where_that_scope_runs() -> None:
    """A call written inside a function, a lambda or a generator expression
    reads the name when that runs, so it may meet every ``def`` from where
    the function is written on; one in a class body, a list comprehension
    or a default runs where it is written, and meets the one standing there.

    The call was read as if it stood in the module at the place it holds in
    its own function, so its index there was set against the module's, and
    a lambda or a generator was read where it is written.
    """
    source = textwrap.dedent(
        """
        def helper():
            return 1

        def reader():
            first = 1
            second = 2
            third = 3
            return helper()

        later = lambda: helper()
        lazy = (helper() for _ in range(2))
        each = [helper() for _ in range(2)]

        class Holder:
            value = helper()

        def defaulted(x=helper()):
            return x

        def helper():
            return 2
        """
    )
    tree = ast.parse(source)
    bindings = _definitions(tree, "helper")
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "helper"
    ]
    met = {}
    for call in sorted(calls, key=lambda node: node.lineno):
        values = []
        for binding in ast_scan.live_bindings(tree, bindings, call):
            returned = binding.body[0]
            assert isinstance(returned, ast.Return)
            assert isinstance(returned.value, ast.Constant)
            values.append(returned.value.value)
        met[call.lineno] = values
    assert met == {
        9: [1, 2], 11: [1, 2], 12: [1, 2], 13: [1], 16: [1], 18: [1],
    }  # fmt: skip


def test_bindings_by_name_lists_every_binding_of_a_scope_in_source_order() -> None:
    """Each name a scope binds, with the import, the ``def``, the assignment
    and the other bindings of it in the order of the source; a function's
    body is its own, and a name it declares ``global`` is the module's.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            from pkg import helper
            def helper():
                global late
                late = 1
                inner = 2
            helper = None
            for helper in items:
                pass
            try:
                pass
            except ValueError as helper:
                pass
            """
        )
    )
    found = ast_scan.bindings_by_name(tree)
    assert sorted(found) == ["helper"]
    assert [type(node).__name__ for node in found["helper"]] == [
        "ImportFrom", "FunctionDef", "Name", "Name", "ExceptHandler",
    ]  # fmt: skip
    function = tree.body[1]
    assert sorted(ast_scan.bindings_by_name(function)) == ["inner"]


def test_an_annotation_without_a_value_binds_no_value() -> None:
    """``flag: type`` binds nothing: the import before it is what the name holds.

    A function that annotates a name makes it its own all the same, as
    Python does, and so does a class body; the module does not, and none of
    them counts the annotation among the bindings of the name.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            from numpy import bool_ as flag
            flag: type

            def f():
                from numpy import bool_ as kind
                kind: type
                own: int

            class Holder:
                field: int
            """
        )
    )
    found = ast_scan.bindings_by_name(tree)
    assert [type(node).__name__ for node in found["flag"]] == ["ImportFrom"]
    assert ast_scan.own_names(tree).how("flag") == "import"
    function = tree.body[2]
    assert [type(n).__name__ for n in ast_scan.bindings_by_name(function)["kind"]] == [
        "ImportFrom"
    ]
    assert "own" not in ast_scan.bindings_by_name(function)
    names = ast_scan.own_names(function)
    assert names.how("kind") == "import"
    assert names.binds("own")
    assert ast_scan.own_names(tree.body[3]).binds("field")
    assert "field" not in ast_scan.bindings_by_name(tree.body[3])


def test_a_module_name_stands_for_what_a_function_binds_it_to_under_global() -> None:
    """A function, a method or a class body that declares a module name
    ``global`` and binds it may run at any time, so what it binds the name
    to may stand once the module has run, beside the bindings at the top
    that :func:`ast_scan.live_bindings` keeps; a name only such a function
    binds stands for that alone, and a local of the same spelling is not
    the module's.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            from ._checked import read
            read = read

            def swap():
                global read, extra
                read = loose
                from ._other import extra

            class Holder:
                def method(self):
                    global read
                    def read(path):
                        return path

            def own():
                read = 1
            """
        )
    )
    inside = ast_scan.global_bindings(tree)
    assert sorted(inside) == ["extra", "read"]
    assert [type(node).__name__ for node in inside["read"]] == ["Name", "FunctionDef"]
    standing = ast_scan.standing_bindings(tree)
    assert [(type(node).__name__, _line(node)) for node in standing["read"]] == [
        ("Name", 3), ("Name", 7), ("FunctionDef", 13),
    ]  # fmt: skip
    assert [type(node).__name__ for node in standing["extra"]] == ["ImportFrom"]


def test_a_module_without_a_global_statement_is_not_read_for_one() -> None:
    """With no ``global`` anywhere in the module no scope sends a name to it,
    and no scope is read to find one.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            def outer():
                read = 1
                def inner():
                    nonlocal read
                    read = 2
                return inner

            class Holder:
                read = 3
            """
        )
    )
    read_before = ast_scan.own_names.cache_info().misses
    assert ast_scan.global_bindings(tree) == {}
    assert ast_scan.own_names.cache_info().misses == read_before


def test_a_binding_left_out_stands_neither_at_the_top_nor_under_global() -> None:
    """What a caller leaves out of a module's bindings is left out wherever it
    is written: of what the top of the module binds, and of what a function
    binds under ``global``.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            from json import dumps as read

            if LEFT_OUT:
                from json import loads as read

            def swap():
                global read, extra
                if LEFT_OUT:
                    from json import load as read
                    from json import load as extra
                from json import JSONDecoder as read
            """
        )
    )
    left_out = {
        id(node)
        for statement in ast.walk(tree)
        if isinstance(statement, ast.If)
        for child in statement.body
        for node in ast.walk(child)
    }
    standing = ast_scan.standing_bindings(tree, left_out)
    assert [_line(node) for node in standing["read"]] == [2, 12]
    assert standing["extra"] == []
    assert [_line(node) for node in ast_scan.standing_bindings(tree)["read"]] == [
        2, 5, 10, 12,
    ]  # fmt: skip


def test_a_binding_for_the_type_checker_stands_beside_none_that_runs() -> None:
    """What an ``if TYPE_CHECKING:`` block holds never runs, so it is no value
    a name may hold beside a binding that does: not in a function under
    ``global``, not at the top of a module and not in the block's ``else``,
    which is what runs. A name nothing else binds keeps it, for what reads
    annotations through it.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            from json import dumps as beside

            if TYPE_CHECKING:
                from json import loads as beside
                from json import load as alone

            if typing.TYPE_CHECKING:
                def either():
                    return 1
            else:
                def either():
                    return 2

            def swap():
                global beside, inside
                if TYPE_CHECKING:
                    from json import load as beside
                    inside = 1
            """
        )
    )
    assert ast_scan.global_bindings(tree) == {}
    swap = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "swap"
    )
    either = ast_scan.bindings_by_name(tree)["either"]
    assert [_line(node) for node in ast_scan.bindings_from(tree, either, swap)] == [12]
    standing = ast_scan.standing_bindings(tree)
    assert [_line(node) for node in standing["beside"]] == [2]
    assert [_line(node) for node in standing["alone"]] == [6]
    assert [_line(node) for node in standing["either"]] == [12]
    assert "inside" not in standing
    left_out = ast_scan.for_the_type_checker(tree)
    assert ast_scan.standing_bindings(tree, left_out)["alone"] == []


def test_a_reader_of_annotations_reads_the_block_and_not_its_else() -> None:
    """A type checker reads what the program never runs and leaves out the
    ``else``, so a reader of annotations takes the block, while what runs stays
    what a reader of the program takes; a binding a function makes under
    ``global`` runs for both.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            if TYPE_CHECKING:
                Mode = 1
            else:
                Mode = 2

            if TYPE_CHECKING:
                from json import dumps as lazy
                from json import dumps as swapped

            def load():
                global lazy, swapped
                from json import loads as lazy
                swapped = 3
            """
        )
    )
    program = ast_scan.standing_bindings(tree)
    assert [_line(node) for node in program["Mode"]] == [5]
    assert [_line(node) for node in program["lazy"]] == [13]
    assert [_line(node) for node in program["swapped"]] == [14]
    read = ast_scan.standing_bindings(tree, annotations=True)
    assert [_line(node) for node in read["Mode"]] == [3]
    assert [_line(node) for node in read["lazy"]] == [8, 13]
    assert [_line(node) for node in read["swapped"]] == [9, 14]


def test_the_body_of_a_function_s_if_type_checking_block_is_emptied() -> None:
    """What a function's ``if TYPE_CHECKING:`` holds goes and its ``else`` stays,
    at any depth of the function. The block at the top of a module and in a class
    body stay, where a guard reads annotations and a declared constructor.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            if TYPE_CHECKING:
                from a import b

            class Record:
                if TYPE_CHECKING:
                    def __init__(self, x): ...

            def f(x):
                for _ in x:
                    if TYPE_CHECKING:
                        y = 1
                    else:
                        y = 2
                return y
            """
        )
    )
    ast_scan.empty_type_checking_bodies(tree)
    source = ast.unparse(tree)
    assert "from a import b" in source
    assert "def __init__" in source
    assert "y = 1" not in source
    assert "y = 2" in source


def test_a_tree_whose_functions_test_no_flag_comes_back_as_it_was(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A tree whose functions hold no test on ``TYPE_CHECKING`` is handed back
    untouched, its blocks at the top and in a class body with it, and no function
    of it is walked on its own; a conditional expression on the flag in a
    function's default is still emptied.
    """
    walked: list[ast.AST] = []
    scope_nodes = ast_scan.scope_nodes

    def counted(scope: ast.AST) -> list[ast.AST]:
        walked.append(scope)
        return scope_nodes(scope)

    monkeypatch.setattr(ast_scan, "scope_nodes", counted)
    source = textwrap.dedent(
        """
        if TYPE_CHECKING:
            from a import b

        class Record:
            if TYPE_CHECKING:
                def __init__(self, x): ...

        def f(x, y=1 if enabled else 2):
            if x:
                return y
            return lambda: x if y else None
        """
    )
    tree = ast.parse(source)
    written = ast.dump(tree)
    assert ast_scan.empty_type_checking_bodies(tree) is tree
    assert ast.dump(tree) == written
    assert walked == []

    tree = ast.parse("def f(x=b if TYPE_CHECKING else c):\n    return x\n")
    ast_scan.empty_type_checking_bodies(tree)
    assert ast.unparse(tree).startswith("def f(x=None if TYPE_CHECKING else c)")


@pytest.mark.parametrize(
    ("test", "never", "runs"),
    [
        ("TYPE_CHECKING", "first", "second"),
        ("typing.TYPE_CHECKING", "first", "second"),
        ("not TYPE_CHECKING", "second", "first"),
        ("not typing.TYPE_CHECKING", "second", "first"),
    ],
)
def test_a_test_on_type_checking_says_which_branch_runs(
    test: str, never: str, runs: str
) -> None:
    """``if not TYPE_CHECKING:`` is the same test with its branches swapped, in a
    statement and in a conditional expression: what the program runs is one branch
    and what the type checker alone reads the other.
    """
    tree = ast.parse(f"if {test}:\n    first = 1\nelse:\n    second = 2\n")
    statement = tree.body[0]
    assert isinstance(statement, ast.If)
    assert ast_scan.is_type_checking_block(statement, tree)
    written = {name.id: name for name in ast.walk(tree) if isinstance(name, ast.Name)}
    assert id(written[never]) in ast_scan.for_the_type_checker(tree)
    assert id(written[runs]) not in ast_scan.for_the_type_checker(tree)
    assert id(written[runs]) in ast_scan.for_the_program(tree)
    assert id(written[never]) not in ast_scan.for_the_program(tree)
    running = ast_scan.what_runs(statement)
    names = [
        line.targets[0].id
        for line in running
        if isinstance(line, ast.Assign) and isinstance(line.targets[0], ast.Name)
    ]
    assert len(running) == 1
    assert names == [runs]

    tree = ast.parse(f"held = first if {test} else second\n")
    read = {
        name.id: name
        for name in ast.walk(tree)
        if isinstance(name, ast.Name) and isinstance(name.ctx, ast.Load)
    }
    assert id(read[never]) in ast_scan.for_the_type_checker(tree)
    assert id(read[runs]) not in ast_scan.for_the_type_checker(tree)


@pytest.mark.parametrize(
    "test",
    ["TYPE_CHECKING or enabled", "enabled and TYPE_CHECKING", "not enabled", "enabled"],
)
def test_any_other_test_says_nothing_of_either_branch(test: str) -> None:
    """Only the name itself, or its negation, decides a branch: ``TYPE_CHECKING or
    enabled`` runs whenever ``enabled`` is true.
    """
    tree = ast.parse(f"if {test}:\n    first = 1\nelse:\n    second = 2\n")
    assert not ast_scan.is_type_checking_block(tree.body[0], tree)
    assert ast_scan.for_the_type_checker(tree) == frozenset()
    assert ast_scan.for_the_program(tree) == frozenset()


_BRANCHES_TESTED = (
    "if {test}:\n    first = 1\nelse:\n    second = 2\n\n"
    "def f():\n    if {test}:\n        third = 3\n    return 4 if {test} else 5\n"
)


@pytest.mark.parametrize(
    ("prelude", "test"),
    [
        ("TYPE_CHECKING = True\n", "TYPE_CHECKING"),
        ("from settings import TYPE_CHECKING\n", "TYPE_CHECKING"),
        ("from settings import *\n", "TYPE_CHECKING"),
        ("import os as typing\n", "typing.TYPE_CHECKING"),
        (
            "import typing\n\ndef load(typing):\n    return typing\n",
            "typing.TYPE_CHECKING",
        ),
        (
            "from typing import TYPE_CHECKING\n\ndef f(TYPE_CHECKING=True): ...\n",
            "TYPE_CHECKING",
        ),
        (
            "from typing import TYPE_CHECKING\n\n"
            "def switch():\n    global TYPE_CHECKING\n    TYPE_CHECKING = True\n",
            "TYPE_CHECKING",
        ),
        ("settings = load()\n", "settings.TYPE_CHECKING"),
    ],
)
def test_a_name_the_module_binds_to_anything_else_decides_no_branch(
    prelude: str, test: str
) -> None:
    """``TYPE_CHECKING`` is the flag only where every binding of the name, in
    any scope of the module, is an import of it from ``typing`` (or the
    constant ``False``): a module that binds it to anything else, to ``True``
    above all, may run either branch, and so may one whose ``typing`` is not
    the module. Neither branch is taken for what never runs, and no body of a
    function is emptied.
    """
    tree = ast.parse(prelude + _BRANCHES_TESTED.format(test=test))
    assert ast_scan.for_the_type_checker(tree) == frozenset()
    assert ast_scan.for_the_program(tree) == frozenset()
    source = ast.unparse(ast_scan.empty_type_checking_bodies(tree))
    assert "third = 3" in source
    assert f"4 if {test} else 5" in source
    ast_scan.forget_trees()


@pytest.mark.parametrize(
    ("prelude", "test"),
    [
        ("from typing import TYPE_CHECKING\n", "TYPE_CHECKING"),
        ("from typing import TYPE_CHECKING as CHECKING\n", "CHECKING"),
        ("from typing_extensions import TYPE_CHECKING\n", "TYPE_CHECKING"),
        ("import typing as t\n", "t.TYPE_CHECKING"),
        ("import typing_extensions\n", "typing_extensions.TYPE_CHECKING"),
        (
            "try:\n    from typing import TYPE_CHECKING\n"
            "except ImportError:\n    TYPE_CHECKING = False\n",
            "TYPE_CHECKING",
        ),
    ],
)
def test_the_flag_of_typing_decides_its_branches_under_any_name(
    prelude: str, test: str
) -> None:
    """An import of the flag under another name, of ``typing`` under another
    name, or of ``typing_extensions``, holds the flag all the same, and so does
    the fallback that assigns ``False`` to it: what the block holds never runs.
    """
    tree = ast.parse(prelude + _BRANCHES_TESTED.format(test=test))
    written = {
        name.id: name
        for name in ast.walk(tree)
        if isinstance(name, ast.Name) and isinstance(name.ctx, ast.Store)
    }
    assert id(written["first"]) in ast_scan.for_the_type_checker(tree)
    assert id(written["second"]) in ast_scan.for_the_program(tree)
    source = ast.unparse(ast_scan.empty_type_checking_bodies(tree))
    assert "third = 3" not in source
    assert "4 if" not in source
    ast_scan.forget_trees()


def test_a_scope_read_as_a_tree_of_its_own_reads_the_flag_of_its_module() -> None:
    """A guard that hands a function as the tree to read reads what the
    module binds the flag to, once the module has been read: a module that
    rebinds it leaves the function's block running.
    """
    tree = ast.parse(
        "TYPE_CHECKING = True\n" + _BRANCHES_TESTED.format(test="TYPE_CHECKING")
    )
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    assert ast_scan.for_the_type_checker(tree) == frozenset()
    assert ast_scan.for_the_type_checker(function) == frozenset()
    ast_scan.forget_trees()


@pytest.mark.parametrize(
    ("prelude", "test", "alone", "in_its_module"),
    [
        ("TYPE_CHECKING = True\n", "TYPE_CHECKING", True, False),
        ("import typing as t\n", "t.TYPE_CHECKING", False, True),
    ],
    ids=["module-rebinds-the-flag", "module-names-typing-otherwise"],
)
def test_a_scope_read_before_its_module_reads_the_module_s_flag_once_it_is_read(
    prelude: str, test: str, *, alone: bool, in_its_module: bool
) -> None:
    """A function read as a tree of its own before its module reads its own
    bindings, as a fragment does; once the module is read, the function reads
    what the module binds the flag to, whatever it was asked before.

    What the function's blocks never run, and which of its two classes of
    one name stands, were kept from the first reading, so a guard that read
    a function before its module took the block of a module that binds
    ``TYPE_CHECKING = True`` for one that never runs, and ran the block of
    one that imports ``typing as t``, for as long as it ran.
    """
    tree = ast.parse(
        prelude
        + textwrap.dedent(
            f"""
            def f():
                held = 1
                if {test}:
                    held = 2
                class Box:
                    def size(self):
                        return 1
                if {test}:
                    class Box:
                        def size(self):
                            return 2
                return held, 3 if {test} else 4
            """
        )
    )
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    first, second = ast_scan.bindings_by_name(function)["held"]
    returned = function.body[-1]
    assert isinstance(returned, ast.Return)
    assert isinstance(returned.value, ast.Tuple)
    read, chosen = returned.value.elts
    assert isinstance(chosen, ast.IfExp)
    sizes = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.FunctionDef) and node.name == "size"
    ]

    def reads_the_flag() -> bool:
        never = id(second) in ast_scan.for_the_type_checker(function)
        runs = id(chosen.orelse) in ast_scan.for_the_program(function)
        held = ast_scan.live_bindings(function, [first, second], read)
        standing = ast_scan.live_class_members(function, sizes)
        assert runs is never
        assert held == ([first] if never else [first, second])
        assert standing == (sizes[:1] if never else sizes)
        return never

    assert reads_the_flag() is alone
    ast_scan.for_the_type_checker(tree)
    assert reads_the_flag() is in_its_module
    ast_scan.forget_trees()


def test_what_a_function_never_runs_is_emptied_in_every_form() -> None:
    """The negated test keeps its body and loses its ``else``, and a conditional
    expression loses the branch that never runs, in a lambda or a comprehension of
    the function too. Each still reads what runs.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            def f(x):
                if not TYPE_CHECKING:
                    runs_a = 1
                else:
                    never_a = 2
                runs_b = 3 if not TYPE_CHECKING else never_b
                runs_c = never_c if TYPE_CHECKING else 4
                held = lambda: never_d if TYPE_CHECKING else 5
                return [never_e if TYPE_CHECKING else 6 for _ in x]

            top = 7 if TYPE_CHECKING else 8
            """
        )
    )
    ast_scan.empty_type_checking_bodies(tree)
    source = ast.unparse(tree)
    assert "runs_a = 1" in source
    assert "runs_b = 3" in source
    assert "runs_c" in source
    assert "never_" not in source
    assert "top = 7 if TYPE_CHECKING else 8" in source


def test_a_type_parameter_hides_the_module_name_of_its_spelling() -> None:
    """``def f[T]`` and ``class Box[T]`` bind ``T`` for what they hold: the
    function's body, the class body and the methods of the class, which
    see the class's type parameters though not its other names. A name of
    the module of that spelling is not what ``T`` reads there.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            T = make()

            def first[T](x):
                return T(x)

            class Box[T]:
                item = T()

                def get(self):
                    return T()

                def own(self, T):
                    return T()

            def plain(x):
                return T(x)
            """
        )
    )
    first, box = tree.body[1], tree.body[2]
    assert isinstance(box, ast.ClassDef)
    in_first, in_body, in_method, in_own, in_plain = _calls(tree, "T")
    assert ast_scan.binding_of(tree, in_first, "T") == ("binding", first)
    assert ast_scan.binding_of(tree, in_body, "T") == ("binding", box)
    assert ast_scan.binding_of(tree, in_method, "T") == ("binding", box)
    assert ast_scan.binding_of(tree, in_own, "T")[1] is box.body[2]
    assert ast_scan.binding_of(tree, in_plain, "T") == ("binding", tree)
    assert ast_scan.own_names(first).binds("T")


def test_a_binding_runs_before_a_read_only_on_every_way_there() -> None:
    """An assignment or an import straight in a block that holds the read,
    before it, runs on every way to the read; one in a branch, in the body
    of a ``try``, a loop's target, or one after the read does not.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            def f(x, items):
                a = 1
                if x:
                    b = 1
                try:
                    c = 1
                except ValueError:
                    pass
                for d in items:
                    pass
                import os as e
                use(a, b, c, d, e, g)
                g = 1
            """
        )
    )
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    (call,) = _calls(function, "use")
    stores = {
        node.id: node
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    imported = next(n for n in ast.walk(function) if isinstance(n, ast.Import))
    found = {
        name: ast_scan.runs_before(tree, node, call)
        for name, node in [*stores.items(), ("e", imported)]
    }
    assert found == {
        "a": True, "b": False, "c": False, "d": False, "e": True, "g": False,
    }  # fmt: skip


def test_a_binding_runs_before_a_read_in_the_same_with_or_try_body() -> None:
    """A binding and a read in one ``with`` or ``try`` body: an exception
    that skips the binding leaves that body, and the read with it, so the
    read is reached only through the binding. A read after the statement
    still meets an exception caught before the binding ran.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            def f():
                with ctx():
                    a = 1
                    use(a)
                try:
                    b = 1
                    use(b)
                except ValueError:
                    pass
                try:
                    c = 1
                except ValueError:
                    pass
                use(c)
            """
        )
    )
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    reads = {
        node.id: node
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    found = {
        node.id: ast_scan.runs_before(tree, node, reads[node.id])
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    assert found == {"a": True, "b": True, "c": False}


def test_an_annotation_without_a_value_runs_no_binding_before_a_read() -> None:
    """``a: int`` binds nothing, so it is no binding that runs before a read;
    ``b: int = 1`` binds ``b`` as an assignment does.
    """
    tree = ast.parse(
        textwrap.dedent(
            """
            def f():
                a: int
                b: int = 1
                use(a, b)
            """
        )
    )
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    (call,) = _calls(function, "use")
    found = {
        node.id: ast_scan.runs_before(tree, node, call)
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    assert found == {"a": False, "b": True}


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


def test_an_assignment_expression_is_read_as_the_assignment_it_is() -> None:
    """``(fn := helper)`` stores ``helper`` in ``fn`` as ``fn = helper`` does.

    :func:`ast_scan.bindings_by_name` gives such a binding as the expression,
    and its value was read only from an assignment statement, so a name an
    assignment expression binds stood for nothing the guards could follow.
    """
    tree = ast.parse("def f():\n    if (fn := helper) is not None:\n        pass\n")
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    (binding,) = ast_scan.bindings_by_name(function)["fn"]
    assert isinstance(binding, ast.NamedExpr)
    target = ast_scan.assignment_target(binding)
    assert target is binding.target
    for node in (binding, binding.target):
        value = ast_scan.assigned_value(tree, node)
        assert isinstance(value, ast.Name)
        assert value.id == "helper"
    statement = ast.parse("fn = helper").body[0]
    assert isinstance(statement, ast.Assign)
    assert ast_scan.assignment_target(statement.targets[0]) is statement.targets[0]
    assert ast_scan.assignment_target(statement) is None
