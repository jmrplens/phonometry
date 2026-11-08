#  Copyright (c) 2026. Jose Manuel Requena Plens
"""List every numpy array or scalar type the package annotates without its type arguments.

numpy gives :class:`numpy.ndarray`, :class:`numpy.dtype` and the abstract scalar
types (:class:`numpy.number`, :class:`numpy.integer`, :class:`numpy.floating`,
:class:`numpy.complexfloating` and the others of :data:`TYPE_ARGUMENTS`)
default type arguments only from 2.3, and the package runs on numpy from 2.0.2
(2.1.0 on Python 3.13). There a type checker reads a bare ``np.ndarray`` as
``ndarray[Unknown, Unknown]`` and a bare ``np.floating`` as
``floating[Unknown]``: every public name annotated with one is partly unknown
to it, and mypy reports a ``[type-arg]`` error for each. ``NDArray`` written
alone is an array of an unknown dtype on every numpy.

The check reads every type expression of ``src/phonometry``: the annotation of
each parameter, ``*args`` and ``**kwargs`` among them, and of each return; of
each annotated assignment, a dataclass field, a variable or a module constant;
the value of a type alias, ``type X = ...``, ``X: TypeAlias = ...``, a plain
``X = ...`` at the top of a module whose value is a ``|`` union or a subscript,
which a type checker reads as an alias whether or not an annotation names it
(``_REAL = float | np.integer``, held for an ``isinstance``), and any other
plain ``X = ...`` an annotation reads; the bound and the constraints of a type
parameter; and the type handed to ``typing.cast``, ``typing.TypeVar``,
``typing.NewType`` and ``typing.assert_type``. An annotation written as a
string is read as the expression it holds; what a ``Literal`` holds is a value
and is not read, nor is the metadata of an ``Annotated``. A name is read as
Python reads it where it is written, through the imports of the module and of
each function around it and through the package's own re-exports
(:class:`check_return_overloads.Package`), so ``np.ndarray``,
``numpy.ndarray``, ``from numpy import ndarray as Array`` and ``npt.NDArray``
are one type; a type alias is read once, where it is defined, and an
annotation that names it reports nothing of its own.

Each finding has one of three kinds:

- **bare**: a type of :data:`TYPE_ARGUMENTS` written alone, or with fewer type
  arguments than it takes below numpy 2.3 (``np.complexfloating[Any]``, which
  takes two there, the precision of the real and of the imaginary part).
- **open**: an array whose dtype is left open, ``NDArray[Any]``,
  ``NDArray[np.generic]``, ``np.ndarray[..., Any]``, ``np.dtype[Any]`` or
  ``np.dtype[np.generic]``. It is complete, and right only where the array
  really takes several dtypes.
- **generic**: ``np.generic`` anywhere else, a scalar of any type or the bound
  of a type parameter. It takes no type argument below numpy 2.3 and is
  complete.

The second and the third are listed for review and never fail. A bare one
fails the check (:data:`REFUSES_BARE`); ``--refuse`` fails on it in a run of a
copy that turns the constant off. A file or a directory named on the
command line narrows what is listed to it; the whole package is read all the
same, so that a name it re-exports resolves.
"""

from __future__ import annotations

import argparse
import ast
import collections
import json
import pathlib
import sys
from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

import check_return_overloads as overloads
from ast_scan import ROOT, python_files, relative

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

#: The package the check reads.
SOURCE = ROOT / "src" / "phonometry"

#: Whether a bare type fails the check. On: the package writes none, and a
#: new one fails the check where it is written.
REFUSES_BARE = True

