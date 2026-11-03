#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A reader of a caller's number names the parameter the number came from.

Every check of ``_internal/validation.py`` that takes ``(value, name)`` writes
``name`` into what it refuses, and the caller looks for that name among the
parameters of the function they called. A reading inside a loop that handed
the loop's own variable named nothing the caller wrote:
``signals.tone_burst(pre_silence="0.1")`` was refused as ``'value' must be one
number``, ``environment.amplitude_modulation_block(modulation_frequency_range_hz=
("0.5", 2.0))`` as ``'v' must be one number``, and a reading in an error
message of the pile-driving spectrum named ``'np'``, the alias of NumPy.

The calls below hold each public function that reads such a number to the
parameter's name, and the AST check holds the tree: a name handed to a reader
is never a variable a ``for`` or a comprehension binds where the call is, never
the alias of an imported module, and never the iterable of another variable
of the same ``zip`` (``real_number(i, "ks")`` over
``zip(ks, pressure, intensity)``).
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import textwrap
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pytest

import phonometry
from phonometry import broadcast, environment, hearing, materials, room, signals
from phonometry._internal import validation

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

_SOURCE = pathlib.Path(phonometry.__file__).parent


def _readers() -> frozenset[str]:
    """The checks of the validation module that take ``(value, name)``."""
    found = set()
    for attribute, member in vars(validation).items():
        if not inspect.isfunction(member) or member.__module__ != validation.__name__:
            continue
        parameters = list(inspect.signature(member).parameters)
        if len(parameters) >= 2 and parameters[1] == "name":  # noqa: PLR2004
            found.add(attribute)
    return frozenset(found)


_READERS = _readers()


def _roots(node: ast.AST) -> set[str]:
    """The names and attributes an expression is written from."""
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)
    }


def _bind(target: ast.expr, iterable: ast.expr, into: dict[str, ast.expr]) -> None:
    """Record what each variable of a loop *target* runs over."""
    if isinstance(target, ast.Name):
        into[target.id] = iterable
        return
    if not isinstance(target, ast.Tuple | ast.List):
        return
    if (
        isinstance(iterable, ast.Call)
        and isinstance(iterable.func, ast.Name)
        and iterable.func.id == "zip"
        and len(iterable.args) == len(target.elts)
    ):
        for element, argument in zip(target.elts, iterable.args, strict=True):
            _bind(element, argument, into)
        return
    for element in target.elts:
        _bind(element, iterable, into)


def _module_aliases(tree: ast.Module) -> frozenset[str]:
    """The names an ``import`` statement of *tree* binds to a module."""
    return frozenset(
        alias.asname or alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )


