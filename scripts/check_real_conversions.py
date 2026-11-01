#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a conversion to floats that reads a caller's complex value as its real part.

``np.asarray(x, dtype=np.float64)`` takes a complex value and gives back its
real part, with no more than a ``ComplexWarning``: ``[1 + 2j]`` comes back as
``[1.0]``, and so does a NumPy complex number held in a list or an array of
objects. A function that converts what its caller gave it that way checks,
computes and returns from a value the caller never gave, and ISO/TS
12913-3's ``method_b_scale_values`` rated ``0.5 + 0.3j`` as the mark at 0.5.
The library reads a caller's numbers through the shared reader of
``src/phonometry/_internal/validation.py``, :func:`real_array`, which refuses
a complex value, a text and a ``bytearray`` by the parameter's name, or asks
one of the shared checks first (:data:`CHECKS`).

This reads every module under ``src/phonometry`` and reports a conversion to
floats of a caller's value that no check precedes in the same function:

- **A conversion to floats**: ``np.asarray``, ``np.array``,
  ``np.asanyarray``, ``np.ascontiguousarray`` or ``np.asfortranarray`` with a
  real floating dtype (``float``, ``np.float64``, ``np.float32``, ``"float64"``
  and the rest), given by keyword or in second place; ``.astype()`` of one;
  and ``np.float64()`` and ``np.float32()`` of a value.
- **A caller's value**: a parameter of the function that holds the
  conversion, read bare or through what keeps it the caller's (an item of it,
  ``x[0]``; ``np.atleast_1d(x)``, ``np.ravel(x)``, ``list(x)`` and the other
  conversions that keep its dtype; arithmetic on it), a name bound to one of
  those, or a name a ``for`` loop or a comprehension takes from one; and, in a
  record's ``__post_init__``, a field, ``self.x``, which the caller set. A
  private function's parameter counts as much as a public one's: a public
  function hands its caller's value on to the helper that converts it.
- **A check**: a call of one of :data:`CHECKS` with the value (or what it is
  read from) among its arguments, or of a function of the library that hands
  its first parameter to one (found by following such calls through the
  package until no new one turns up), earlier in the source than the
  conversion; or a name rebound to what a check returns. The order is read
  from the source, not from the paths the function can take.

A value the function computed (a local of its own arithmetic, a field of a
record it was handed, which the record read when it was built) is no
caller's, and the census lists it as computed. A field a record's method
reads outside ``__post_init__`` is listed apart: the record's constructor is
where its caller's value was read.

``--census`` prints every conversion to floats in the tree with what it
reads, so that the class is listed whole and not only what is left of it.

A conversion of a value that is no caller's number but that the rule cannot
tell from one (the samples SciPy decoded from a file, a mask the engine
builds, an array of objects an ``isinstance`` test has read item by item, the
quick path of the reader itself, the drawing helpers whose source the published
clips fingerprint, which draw what a result holds) is listed in
:data:`EXEMPT`, keyed by file and function with the reason; an entry that
covers nothing is reported too.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from ast_scan import ROOT, exempted, python_files, relative

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence

#: The library this reads, the default when no path is given.
SOURCE = ROOT / "src" / "phonometry"
#: The package every module of the library is named from.
PACKAGE = "phonometry"
#: The module that holds :data:`CHECKS`, by the name it is imported by.
SHARED = f"{PACKAGE}._internal.validation"

#: The shared checks of ``_internal/validation.py`` that refuse a complex value
#: given to them, by name. ``tests/test_check_real_conversions.py`` calls each
#: with one and wants the refusal.
CHECKS = frozenset(
    {
        "real_array",
        "refuse_complex",
        "holds_complex",
        "require_real",
        "require_scalar",
        "require_positive",
        "require_non_negative",
        "require_finite",
        "require_fraction",
        "require_count",
        "require_above_absolute_zero",
        "require_above_absolute_zero_array",
        "require_positive_array",
        "require_finite_array",
        "require_finite_matrix",
        "require_1d_signal",
        "require_per_band",
        "arrays_of",
        "pair_of_arrays",
        "floats_of",
        "pair_of_floats",
    }
)