#: Each numpy type that takes type arguments with no default below numpy 2.3,
#: by the dotted name it resolves to, with how many it takes there. An array
#: takes its shape and its dtype, ``NDArray`` the scalar type of its items, a
#: complex scalar the precision of each of its two parts.
TYPE_ARGUMENTS: Mapping[str, int] = MappingProxyType(
    {
        "numpy.ndarray": 2,
        "numpy.memmap": 2,
        "numpy.matrix": 2,
        "numpy.recarray": 2,
        "numpy.rec.recarray": 2,
        "numpy.char.chararray": 2,
        "numpy.ma.MaskedArray": 2,
        "numpy.ma.core.MaskedArray": 2,
        "numpy.typing.NDArray": 1,
        "numpy.dtype": 1,
        "numpy.flatiter": 1,
        "numpy.number": 1,
        "numpy.integer": 1,
        "numpy.signedinteger": 1,
        "numpy.unsignedinteger": 1,
        "numpy.inexact": 1,
        "numpy.floating": 1,
        "numpy.complexfloating": 2,
    }
)

#: The arrays among :data:`TYPE_ARGUMENTS`, whose second argument is the dtype.
_ARRAYS = frozenset(name for name, count in TYPE_ARGUMENTS.items() if count == 2) - {
    "numpy.complexfloating"
}
_NDARRAY_ALIAS = "numpy.typing.NDArray"
_DTYPE = "numpy.dtype"
_GENERIC = "numpy.generic"
_ANNOTATED = frozenset({"typing.Annotated", "typing_extensions.Annotated"})
_TYPE_ALIAS = frozenset({"typing.TypeAlias", "typing_extensions.TypeAlias"})
#: The calls whose arguments are types, and which of their positions are.
_TYPE_CALLS: Mapping[str, slice] = MappingProxyType(
    {
        "typing.cast": slice(0, 1),
        "typing_extensions.cast": slice(0, 1),
        "typing.assert_type": slice(1, 2),
        "typing_extensions.assert_type": slice(1, 2),
        "typing.NewType": slice(1, 2),
        "typing_extensions.NewType": slice(1, 2),
        "typing.TypeVar": slice(1, None),
        "typing_extensions.TypeVar": slice(1, None),
    }
)

Kind = Literal["bare", "open", "generic"]
KINDS: tuple[Kind, ...] = ("bare", "open", "generic")


@dataclass(frozen=True)
class Finding:
    """One numpy type an annotation writes, and where."""

    #: The file, relative to the repository.
    path: str
    line: int
    column: int
    #: The qualified function or class that holds the annotation, or
    #: ``"<module>"``.
    scope: str
    #: What the annotation types: ``parameter x``, ``*args``, ``**kwargs``,
    #: ``return``, ``field x``, ``variable x``, ``alias X``, ``type parameter
    #: T``, ``cast``, ``assert_type``, ``NewType N``, ``TypeVar T``.
    slot: str
    kind: Kind
    #: The type as written, and the whole annotation it stands in.
    written: str
    annotation: str

    @property
    def key(self) -> tuple[str, str, str]:
        """The file, the scope and the slot: where a reader looks for it."""
        return self.path, self.scope, self.slot

    def line_text(self) -> str:
        """The finding on one line, as the report prints it."""
        return (
            f"{self.path}:{self.line}:{self.column + 1}: {self.kind}: "
            f"{self.written} in {self.scope} {self.slot}: {self.annotation}"
        )


@dataclass(frozen=True)
class _Site:
    """Where a type expression stands: its module, scope and slot."""

    module: str
    path: str
    scope: str
    slot: str
    #: What each name imported by the functions around it stands for.
    local: Mapping[str, str]