class _Reader(ast.NodeVisitor):
    """Walks one module, keeping what each loop variable in scope runs over."""

    def __init__(self, where: str, aliases: frozenset[str]) -> None:
        self.where = where
        self.aliases = aliases
        self.loops: list[dict[str, ast.expr]] = [{}]
        self.found: list[str] = []

    def _scope(self, node: ast.AST) -> None:
        self.loops.append({})
        self.generic_visit(node)
        self.loops.pop()

    visit_FunctionDef = visit_AsyncFunctionDef = visit_Lambda = _scope

    def _with_loop(self, bound: dict[str, ast.expr], body: list[ast.AST]) -> None:
        self.loops.append({**self.loops[-1], **bound})
        for node in body:
            self.visit(node)
        self.loops.pop()

    def visit_For(self, node: ast.For | ast.AsyncFor) -> None:
        self.visit(node.iter)
        bound: dict[str, ast.expr] = {}
        _bind(node.target, node.iter, bound)
        self._with_loop(bound, [*node.body, *node.orelse])

    visit_AsyncFor = visit_For

    def _comprehension(
        self, node: ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp
    ) -> None:
        bound: dict[str, ast.expr] = {}
        for generator in node.generators:
            self.visit(generator.iter)
            _bind(generator.target, generator.iter, bound)
        parts = [part for generator in node.generators for part in generator.ifs]
        if isinstance(node, ast.DictComp):
            parts += [node.key, node.value]
        else:
            parts.append(node.elt)
        self._with_loop(bound, parts)

    visit_ListComp = visit_SetComp = visit_GeneratorExp = visit_DictComp = (
        _comprehension
    )

    def visit_Call(self, node: ast.Call) -> None:
        self.generic_visit(node)
        if not (
            isinstance(node.func, ast.Name)
            and node.func.id in _READERS
            and len(node.args) >= 2  # noqa: PLR2004
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            return
        reason = self._misnaming(node.args[0], node.args[1].value)
        if reason:
            self.found.append(
                f"{self.where}:{node.lineno}: {ast.unparse(node)} {reason}"
            )

    def _misnaming(self, value: ast.expr, name: str) -> str | None:
        loops = self.loops[-1]
        if name in self.aliases:
            return "names an imported module"
        if name in loops:
            return "names a loop's variable"
        if not (isinstance(value, ast.Name) and value.id in loops):
            return None
        own = _roots(loops[value.id])
        others = set().union(*(_roots(it) for it in loops.values())) - own
        if name in others:
            return "names another value of the loop"
        return None


def misnamed_readings(root: pathlib.Path) -> list[str]:
    """Every reading under *root* whose name is no parameter the value came from."""
    found: list[str] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        reader = _Reader(str(path.relative_to(root)), _module_aliases(tree))
        reader.visit(tree)
        found += reader.found
    return found


def _misnamed_in(source: str) -> list[str]:
    tree = ast.parse(textwrap.dedent(source))
    reader = _Reader("planted.py", _module_aliases(tree))
    reader.visit(tree)
    return reader.found


def test_the_library_hands_every_reader_a_parameter_s_name() -> None:
    assert misnamed_readings(_SOURCE) == []


@pytest.mark.parametrize(
    "source",
    [
        # The loop's own variable.
        """
        def burst(pre, post):
            for name, value in (("pre", pre), ("post", post)):
                real_number(value, "value")
        """,
        # A comprehension's variable.
        """
        def band(range_hz):
            return tuple(real_number(v, "v") for v in range_hz)
        """,
        # A variable of a generator expression handed to any().
        """
        def deltas(a, b):
            return any(require_finite(d, "d") for d in (a, b))
        """,
        # The alias of an imported module.
        """
        import numpy as np

        def message(frequencies, i):
            return real_number(np.asarray(frequencies)[i], "np")
        """,
        # The iterable of another variable of the same zip.
        """
        def annex(ks, pressure, intensity):
            for k, p, i in zip(ks, pressure, intensity, strict=True):
                complex_number(i, "ks")
        """,
    ],
)
def test_the_check_finds_a_reading_named_after_no_parameter(source: str) -> None:
    assert len(_misnamed_in(source)) == 1


@pytest.mark.parametrize(
    "source",
    [
        # The loop hands the reader the parameter's name it carries.
        """
        def burst(pre, post):
            for name, value in (("pre", pre), ("post", post)):
                real_number(value, name)
        """,
        # The iterable's own name.
        """
        def band(range_hz):
            return tuple(real_number(v, "range_hz") for v in range_hz)
        """,
        # A helper's parameter that shares a name with a loop elsewhere.
        """
        def outer(values):
            for value in values:
                pass

            def fmt(value):
                return real_number(value, "value")

            return fmt
        """,
    ],
)
def test_the_check_passes_a_reading_named_after_its_parameter(source: str) -> None:
    assert _misnamed_in(source) == []


def _parameters(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    arguments = function.args
    return [
        a.arg for a in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
    ]


def _read_bare(value: ast.expr) -> str | None:
    """The name *value* reads as it is or by an item (``x``, ``x[i]``), or ``None``.

    A field read off a record (``record.height_m``) is named after the field,
    which is what the caller wrote, so it is no value read bare.
    """
    while isinstance(value, ast.Subscript):
        value = value.value
    return value.id if isinstance(value, ast.Name) else None


def _helper_readings(
    helper: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, list[tuple[str, int]]]:
    """``{parameter: [(name handed to the reader, line)]}`` of what *helper* reads by a literal name."""
    parameters = set(_parameters(helper))
    found: dict[str, list[tuple[str, int]]] = {}
    for node in ast.walk(helper):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in _READERS
            and len(node.args) >= 2  # noqa: PLR2004
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            continue
        read = _read_bare(node.args[0])
        if read in parameters:
            found.setdefault(read, []).append((node.args[1].value, node.lineno))
    return found


#: One reading of a value by a literal name: the name, its line and the
#: function whose reader writes it.
type _Reading = tuple[str, int, str]


def _bound_arguments(
    callee: ast.FunctionDef | ast.AsyncFunctionDef, call: ast.Call
) -> dict[str, ast.expr]:
    """What *call* hands each parameter of *callee*, by position or keyword."""
    bound = dict(zip(_parameters(callee), call.args, strict=False))
    bound.update({k.arg: k.value for k in call.keywords if k.arg})
    return bound


#: The statements that hold other statements: a reading inside one of them
#: runs on some paths only, so it is no reading that runs before what follows.
_COMPOUND = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.TryStar,
    ast.With,
    ast.AsyncWith,
    ast.Match,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
)


def _runs_whole(node: ast.AST) -> Iterator[ast.AST]:
    """The nodes of *node* that run whenever it runs, *node* among them.

    A conditional expression runs its test, an ``and`` or an ``or`` its
    first operand and a chained comparison its first link, and the rest
    on some paths only. A lambda computes its defaults where it is written
    and runs its body when it is called, which may be never; a
    comprehension reads its first iterable before any item and the rest
    once for each item, of which there may be none, and a generator only
    when it is drawn from. ``python -O`` leaves an ``assert`` out, and the
    annotation of a variable is never read.
    """
    yield node
    parts: list[ast.AST]
    if isinstance(node, ast.Assert):
        parts = []
    elif isinstance(node, ast.IfExp):
        parts = [node.test]
    elif isinstance(node, ast.BoolOp):
        parts = node.values[:1]
    elif isinstance(node, ast.Compare):
        parts = [node.left, node.comparators[0]]
    elif isinstance(node, ast.Lambda):
        parts = [
            *node.args.defaults,
            *(default for default in node.args.kw_defaults if default is not None),
        ]
    elif isinstance(node, ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp):
        parts = [node.generators[0].iter]
    elif isinstance(node, ast.AnnAssign):
        parts = [node.target] if node.value is None else [node.target, node.value]
    else:
        parts = list(ast.iter_child_nodes(node))
    for part in parts:
        yield from _runs_whole(part)


def _reads_itself(statement: ast.stmt, parameter: str) -> bool:
    """Whether a statement reads *parameter* under its own name whenever it holds one.

    A simple statement that hands it to a reader in a part that runs
    whenever the statement does (:func:`_runs_whole`) does; so does ``if
    parameter is not None:`` with such a statement in its body, since a
    parameter that is ``None`` holds no number to read, and every later use
    of one that is not finds it read.
    """
    if (
        isinstance(statement, ast.If)
        and isinstance(statement.test, ast.Compare)
        and isinstance(statement.test.left, ast.Name)
        and statement.test.left.id == parameter
        and len(statement.test.ops) == 1
        and isinstance(statement.test.ops[0], ast.IsNot)
        and isinstance(statement.test.comparators[0], ast.Constant)
        and statement.test.comparators[0].value is None
    ):
        return any(_reads_itself(inner, parameter) for inner in statement.body)
    if isinstance(statement, _COMPOUND):
        return False
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _READERS
        and len(node.args) >= 2  # noqa: PLR2004
        and _read_bare(node.args[0]) == parameter
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == parameter
        for node in _runs_whole(statement)
    )