#: The NumPy constructors that convert to the dtype they are given.
_ARRAY_CONVERSIONS = frozenset(
    {"asarray", "array", "asanyarray", "ascontiguousarray", "asfortranarray"}
)
#: The real floating dtypes, by the last part of their name or as a text.
_REAL_DTYPES = frozenset(
    {
        "float",
        "float16",
        "float32",
        "float64",
        "double",
        "single",
        "half",
        "longdouble",
        "f2",
        "f4",
        "f8",
        "d",
    }
)
#: The NumPy scalar types whose call converts one value to a real float.
_SCALAR_CONVERSIONS = frozenset({"float16", "float32", "float64", "double", "single"})
#: The calls that keep their argument the caller's: same values, same dtype
#: or one that still holds a complex number.
_KEEPING_CALLS = frozenset(
    {
        "asarray",
        "array",
        "asanyarray",
        "ascontiguousarray",
        "atleast_1d",
        "atleast_2d",
        "atleast_3d",
        "ravel",
        "squeeze",
        "copy",
        "list",
        "tuple",
        "sorted",
        "reversed",
        "enumerate",
        "zip",
        "flatten",
        "reshape",
        "transpose",
    }
)

#: The conversions of a value that is no caller's number, which the rule
#: cannot tell, keyed by the file relative to the repository and the function
#: that holds them, with the reason.
EXEMPT: dict[tuple[str, str], str] = {
    ("src/phonometry/_plot/common.py", "_srgb_to_lab"): (
        "an sRGB triple of the figure's own palette, which the contrast checks "
        "of every drawing read; no caller hands it, and the clips fingerprint "
        "this module's source"
    ),
    ("src/phonometry/_plot/common.py", "_facade_x_axis"): (
        "the band axis of a result being drawn, a field the result read when "
        "it was built; the clips fingerprint this module's source"
    ),
    ("src/phonometry/_plot/common.py", "_bar_width"): (
        "the bar positions a renderer computed from a result's band axis; the "
        "clips fingerprint this module's source"
    ),
    ("src/phonometry/_plot/common.py", "_plot_band_level_bars"): (
        "the levels of a result being drawn, a field the result read when it "
        "was built; the clips fingerprint this module's source"
    ),
    ("src/phonometry/_plot/common.py", "_plot_two_runs"): (
        "the band axis of a result being drawn, a field the result read when "
        "it was built; the clips fingerprint this module's source"
    ),
    ("src/phonometry/_internal/validation.py", "real_array"): (
        "the shared reader itself, whose quick path converts only an array of "
        "truth values, integers or floats, which holds no complex number"
    ),
    ("src/phonometry/_internal/display.py", "_sequence_summary"): (
        "a record's display, after an isinstance test that every item is an int "
        "or a float; reading it through real_array would import the validation "
        "module into the display module it imports"
    ),
    ("src/phonometry/io/_wav.py", "_scale_to_float"): (
        "the samples SciPy decoded from a WAV file, an integer or a float array "
        "by the format; no caller hands them"
    ),
    ("src/phonometry/simulation/elastic_fdtd.py", "_device_mask"): (
        "a boolean mask the engine builds from the grid, sent to the device as "
        "zeros and ones; no caller hands it"
    ),
    ("src/phonometry/simulation/fdtd.py", "_real_objects"): (
        "an array of objects converted only after an isinstance test that every "
        "item is a real number and no truth value"
    ),
}

#: What a conversion reads, as the census lists it.
Verdict = Literal["unchecked", "checked", "computed", "field"]


@dataclass(frozen=True)
class Conversion:
    """One conversion to floats, with what it reads."""

    path: pathlib.Path
    line: int
    function: str
    source: str
    verdict: Verdict

    @property
    def key(self) -> tuple[str, str]:
        """The file relative to the repository, and the function, as EXEMPT keys them."""
        return relative(self.path), self.function

    def describe(self) -> str:
        """One line naming the place, the verdict and the code."""
        return (
            f"{relative(self.path)}:{self.line}  {self.function}  "
            f"{self.verdict}: {self.source}"
        )