class _Reader:
    """Every type expression of a package, read through its imports and aliases."""

    def __init__(self, root: pathlib.Path) -> None:
        files = python_files([], root)
        self.package = overloads.Package(files, root)
        self.findings: list[Finding] = []
        self._seen: set[tuple[str, int, int, str]] = set()
        #: The aliases an annotation reads, by their dotted name.
        self._reached: set[str] = set()
        for path in files:
            module = overloads._module_name(path, root)
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            package = (
                module if path.name == "__init__.py" else module.rpartition(".")[0]
            )
            self._read_scope(tree, module, relative(path), package, "", {})
        self._read_aliases()
        self.findings.sort(key=lambda f: (f.path, f.line, f.column, f.kind))

    def _read_aliases(self) -> None:
        """Read the value of every plain alias a type checker reads, once each.

        A ``|`` union or a subscript at the top of a module is an alias to a
        type checker, read or not; a bare name or attribute is one when an
        annotation reads it. An alias read by another alias is read too, so
        the walk runs until no alias it meets is new.
        """
        self._reached |= {
            dotted
            for dotted, (_module, value) in self.package.aliases.items()
            if isinstance(value, ast.Subscript | ast.BinOp)
        }
        done: set[str] = set()
        while pending := self._reached - done:
            for dotted in sorted(pending):
                done.add(dotted)
                module, value = self.package.aliases[dotted]
                name = dotted.rpartition(".")[2]
                site = _Site(
                    module, self.package.paths[module], "<module>", f"alias {name}", {}
                )
                self._read_type(value, site, value)

    # The scope's place, and what it inherits: six arguments, each needed.
    def _read_scope(  # noqa: PLR0913
        self,
        node: ast.AST,
        module: str,
        path: str,
        package: str,
        scope: str,
        local: Mapping[str, str],
    ) -> None:
        """Read every type expression a scope writes, and the scopes inside it.

        :param local: What the names imported by the functions around *node*
            stand for; a function adds what it imports itself.
        """
        owner = "field" if isinstance(node, ast.ClassDef) else "variable"
        nodes = _own_nodes(node)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            # A body reads what the function imports for itself as well.
            local = {**local, **overloads._imports(nodes, package, into={})}
        site = _Site(module, path, scope or "<module>", "", local)
        for child in nodes:
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                inner = f"{scope}.{child.name}" if scope else child.name
                # A signature is read where the definition stands.
                self._read_definition(child, _Site(module, path, inner, "", local))
                self._read_scope(child, module, path, package, inner, local)
            elif isinstance(child, ast.AnnAssign):
                self._read_annotated(child, site, owner)
            elif isinstance(child, ast.TypeAlias):
                self._read_type_alias(child, site)
            elif isinstance(child, ast.Call):
                self._read_call(child, site)

    def _read_definition(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef, own: _Site
    ) -> None:
        """Read a definition's signature and the bounds of its type parameters."""
        for parameter in node.type_params:
            self._read_bound(parameter, own)
        if isinstance(node, ast.ClassDef):
            return
        arguments = node.args
        for argument in [
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        ]:
            if argument.annotation is not None:
                self._read_type(
                    argument.annotation,
                    _slot(own, f"parameter {argument.arg}"),
                    argument.annotation,
                )
        for prefix, star in (("*", arguments.vararg), ("**", arguments.kwarg)):
            if star is not None and star.annotation is not None:
                self._read_type(
                    star.annotation, _slot(own, f"{prefix}{star.arg}"), star.annotation
                )
        if node.returns is not None:
            self._read_type(node.returns, _slot(own, "return"), node.returns)

    def _read_bound(self, parameter: ast.type_param, site: _Site) -> None:
        """Read the bound of a type parameter, or the tuple of its constraints."""
        if isinstance(parameter, ast.TypeVar) and parameter.bound is not None:
            self._read_type(
                parameter.bound,
                _slot(site, f"type parameter {parameter.name}"),
                parameter.bound,
            )

    def _read_annotated(self, node: ast.AnnAssign, site: _Site, owner: str) -> None:
        """Read an annotated assignment: its annotation, or the alias it declares.

        :param owner: ``"field"`` in a class body, ``"variable"`` elsewhere.
        """
        target = ast.unparse(node.target)
        if self._resolve(node.annotation, site) in _TYPE_ALIAS:
            if node.value is not None:
                self._read_type(node.value, _slot(site, f"alias {target}"), node.value)
            return
        self._read_type(
            node.annotation, _slot(site, f"{owner} {target}"), node.annotation
        )

    def _read_type_alias(self, node: ast.TypeAlias, site: _Site) -> None:
        """Read a ``type`` statement: its value and the bounds of its parameters."""
        for parameter in node.type_params:
            self._read_bound(parameter, site)
        name = ast.unparse(node.name)
        self._read_type(node.value, _slot(site, f"alias {name}"), node.value)

    def _read_call(self, node: ast.Call, site: _Site) -> None:
        """Read the types a call of :data:`_TYPE_CALLS` is handed."""
        called = self._resolve(node.func, site)
        if called is None or called not in _TYPE_CALLS:
            return
        short = called.rpartition(".")[2]
        named = node.args[0] if node.args else None
        label = short
        if (
            short in {"TypeVar", "NewType"}
            and isinstance(named, ast.Constant)
            and isinstance(named.value, str)
        ):
            label = f"{short} {named.value}"
        types = list(node.args[_TYPE_CALLS[called]])
        if short == "TypeVar":
            types += [kw.value for kw in node.keywords if kw.arg == "bound"]
        for written in types:
            self._read_type(written, _slot(site, label), written)

    def _resolve(self, node: ast.expr, site: _Site) -> str | None:
        """The dotted name a name or an attribute chain stands for where it is read."""
        return self.package.resolve(site.module, node, dict(site.local) or None)

    def _report(self, node: ast.expr, site: _Site, kind: Kind, whole: ast.expr) -> None:
        """Keep a finding, once for each place and kind however it was reached."""
        place = (site.path, node.lineno, node.col_offset, kind)
        if place in self._seen:
            return
        self._seen.add(place)
        self.findings.append(
            Finding(
                path=site.path,
                line=node.lineno,
                column=node.col_offset,
                scope=site.scope,
                slot=site.slot,
                kind=kind,
                written=ast.unparse(node),
                annotation=ast.unparse(whole),
            )
        )

    def _read_type(self, node: ast.expr, site: _Site, whole: ast.expr) -> None:
        """Report what a type expression writes of numpy, at any depth."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                parsed = ast.parse(node.value, mode="eval").body
            except SyntaxError:
                return
            for inner in ast.walk(parsed):
                if isinstance(inner, ast.expr):
                    # Where the reader finds it: inside the string, after its quote.
                    first = inner.lineno == 1
                    inner.lineno = node.lineno + inner.lineno - 1
                    inner.col_offset += node.col_offset + 1 if first else 0
            self._read_type(parsed, site, whole)
            return
        if isinstance(node, ast.Subscript):
            self._read_subscript(node, site, whole)
            return
        if isinstance(node, ast.Name | ast.Attribute):
            dotted = self._resolve(node, site)
            if dotted in TYPE_ARGUMENTS:
                self._report(node, site, "bare", whole)
            elif dotted == _GENERIC:
                self._report(node, site, "generic", whole)
            elif dotted in self.package.aliases:
                self._reached.add(dotted)
            return
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                self._read_type(child, site, whole)

    def _read_subscript(
        self, node: ast.Subscript, site: _Site, whole: ast.expr
    ) -> None:
        """Report a subscripted type: its arity, its dtype, and what it is given."""
        base = self._resolve(node.value, site)
        items = _items(node)
        if base is None:
            pass
        elif base in overloads._LITERAL_FORMS:
            return
        elif base in _ANNOTATED:
            items = items[:1]
        elif base in TYPE_ARGUMENTS:
            if len(items) < TYPE_ARGUMENTS[base]:
                self._report(node, site, "bare", whole)
            dtype = None
            if base in _ARRAYS and len(items) == TYPE_ARGUMENTS[base]:
                dtype = items[1]
            elif base in {_NDARRAY_ALIAS, _DTYPE} and items:
                dtype = items[0]
            if dtype is not None and self._open(dtype, site, base):
                self._report(node, site, "open", whole)
                items = [item for item in items if item is not dtype]
        elif base in self.package.aliases:
            self._reached.add(base)
        if not isinstance(node.value, ast.Name | ast.Attribute):
            self._read_type(node.value, site, whole)
        for item in items:
            self._read_type(item, site, whole)

    def _open(self, dtype: ast.expr, site: _Site, base: str) -> bool:
        """Whether the dtype argument of *base* leaves the dtype open.

        ``Any`` does, and so does ``np.generic`` where a scalar type is the
        argument (``NDArray`` and ``np.dtype``); an array's ``np.dtype[...]``
        argument is read as a ``np.dtype`` of its own.
        """
        resolved = self._resolve(dtype, site)
        if resolved in overloads._ANY:
            return True
        return base in {_NDARRAY_ALIAS, _DTYPE} and resolved == _GENERIC


def _own_nodes(scope: ast.AST) -> list[ast.AST]:
    """The nodes a scope holds: the definitions in it, but nothing inside them.

    A lambda or a comprehension opens no scope an annotation stands in, so
    what it holds is read with the scope around it.
    """
    found: list[ast.AST] = []
    pending = list(ast.iter_child_nodes(scope))
    while pending:
        node = pending.pop()
        found.append(node)
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            pending.extend(ast.iter_child_nodes(node))
    return found


def _slot(site: _Site, slot: str) -> _Site:
    """The site with its slot named."""
    return _Site(site.module, site.path, site.scope, slot, site.local)


def _items(node: ast.Subscript) -> list[ast.expr]:
    """The arguments of a subscript, one or several."""
    inner = node.slice
    return list(inner.elts) if isinstance(inner, ast.Tuple) else [inner]


def findings_in(root: pathlib.Path = SOURCE) -> list[Finding]:
    """Every numpy type the type expressions of the package under *root* write.

    :param root: The package directory, ``src/phonometry`` by default.
    :return: The findings, by file and place.
    """
    return _Reader(root).findings


def _narrowed(findings: Sequence[Finding], paths: Sequence[str]) -> list[Finding]:
    """The findings in the files and directories named, all of them for none."""
    if not paths:
        return list(findings)
    wanted = [relative(pathlib.Path(path)) for path in paths]
    return [
        finding
        for finding in findings
        if any(
            finding.path == place or finding.path.startswith(place.rstrip("/") + "/")
            for place in wanted
        )
    ]


def counts(findings: Sequence[Finding]) -> dict[str, dict[str, int]]:
    """How many findings of each kind each file holds."""
    by_file: dict[str, collections.Counter[str]] = collections.defaultdict(
        collections.Counter
    )
    for finding in findings:
        by_file[finding.path][finding.kind] += 1
    return {
        path: {kind: by_file[path][kind] for kind in KINDS} for path in sorted(by_file)
    }


def _summary(findings: Sequence[Finding]) -> str:
    """How many findings of each kind, in how many files."""
    kinds = collections.Counter(finding.kind for finding in findings)
    files = {finding.path for finding in findings}
    return (
        f"{kinds['bare']} bare, {kinds['open']} open and {kinds['generic']} generic "
        f"numpy types in {len(files)} files."
    )


def main(argv: Sequence[str] | None = None) -> int:
    """List the numpy types the package annotates, and fail on a bare one when asked."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "paths", nargs="*", help="files or directories to list; the package if none"
    )
    parser.add_argument(
        "--refuse",
        action="store_true",
        help="fail on a bare type, as the check will once none is left",
    )
    parser.add_argument(
        "--kind",
        choices=KINDS,
        action="append",
        help="list only findings of this kind (repeatable)",
    )
    parser.add_argument(
        "--json", type=pathlib.Path, help="also write the findings to this file"
    )
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=SOURCE,
        help="the package directory to read (src/phonometry)",
    )
    arguments = parser.parse_args(argv)

    findings = _narrowed(findings_in(arguments.root), arguments.paths)
    if arguments.json is not None:
        arguments.json.write_text(
            json.dumps([asdict(finding) for finding in findings], indent=1) + "\n",
            encoding="utf-8",
        )
    listed = [
        finding
        for finding in findings
        if arguments.kind is None or finding.kind in arguments.kind
    ]
    for finding in listed:
        print(finding.line_text())
    print(_summary(findings))
    bare = [finding for finding in findings if finding.kind == "bare"]
    if bare and (REFUSES_BARE or arguments.refuse):
        print(
            f"::error::{len(bare)} numpy type(s) written without their type "
            "arguments: write the dtype each array holds (NDArray[np.float64]), "
            "the precision a scalar type takes (np.floating[Any]), or "
            "NDArray[Any] where the array takes several dtypes."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