def _read_before(
    function: ast.FunctionDef | ast.AsyncFunctionDef, call: ast.Call, parameter: str
) -> bool:
    """Whether *function* reads *parameter* under its own name on every path to *call*.

    A reading counts where it is a simple statement that comes before one of
    the statements holding *call*, in the same block, and sits in a part of
    it that runs whole: it runs before the call whichever way the function
    goes. One in a branch, a loop or a handler runs on some paths only, as
    does one on a side of a conditional expression, after an ``and`` or an
    ``or``, or in a lambda, a comprehension or a generator.
    """
    parents: dict[ast.AST, tuple[ast.AST, list[ast.stmt]]] = {}
    for node in ast.walk(function):
        for field in ("body", "orelse", "finalbody", "handlers", "cases"):
            block = getattr(node, field, None)
            if isinstance(block, list):
                for child in block:
                    parents[child] = (node, block)
    holder: ast.AST | None = next(
        (
            statement
            for statement in ast.walk(function)
            if isinstance(statement, ast.stmt)
            and not isinstance(statement, _COMPOUND)
            and any(node is call for node in ast.walk(statement))
        ),
        None,
    )
    while holder is not None and holder in parents:
        owner, block = parents[holder]
        if isinstance(holder, ast.stmt):
            earlier = block[: block.index(holder)]
            if any(_reads_itself(statement, parameter) for statement in earlier):
                return True
        holder = owner if owner is not function else None
    return False