def _last_name(node: ast.expr) -> str | None:
    """``f`` of ``f``, of ``np.f`` and of ``a.b.f``; ``None`` for anything else."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_real_dtype(node: ast.expr | None) -> bool:
    """Whether *node* names a real floating dtype (``float``, ``np.float64``, ``"f8"``)."""
    if node is None:
        return False
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value in _REAL_DTYPES
    return _last_name(node) in _REAL_DTYPES


def _keyword(call: ast.Call, name: str) -> ast.expr | None:
    return next((k.value for k in call.keywords if k.arg == name), None)


def _array_conversion(call: ast.Call) -> ast.expr | None:
    """The value a NumPy constructor converts, when its dtype is a real float."""
    dtype = _keyword(call, "dtype")
    if dtype is None and len(call.args) > 1:
        dtype = call.args[1]
    return call.args[0] if call.args and _is_real_dtype(dtype) else None


def converted(call: ast.Call) -> ast.expr | None:
    """The value *call* converts to floats, or ``None`` when it converts none."""
    if not isinstance(call.func, ast.Attribute):
        return None
    name = call.func.attr
    if name in _ARRAY_CONVERSIONS:
        return _array_conversion(call)
    if name == "astype":
        dtype = call.args[0] if call.args else _keyword(call, "dtype")
        return call.func.value if _is_real_dtype(dtype) else None
    if name in _SCALAR_CONVERSIONS and len(call.args) == 1:
        return call.args[0]
    return None


def root(node: ast.expr, *, fields: bool) -> str | None:
    """The name a value is read from, through what keeps it the same value.

    ``x`` for ``x``, ``x[0]``, ``np.atleast_1d(x)`` and ``x.ravel()``;
    ``self.f`` for a field when *fields* (in ``__post_init__``); ``None`` for a
    value that is not read from one name.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        if fields and isinstance(node.value, ast.Name) and node.value.id == "self":
            return f"self.{node.attr}"
        return None
    if isinstance(node, ast.Subscript | ast.Starred):
        return root(node.value, fields=fields)
    if isinstance(node, ast.Call):
        return _kept_root(node, fields=fields)
    return None


def _kept_root(call: ast.Call, *, fields: bool) -> str | None:
    """The name a call that keeps its argument's values reads them from.

    A conversion to floats gives floats and is a site of its own, so it keeps
    nothing; a method (``x.ravel()``) keeps its object, a function
    (``np.atleast_1d(x)``, ``list(x)``) its first argument.
    """
    if converted(call) is not None or _last_name(call.func) not in _KEEPING_CALLS:
        return None
    func = call.func
    if isinstance(func, ast.Attribute) and not (
        isinstance(func.value, ast.Name) and func.value.id == "np"
    ):
        return root(func.value, fields=fields)
    return root(call.args[0], fields=fields) if call.args else None


def _roots(node: ast.expr, *, fields: bool) -> list[str]:
    """Every name *node* reads a value from as it is: either branch of a
    conditional, each member of a tuple or a list. Arithmetic computes a
    value of its own, and reads none as it is.
    """
    if isinstance(node, ast.IfExp):
        return _roots(node.body, fields=fields) + _roots(node.orelse, fields=fields)
    if isinstance(node, ast.Tuple | ast.List):
        return [name for item in node.elts for name in _roots(item, fields=fields)]
    found = root(node, fields=fields)
    return [] if found is None else [found]


def _parameters(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """The parameters of *function*, in order, ``self`` and ``cls`` left out."""
    arguments = function.args
    named = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]
    named.extend(each for each in (arguments.vararg, arguments.kwarg) if each)
    return [p.arg for p in named if p.arg not in {"self", "cls"}]


def _own_nodes(function: ast.AST) -> Iterator[ast.AST]:
    """The nodes of *function*, leaving out the functions, lambdas and classes in it."""
    pending = list(ast.iter_child_nodes(function))
    while pending:
        node = pending.pop()
        if isinstance(
            node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda
        ):
            continue
        yield node
        pending.extend(ast.iter_child_nodes(node))


def _end(node: ast.AST) -> tuple[int, int]:
    return (
        getattr(node, "end_lineno", 0) or 0,
        getattr(node, "end_col_offset", 0) or 0,
    )


def _start(node: ast.AST) -> tuple[int, int]:
    return (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))


#: A state a name takes at a place in the source: the caller's value, a value
#: a check has read, or anything else.
State = Literal["caller", "checked", "other"]