type _Function = ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True)
class _Module:
    """One module of the package as the check reads it."""

    dotted: str
    where: str
    tree: ast.Module
    #: Its functions at the top, by name.
    functions: dict[str, _Function]
    #: The names it imports from another module: ``{local: (module, name)}``.
    imports: dict[str, tuple[str, str]]

    @property
    def public(self) -> bool:
        """Whether a caller imports from it by a path with no private part."""
        return not any(part.startswith("_") for part in self.dotted.split("."))


def _module(dotted: str, where: str, tree: ast.Module, *, package: bool) -> _Module:
    """Read *tree*, the module *dotted* (a package's ``__init__`` when *package*)."""
    base = dotted if package else dotted.rpartition(".")[0]
    imports: dict[str, tuple[str, str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        source = node.module or ""
        if node.level:
            parent = base.rsplit(".", node.level - 1)[0] if node.level > 1 else base
            source = f"{parent}.{source}" if source else parent
        for alias in node.names:
            imports[alias.asname or alias.name] = (source, alias.name)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    return _Module(dotted, where, tree, functions, imports)


def _published(module: _Module) -> set[str]:
    """The names *module*'s ``__all__`` lists."""
    for node in module.tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)
            and isinstance(node.value, ast.List | ast.Tuple)
        ):
            return {
                e.value
                for e in node.value.elts
                if isinstance(e, ast.Constant) and isinstance(e.value, str)
            }
    return set()


class _Readings:
    """What each function of the package reads its parameters as, through its calls too.

    A function reads a parameter under a literal name where it hands it to a
    reader itself, and wherever it hands it on, bare, to another function of
    the package, private or public, of its module or one it imports from,
    that reads it: the name that function's reader writes, however many calls
    down, is the name the caller's own caller sees. A parameter the function
    read under its own name on every path to the call is refused there first,
    so what the callee reads of it after says nothing.
    """

    def __init__(self, modules: list[_Module]) -> None:
        self.modules = {module.dotted: module for module in modules}
        self._memo: dict[tuple[str, str], dict[str, list[_Reading]]] = {}

    def resolve(
        self, module: _Module, name: str, depth: int = 0
    ) -> tuple[_Module, _Function] | None:
        """The function *name* stands for in *module*, followed through its imports."""
        if name in module.functions:
            return module, module.functions[name]
        source, original = module.imports.get(name, ("", ""))
        if source in self.modules and depth < len(self.modules):
            return self.resolve(self.modules[source], original, depth + 1)
        return None

    def handed(
        self,
        module: _Module,
        function: _Function,
        visiting: frozenset[tuple[str, str]] = frozenset(),
    ) -> Iterator[tuple[str, list[_Reading]]]:
        """Each parameter *function* hands on, with how it is read down there."""
        given = set(_parameters(function))
        for call in ast.walk(function):
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)):
                continue
            found = self.resolve(module, call.func.id)
            if found is None or found[1] is function:
                continue
            owner, callee = found
            if (owner.dotted, callee.name) in visiting:
                continue
            inner = visiting | {(module.dotted, function.name)}
            readings = self.of(owner, callee, inner)
            for parameter, value in _bound_arguments(callee, call).items():
                if not (isinstance(value, ast.Name) and value.id in given):
                    continue
                if _read_before(function, call, value.id):
                    continue
                if parameter in readings:
                    yield value.id, readings[parameter]

    def of(
        self,
        module: _Module,
        function: _Function,
        visiting: frozenset[tuple[str, str]] = frozenset(),
    ) -> dict[str, list[_Reading]]:
        """``{parameter: readings}`` of *function*, its own and its callees'."""
        key = (module.dotted, function.name)
        if key in self._memo:
            return self._memo[key]
        found: dict[str, list[_Reading]] = {
            parameter: [
                (name, line, f"{module.where}:{line}: {function.name}")
                for name, line in uses
            ]
            for parameter, uses in _helper_readings(function).items()
        }
        for parameter, uses in self.handed(module, function, visiting):
            found.setdefault(parameter, []).extend(uses)
        if not visiting:
            self._memo[key] = found
        return found


def _public_callers(module: _Module, published: set[str]) -> Iterator[_Function]:
    """The functions and methods of *module* a caller of the library calls."""

    def public(name: str) -> bool:
        return not name.startswith("_") and (module.public or name in published)

    for node in module.tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and public(
            node.name
        ):
            yield node
        elif isinstance(node, ast.ClassDef) and public(node.name):
            yield from (
                method
                for method in node.body
                if isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef)
                and not method.name.startswith("_")
            )


def _misnamings(modules: list[_Module]) -> list[str]:
    """Readings, down any chain of calls in the package, named otherwise than
    the public parameter handed to them.
    """
    readings = _Readings(modules)
    published = set().union(*(_published(m) for m in modules if m.public))
    found: set[str] = set()
    for module in modules:
        for caller in _public_callers(module, published):
            for parameter, uses in readings.handed(module, caller):
                found.update(
                    f"{place} names {name!r} what {caller.name} hands it as "
                    f"{parameter!r}"
                    for name, _line, place in uses
                    if name != parameter
                )
    return sorted(found)


def _handed_misnamings(tree: ast.Module, where: str) -> list[str]:
    """The misnamed readings of one module read on its own, as a public one."""
    return _misnamings([_module("planted", where, tree, package=False)])


def misnamed_handed_readings(root: pathlib.Path) -> list[str]:
    """Every reading under *root* named after no parameter of the public
    function that hands it the value, down any chain of calls.
    """
    modules = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        parts = (root.name, *relative.with_suffix("").parts)
        package = parts[-1] == "__init__"
        dotted = ".".join(parts[:-1] if package else parts)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        modules.append(_module(dotted, str(relative), tree, package=package))
    return _misnamings(modules)


def test_a_reading_in_a_module_the_caller_imports_from_is_found() -> None:
    """A public function of one module hands its value to a function of
    another, which reads it under that function's own name.
    """
    helper = ast.parse(
        textwrap.dedent(
            """
            def plot_transfer_matrix(matrix, frequency):
                return real_array(frequency, "frequency")
            """
        )
    )
    caller = ast.parse(
        textwrap.dedent(
            """
            from .._plot.materials import plot_transfer_matrix

            class TransferMatrix:
                def plot(self, frequencies):
                    return plot_transfer_matrix(self, frequencies)
            """
        )
    )
    modules = [
        _module("pkg._plot.materials", "_plot/materials.py", helper, package=False),
        _module("pkg.materials.tm", "materials/tm.py", caller, package=False),
    ]
    assert _misnamings(modules) == [
        "_plot/materials.py:3: plot_transfer_matrix names 'frequency' what plot "
        "hands it as 'frequencies'"
    ]


def test_a_helper_names_a_value_as_the_public_caller_does() -> None:
    """A private helper read a value its public caller handed on under its own
    name: ``weighted_absorption({250: "x", ...})`` was refused as ``'values'``,
    ``sound_intensity(..., speed_of_sound="343")`` as ``'c'``.
    """
    assert misnamed_handed_readings(_SOURCE) == []