@dataclass
class _Function:
    """What a function's names hold, place by place, in the order of the source."""

    function: ast.FunctionDef | ast.AsyncFunctionDef
    checked_by: Callable[[ast.Call], list[ast.expr]]
    fields: bool
    events: dict[str, list[tuple[tuple[int, int], State]]] = field(default_factory=dict)
    parameters: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        self.parameters = frozenset(_parameters(self.function))

    def state(self, name: str, place: tuple[int, int]) -> State | None:
        """What *name* holds just before *place*, ``None`` when nothing binds it."""
        before = [event for event in self.events.get(name, ()) if event[0] < place]
        if before:
            return max(before)[1]
        if name in self.parameters or (self.fields and name.startswith("self.")):
            return "caller"
        return None

    def classify(self, value: ast.expr, place: tuple[int, int]) -> State:
        """What a name bound to *value* at *place* holds."""
        if isinstance(value, ast.Call) and self.checked_by(value):
            return "checked"
        states = {self.state(name, place) for name in _roots(value, fields=self.fields)}
        if "caller" in states:
            return "caller"
        return "checked" if "checked" in states else "other"


def _targets(target: ast.expr) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, ast.Tuple | ast.List):
        return [name for item in target.elts for name in _targets(item)]
    if isinstance(target, ast.Starred):
        return _targets(target.value)
    return []


def _bindings(node: ast.AST) -> Iterator[tuple[list[str], ast.expr, tuple[int, int]]]:
    """The names *node* binds, the value they are read from, and where."""
    if isinstance(node, ast.Assign):
        for target in node.targets:
            yield _targets(target), node.value, _end(node)
    elif isinstance(node, ast.AnnAssign | ast.NamedExpr) and node.value is not None:
        yield _targets(node.target), node.value, _end(node)
    elif isinstance(node, ast.For | ast.AsyncFor):
        yield _targets(node.target), node.iter, _start(node.target)
    elif isinstance(node, ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp):
        # The element is written first and read after its loops have bound
        # their names, so the names hold from where the comprehension opens.
        for generator in node.generators:
            yield _targets(generator.target), generator.iter, _start(node)
    elif isinstance(node, ast.withitem) and node.optional_vars is not None:
        yield _targets(node.optional_vars), node.context_expr, _end(node.context_expr)


def _events(scope: _Function, nodes: Sequence[ast.AST]) -> None:
    """Fill *scope*'s events from its *nodes*, in source order: each binding,
    then each check.
    """
    for node in nodes:
        for names, value, place in _bindings(node):
            state = scope.classify(value, place)
            for name in names:
                scope.events.setdefault(name, []).append((place, state))
        if not isinstance(node, ast.Call):
            continue
        for argument in scope.checked_by(node):
            for name in _roots(argument, fields=scope.fields):
                scope.events.setdefault(name, []).append((_end(node), "checked"))


def _verdict(scope: _Function, value: ast.expr, place: tuple[int, int]) -> Verdict:
    """What a conversion of *value* at *place* reads."""
    states = {scope.state(name, place) for name in _roots(value, fields=scope.fields)}
    if "caller" in states:
        return "unchecked"
    if "checked" in states:
        return "checked"
    read = root(value, fields=True)
    return "field" if read is not None and read.startswith("self.") else "computed"