@pytest.mark.parametrize(
    "source",
    [
        # An item of a mapping the helper names after its own parameter.
        """
        def _coerce(values, centers, name):
            return [real_number(values[c], "values") for c in centers]

        def weighted_absorption(alpha_p):
            return _coerce(alpha_p, (250, 500), "alpha_p")
        """,
        # A value handed on by keyword under a shorter name.
        """
        def _bend(bands, *, width):
            return require_positive(width, "width")

        def elbow(frequencies, width_m):
            return _bend(frequencies, width=width_m)
        """,
        # Two private calls down: the reading names the second helper's own.
        """
        def _mean_level(levels):
            return real_array(levels, "levels")

        def _comparison_inputs(n_bands, reference_levels):
            return _mean_level(reference_levels)

        def sound_power_comparison(levels, reference_levels):
            return _comparison_inputs(3, reference_levels)
        """,
        # A public function handed another's value, which it reads as its own.
        """
        def db_hr_global_index(band_values):
            return real_array(band_values, "band_values")

        def ra(reduction_index):
            return db_hr_global_index(reduction_index)
        """,
        # Read under its own name in one branch only: the other reaches the
        # helper unread.
        """
        def _mean_level(levels):
            return real_array(levels, "levels")

        def corrected(levels, background_levels, per_position):
            if per_position:
                real_array(background_levels, "background_levels")
            return _mean_level(background_levels)
        """,
        *(
            f"""
            def _mean_level(levels):
                return real_array(levels, "levels")

            def corrected(background_levels, flag, rows):
                {reading}
                return _mean_level(background_levels)
            """
            for reading in (
                # Read on one side of a conditional expression only.
                'checked = real_array(background_levels, "background_levels") '
                "if flag else None",
                # Read after an ``and`` or an ``or`` that may stop before it.
                'checked = flag and real_array(background_levels, "background_levels")',
                'checked = flag or real_array(background_levels, "background_levels")',
                # Read in a later link of a chained comparison, which runs
                # only when the first one holds.
                'checked = 0 < flag < real_array(background_levels, "background_levels")',
                # Read when a lambda is called, which may be never.
                'read = lambda: real_array(background_levels, "background_levels")',
                # Read in a comprehension's element, once for each item of
                # what may hold none.
                'checked = [real_array(background_levels, "background_levels") '
                "for _ in rows]",
                # Read in the iterable of a comprehension's second loop.
                "checked = [v for _ in rows for v in "
                'real_array(background_levels, "background_levels")]',
                # Read when a generator is drawn from, which may be never.
                'checked = (real_array(background_levels, "background_levels") '
                "for _ in (1,))",
                # Read in an ``assert``, which ``python -O`` leaves out.
                'assert real_array(background_levels, "background_levels") is not None',
            )
        ),
    ],
)
def test_the_check_finds_a_helper_reading_named_after_itself(source: str) -> None:
    tree = ast.parse(textwrap.dedent(source))
    assert len(_handed_misnamings(tree, "planted.py")) == 1


@pytest.mark.parametrize(
    "source",
    [
        # The caller's name handed on with the value.
        """
        def _coerce(values, centers, name):
            return [real_number(values[c], name) for c in centers]

        def weighted_absorption(alpha_p):
            return _coerce(alpha_p, (250, 500), "alpha_p")
        """,
        # A field of a record, named after the field the caller set.
        """
        def _setup(ground):
            return require_scalar(ground.receiver_height_m, "receiver_height_m")

        def event_level(ground):
            return _setup(ground)
        """,
        # The helper's name is the public parameter's.
        """
        def _spacing(spacing_m):
            return require_scalar(spacing_m, "spacing_m")

        def range_of(spacing_m):
            return _spacing(spacing_m)
        """,
        # Read under its own name before another public function reads it.
        """
        def db_hr_global_index(band_values):
            return real_array(band_values, "band_values")

        def ra(reduction_index):
            real_array(reduction_index, "reduction_index")
            return db_hr_global_index(reduction_index)
        """,
        # Read under its own name whenever it is given, before it goes on.
        """
        def assess_background_noise(noise_levels):
            return real_array(noise_levels, "noise_levels")

        def verify(levels, background_noise_levels=None):
            if background_noise_levels is not None:
                real_array(background_noise_levels, "background_noise_levels")
            if background_noise_levels is not None:
                return assess_background_noise(background_noise_levels)
            return None
        """,
        # The caller's name handed down the chain with the value.
        """
        def _mean_level(levels, name):
            return real_array(levels, name)

        def _comparison_inputs(reference_levels):
            return _mean_level(reference_levels, "reference_levels")

        def sound_power_comparison(reference_levels):
            return _comparison_inputs(reference_levels)
        """,
        *(
            f"""
            def _mean_level(levels):
                return real_array(levels, "levels")

            def corrected(background_levels, flag, rows):
                {reading}
                return _mean_level(background_levels)
            """
            for reading in (
                # Read in the test of a conditional expression, which runs
                # whichever side it picks.
                'checked = None if real_array(background_levels, "background_levels") '
                "is None else flag",
                # Read in the first operand of an ``or``, which always runs.
                'checked = real_array(background_levels, "background_levels") or flag',
                # Read in the first link of a chained comparison.
                'checked = real_array(background_levels, "background_levels") < flag < 1',
                # Read in the first iterable of a comprehension, read before
                # its first item, and of a generator, read where it is written.
                "checked = [v for v in "
                'real_array(background_levels, "background_levels")]',
                "checked = (v for v in "
                'real_array(background_levels, "background_levels"))',
                # Read in a lambda's default, computed where it is written.
                'read = lambda v=real_array(background_levels, "background_levels"): v',
            )
        ),
    ],
)
def test_the_check_passes_a_helper_reading_named_as_its_caller_does(
    source: str,
) -> None:
    tree = ast.parse(textwrap.dedent(source))
    assert _handed_misnamings(tree, "planted.py") == []


_LEVELS = np.full(22, 90.0)
_OCCLUDED = np.full((3, 22), 70.0)

#: A public call per reading the tree named after a loop, given a text where
#: one number goes, and the parameter the refusal must name.
_CALLS: list[tuple[str, Callable[[], object], str]] = [
    (
        "signals.tone_burst pre_silence",
        lambda: signals.tone_burst(48_000, 1000, 4, pre_silence="0.1"),
        "pre_silence",
    ),
    (
        "signals.tone_burst post_silence",
        lambda: signals.tone_burst(48_000, 1000, 4, post_silence="0.1"),
        "post_silence",
    ),
    (
        "environment.amplitude_modulation_block",
        lambda: environment.amplitude_modulation_block(
            np.full(100, 40.0), modulation_frequency_range_hz=("0.5", 2.0)
        ),
        "modulation_frequency_range_hz",
    ),
    (
        "hearing.earmuff_insertion_loss fixture",
        lambda: hearing.earmuff_insertion_loss(
            _LEVELS, _OCCLUDED, fixture_uncertainty_db="1"
        ),
        "fixture_uncertainty_db",
    ),
    (
        "hearing.earmuff_insertion_loss sound field",
        lambda: hearing.earmuff_insertion_loss(
            _LEVELS, _OCCLUDED, sound_field_uncertainty_db="1"
        ),
        "sound_field_uncertainty_db",
    ),
    (
        "hearing.earmuff_insertion_loss equipment",
        lambda: hearing.earmuff_insertion_loss(
            _LEVELS, _OCCLUDED, equipment_uncertainty_db="1"
        ),
        "equipment_uncertainty_db",
    ),
    (
        "broadcast.QuasiPeakDynamicsResult",
        lambda: broadcast.QuasiPeakDynamicsResult(
            fs=48_000.0, readings_percent=("50",) * 11
        ),
        "readings_percent",
    ),
    (
        "room.sabine_reverberation_time",
        lambda: room.sabine_reverberation_time(100.0, [("10", 0.5)]),
        "surfaces",
    ),
    (
        "room.reverberation_time_models",
        lambda: room.reverberation_time_models(("5", 4.0, 3.0), (0.2, 0.2, 0.2)),
        "dimensions",
    ),
    (
        "materials.frame_bulk_modulus",
        lambda: materials.frame_bulk_modulus("1e5", 0.3),
        "shear_modulus",
    ),
]


def _ids() -> Iterator[str]:
    return (label for label, _, _ in _CALLS)


@pytest.mark.parametrize(("label", "call", "parameter"), _CALLS, ids=list(_ids()))
def test_a_text_is_refused_by_the_parameter_s_name(
    label: str, call: Callable[[], object], parameter: str
) -> None:
    with pytest.raises(TypeError, match=f"'{parameter}' must be"):
        call()