def _functions(
    tree: ast.AST, scope: str = ""
) -> Iterator[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Every function and method of *tree*, with its qualified name."""
    for child in ast.iter_child_nodes(tree):
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            inner = f"{scope}.{child.name}" if scope else child.name
            if not isinstance(child, ast.ClassDef):
                yield inner, child
            yield from _functions(child, inner)
        else:
            yield from _functions(child, scope)


def _module_name(path: pathlib.Path) -> str:
    """The dotted name of a module of the library, from its path."""
    parts = list(path.with_suffix("").parts)
    start = len(parts) - 1 - parts[::-1].index(PACKAGE)
    dotted = parts[start:]
    if dotted[-1] == "__init__":
        dotted = dotted[:-1]
    return ".".join(dotted)


def _imports(tree: ast.Module, module: str, *, is_package: bool) -> dict[str, str]:
    """``{name: "module.name"}`` for each ``from`` import of the module."""
    package = module if is_package else module.rpartition(".")[0]
    found: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            parts = package.split(".")
            base = parts[: len(parts) - (node.level - 1)]
            source = ".".join([*base, *([node.module] if node.module else [])])
        else:
            source = node.module or ""
        for alias in node.names:
            found[alias.asname or alias.name] = f"{source}.{alias.name}"
    return found


@dataclass(frozen=True)
class _Body:
    """A function of a module, with its qualified name and its own nodes in
    the order of the source, read once.
    """

    qualified: str
    function: ast.FunctionDef | ast.AsyncFunctionDef
    nodes: tuple[ast.AST, ...]
    calls: tuple[ast.Call, ...]


@dataclass(frozen=True, eq=False)
class _Module:
    """A module of the library, parsed, with what its imports bind."""

    path: pathlib.Path
    name: str
    imports: dict[str, str]
    bodies: tuple[_Body, ...]


def _module(path: pathlib.Path) -> _Module:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    name = _module_name(path)
    bodies = []
    for qualified, function in _functions(tree):
        nodes = tuple(sorted(_own_nodes(function), key=_start))
        calls = tuple(node for node in nodes if isinstance(node, ast.Call))
        bodies.append(_Body(qualified, function, nodes, calls))
    imports = _imports(tree, name, is_package=path.stem == "__init__")
    return _Module(path, name, imports, tuple(bodies))


@dataclass(frozen=True)
class _Call:
    """A call a function makes by a plain name, kept without its tree.

    The function it reaches, by the module that defines it, and the names
    each argument is read from: in order for the positional ones, by keyword
    for the rest.
    """

    target: str
    positional: tuple[frozenset[str], ...]
    keywords: tuple[tuple[str | None, frozenset[str]], ...]


@dataclass(frozen=True)
class _Signature:
    """What the search for the checks of the package needs of one function."""

    dotted: str
    positional: tuple[str, ...]
    parameters: frozenset[str]
    calls: tuple[_Call, ...]


def _names_of(argument: ast.expr) -> frozenset[str]:
    return frozenset(_roots(argument, fields=False))


def _signatures(path: pathlib.Path) -> list[_Signature]:
    """The functions at the top of the module at *path*, each without its tree.

    A method is called through an object the rule does not follow, so only
    a function at the top of a module can be a check of its own.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    name = _module_name(path)
    imports = _imports(tree, name, is_package=path.stem == "__init__")
    found = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        calls = tuple(
            _Call(
                imports.get(call.func.id, f"{name}.{call.func.id}"),
                tuple(_names_of(argument) for argument in call.args),
                tuple((k.arg, _names_of(k.value)) for k in call.keywords),
            )
            for call in _own_nodes(node)
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
        )
        arguments = node.args
        positional = tuple(a.arg for a in arguments.posonlyargs + arguments.args)
        found.append(
            _Signature(
                f"{name}.{node.name}",
                positional,
                frozenset(_parameters(node)),
                calls,
            )
        )
    return found


@dataclass(frozen=True)
class Check:
    """A function that checks some of its parameters for a complex value.

    A shared check of :data:`CHECKS` lists no parameters, and checks every
    argument it is given (the value; the name or the message beside it is
    no caller's number). A function of the library lists its positional
    parameters in order and the ones it hands to a check.
    """

    parameters: tuple[str, ...] = ()
    checked: frozenset[str] = frozenset()

    def arguments(self, call: ast.Call) -> list[ast.expr]:
        """The arguments of *call* this check reads."""
        if not self.parameters:
            return [*call.args, *(k.value for k in call.keywords)]
        found = [
            argument
            for name, argument in zip(self.parameters, call.args, strict=False)
            if name in self.checked
        ]
        return found + [k.value for k in call.keywords if k.arg in self.checked]

    def names(self, call: _Call) -> frozenset[str]:
        """The names the arguments of *call* this check reads are read from."""
        if not self.parameters:
            read = [*call.positional, *(names for _, names in call.keywords)]
        else:
            read = [
                names
                for name, names in zip(self.parameters, call.positional, strict=False)
                if name in self.checked
            ]
            read += [names for name, names in call.keywords if name in self.checked]
        return frozenset().union(*read)


def _checker(
    module: _Module, checks: Mapping[str, Check]
) -> Callable[[ast.Call], list[ast.expr]]:
    """The arguments a call made in *module* hands to a check, by the module
    that defines the check.
    """

    def checked_by(call: ast.Call) -> list[ast.expr]:
        if not isinstance(call.func, ast.Name):
            return []
        name = call.func.id
        check = checks.get(module.imports.get(name, f"{module.name}.{name}"))
        return [] if check is None else check.arguments(call)

    return checked_by


def package_checks(signatures: Sequence[_Signature]) -> dict[str, Check]:
    """Every check of the package, shared and local, by the module that defines it.

    The shared :data:`CHECKS`, then each function of *signatures* that hands
    a parameter to a check already found, until no new one turns up.
    """
    checks = {f"{SHARED}.{name}": Check() for name in CHECKS}
    grown = True
    while grown:
        grown = False
        for signature in signatures:
            # Every function is read on each pass, a check found early or not.
            grown = _grow(signature, checks) or grown
    return checks


def _grow(signature: _Signature, checks: dict[str, Check]) -> bool:
    """Make the function of *signature* a check, or widen it, when it hands a
    parameter to one.

    :return: Whether a check was added or widened.
    """
    previous = checks.get(signature.dotted)
    if previous is not None and not previous.parameters:
        return False
    read = [checks[c.target].names(c) for c in signature.calls if c.target in checks]
    checked = frozenset().union(*read) & signature.parameters
    if not checked or (previous is not None and checked == previous.checked):
        return False
    checks[signature.dotted] = Check(signature.positional, checked)
    return True


def conversions_in(module: _Module, checks: Mapping[str, Check]) -> list[Conversion]:
    """Every conversion to floats in *module*, with what it reads."""
    checked_by = _checker(module, checks)
    found: list[Conversion] = []
    for body in module.bodies:
        function = body.function
        scope = _Function(function, checked_by, fields=function.name == "__post_init__")
        _events(scope, body.nodes)
        for node in body.calls:
            if (value := converted(node)) is None:
                continue
            verdict = _verdict(scope, value, _start(node))
            found.append(
                Conversion(
                    module.path,
                    node.lineno,
                    body.qualified,
                    ast.unparse(value),
                    verdict,
                )
            )
    return sorted(found, key=lambda c: (relative(c.path), c.line, c.source))


def census(paths: Iterable[pathlib.Path], *, library: bool = True) -> list[Conversion]:
    """Every conversion to floats under *paths*, with what each reads.

    The checks are found across the files read and, with *library*, across
    the whole library too, so that a file read alone still knows the checks
    the package defines. Each module is parsed twice, once for the checks it
    defines and once for its conversions, and one at a time, so that no more
    than one tree is held at once.
    """
    read = [path.resolve() for path in paths]
    sources = set(read)
    if library:
        sources |= {path.resolve() for path in SOURCE.rglob("*.py")}
    checks = package_checks([s for path in sorted(sources) for s in _signatures(path)])
    return [c for path in read for c in conversions_in(_module(path), checks)]


def unchecked(
    paths: Iterable[pathlib.Path], exempt: Mapping[tuple[str, str], str] | None = None
) -> tuple[list[Conversion], list[tuple[str, str]]]:
    """The conversions of a caller's value no check precedes, and stale exemptions."""
    found = [c for c in census(paths) if c.verdict == "unchecked"]
    return exempted(found, EXEMPT if exempt is None else exempt)


def main(argv: Sequence[str] | None = None) -> int:
    """Report each unchecked conversion of a caller's value; with --census, all."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", help="files or directories to read")
    parser.add_argument(
        "--census", action="store_true", help="print every conversion and what it reads"
    )
    arguments = parser.parse_args(argv)
    files = python_files(arguments.paths, SOURCE)
    if arguments.census:
        for conversion in census(files):
            print(conversion.describe())
        return 0
    left, stale = unchecked(files, EXEMPT if not arguments.paths else {})
    for conversion in left:
        print(conversion.describe())
    for key in stale:
        print(f"{key[0]}  {key[1]}  exemption that covers nothing")
    if left or stale:
        print(
            f"{len(left)} conversion(s) to floats read a caller's value no check "
            "has read: read it through real_array(value, name) of "
            "phonometry._internal.validation, or check it first.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
