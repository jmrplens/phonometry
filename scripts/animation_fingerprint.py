#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What each committed clip was drawn by, reduced to one hash per clip.

The figures are byte-compared: CI regenerates them and
``scripts/check_figures.py`` says whether the tree still matches. The clips
cannot be, for the reason ``make animations`` is a separate target -- an FDTD
simulation plus four video encodes per clip is minutes of CPU each, and the
encoders are not bit-reproducible across machines anyway. So a clip is
committed once and then keeps whatever it was drawn with, while the code that
draws it moves on underneath: the Spanish minus-sign repair reached only the
clips that happened to be re-rendered after it, and the twelve that were not
kept shipping an ASCII hyphen in their Spanish tick labels for months with
every gate green.

This module answers the same question ``check_figures.py`` answers for the
SVGs, without rendering anything: **is the committed clip older than the code
that draws it?** It reads the sources as text, resolves what each clip
actually depends on, and reduces that to a fingerprint. The renderer stamps
the fingerprint into :data:`MANIFEST` when it writes a clip
(:func:`stamp`), and ``scripts/check_animation_freshness.py`` recomputes it
in CI and compares. A stamp that no longer matches means the clip on disk was
drawn by code that has since changed.

What goes into a fingerprint
----------------------------

Only what can change a frame, and only the part of it the clip reaches:

* the clip's own ``animate_*`` function and, transitively, every function,
  class and module constant it names inside ``scripts/figures`` -- the module
  helpers, the shared clip tail (``figures/media.py``), the field builders,
  the translation machinery of ``figures/i18n.py`` -- and inside
  ``phonometry._plot``, the drawing code the clips share with the library's
  own renderers: the colours a fill or a quiet line is given against its
  page (``theme_fill``, ``theme_line``), the frequency axis, the dark map of
  a wave field. A name a function imports for itself is followed as one
  imported at the top of its module is. Reaching a name reaches every
  statement at the top of its module that binds it. And the rest of the top
  of every module whose top runs is hashed, in the order it stands, with
  what it names walked. Those modules are the module of a name the walk
  reaches, every package above one, and every module an import at the top
  of one, or in a function the walk reaches, names (the one a re-export
  passes a name through included), since Python runs each of them on
  import. Only a ``def``, a ``class``, an assignment to names that nothing
  else at the top binds and whose value calls nothing but a few pure
  constructors (:data:`_PURE_CALLS`), and an import of such names are left
  to the walk to reach by name. Everything else, whatever kind of statement
  it is, counts: ``figures.theme`` registers the dark field map in a bare
  call, a guarded import is hashed with its guard, a rebound name with each
  of its bindings, an assignment that calls something else with its value.
  So does what a ``def`` or ``class`` runs when it is defined, whether or
  not the walk reaches it: its decorators, a default that calls something,
  a class's bases and keywords and the statements of its body (a method's
  body runs later, and is left to the walk), except a decorator, a base or
  a keyword that only shapes what it is given (``property``,
  ``dataclass``, ``lru_cache``, a builtin exception and the like,
  :data:`_INERT_DEFINITIONS`) and a statement that does nothing. And so
  does what an import of a third-party module imports when no statement
  the clip reaches reads its name, since the import runs all the same,
  unless the code the clip reaches imports that module already (a module
  of the standard library changes nothing a frame is drawn with, and the
  library's own modules outside the walk are its physics, below);
* and inside ``phonometry.io``, the encode path every clip's frames go
  through (``write_video`` and the pipe into ffmpeg), except the encoder
  presets of ``quality``, which a clip's own encoder and options bypass;
* ``figures.theme.set_theme``, which is not called by the clip but decides
  the palette and the rcParams every frame is drawn with, and everything it
  reaches;
* the translation table entries the clip's own strings select (see
  :func:`_selected_translations`).

Three decisions keep the fingerprint from crying wolf, which matters more
here than anywhere else in the repo: a false positive costs a several-minute
re-render, so an alarm nobody believes would be worse than no alarm.

* **The hash is over the AST, not the source text.** Reformatting, a
  reflowed comment or a rewritten docstring cannot move it; only a change to
  what the code *does* can. Nor can the interpreter that reads it: the tree
  is printed without its empty lists, which is the one place Python 3.11 to
  3.14 print the same tree differently (:func:`_drop_empty_lists`).
* **An imported name is hashed as what it is bound to** (:class:`_Canonical`):
  ``_re.sub`` after ``import re as _re`` and ``re.sub`` after ``import re``
  hash alike, wherever the import stands, while ``plt.figure`` hashes as
  ``matplotlib.pyplot.figure`` or ``matplotlib.pylab.figure`` as the import
  says. An import tidy moves nothing; a changed target moves every clip that
  reaches a use of it. A name is read from the scope that binds it, as
  Python reads it; one that two imports bind, or an import and anything
  else, or an import under a condition, is hashed as written, with its
  imports and their conditions.
* **The two big translation tables are excluded wholesale** and re-entered
  entry by entry. ``_ES_EXACT`` has thousands of lines and changes with every
  figure that gains a Spanish string; hashing it whole would mark all
  forty-two clips stale every time any unrelated figure is translated.

Known gaps, deliberately
------------------------

* **The library's physics.** A clip calls ``phonometry`` for its numbers,
  and outside ``phonometry._plot`` and ``phonometry.io`` this walk does not
  follow the library, whether a clip calls a module of it or only imports
  one: such an import keeps no effect of its own. Extending it there would
  trade a real but rare miss for a constant stream of false positives from
  refactors that change no pixel, and a library change that moves a number
  moves the static figures with it, where ``check_figures.py`` does catch
  it. Drawing code is another matter: a change to the colour a helper picks
  moves no number and still redraws every clip that asks for it, so
  ``phonometry._plot`` is walked like ``scripts/figures``.

  A clip that steps one of the FDTD engines is the exception, because its
  frames *are* the engine's numbers. It is tied to the engines' golden
  digests (``engine-digests.json``, see ``scripts/engine_digests.py``),
  which change when what the engines compute changes and never when their
  source is only rewritten: a reworded error message in the engine would
  otherwise mark every field clip stale. A clip counts as one that steps an
  engine when anything it reaches imports ``phonometry.simulation``, by a
  relative import too, or names it (``phonometry.simulation.FDTD2D`` after
  ``import phonometry``).
* **Pattern translations reached only through an f-string.** The selection
  below matches a table pattern against the clip's literal text, and a label
  assembled at run time from several pieces may not be recognisable in the
  source. The code half still covers the usual case, because a string that
  gains a pattern normally gains it *because* the code that builds it
  changed.
* **The order of the bindings at the top of a module.** A name the top both
  imports and assigns counts as rebound whatever their order, which can call
  a clip stale for nothing but never hides a change.
"""

from __future__ import annotations

import ast
import contextlib
import copy
import dataclasses
import errno
import hashlib
import json
import pathlib
import sys
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

_SCRIPTS = pathlib.Path(__file__).resolve().parent

#: The stamped fingerprints, one ``<clip> <hash> <encoder>`` line per clip,
#: sorted.
#: Next to ``figure_language_baseline.txt``, which plays the same role for the
#: language gate: a committed statement about the generated assets that CI
#: checks the tree against.
MANIFEST = _SCRIPTS / "animation_fingerprints.txt"

#: The ffmpeg encoders a published clip may have been written by: both write
#: AV1, on an NVIDIA GPU or on a CPU (the CPU one is publishable as well).
ClipEncoder = Literal["av1_nvenc", "libsvtav1"]
CLIP_ENCODERS: tuple[ClipEncoder, ...] = ("av1_nvenc", "libsvtav1")

#: The package the walk starts in.
_PKG_NAME = "figures"

#: The library, which the walk follows only into the packages below (see
#: "Known gaps").
_LIBRARY = "phonometry"

#: The packages the walk stays inside: where each lives under the repository
#: root, and the dotted name it is imported under. ``phonometry._plot`` is the
#: drawing code of the library, which the clips call for their colours and
#: their axes; the rest of the library is physics (see "Known gaps").
#: ``phonometry.io`` is the encode path: a clip's frames go through
#: :func:`phonometry.io.write_video` into ffmpeg, so a change there can change
#: the file.
_PACKAGES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("scripts", "figures"), (_PKG_NAME,)),
    (("src", "phonometry", "_plot"), ("phonometry", "_plot")),
    (("src", "phonometry", "io"), ("phonometry", "io")),
)

#: Where the clip names are mapped to their builders.
_REGISTRY = "figures.registry"

#: Always part of every fingerprint: nothing calls it from inside a clip, but
#: it sets the rcParams and the palette each frame is drawn with.
_EXTRA_ROOTS = (("figures.theme", "set_theme"),)

#: The FDTD engines' golden digests, at the root of the repository
#: (``scripts/engine_digests.py``). A clip that steps an engine is tied to
#: them instead of to the engine's source; see "Known gaps".
ENGINE_DIGESTS = "engine-digests.json"

#: The translation tables, excluded from the code walk and re-entered per
#: clip by :func:`_selected_translations`.
_TABLES = (("figures.i18n", "_ES_EXACT"), ("figures.i18n", "_ES_PATTERNS"))

#: Reached from the clip tail, but incapable of changing a frame:
#: ``audit_figure`` only names the clip the translation audit attributes its
#: lookups to, so a change to that bookkeeping does not mark every clip
#: stale. The encoder *settings* a clip passes are not here: those do change
#: the file.
_IGNORED: frozenset[tuple[str, str]] = frozenset(
    {
        ("figures.i18n", "audit_figure"),
        # The encoder presets of write_video's ``quality``: the clips pass
        # their own encoder and options, which bypass them, so a preset
        # edit cannot change a clip and must not call them all stale.
        ("phonometry.io._video_quality", "ENCODER_QUALITY"),
    }
)

#: Shortest run of plain text in a table pattern that may select it. Shorter
#: runs (" dB", "°") appear in half the corpus and would attach unrelated
#: patterns to every clip.
_MIN_PATTERN_RUN = 4

#: Shortest half of a run split across an interpolation (see
#: :func:`_run_is_written`).
_MIN_SPLIT = 3

Symbol = tuple[str, str]


class _Module:
    """One parsed source file of the walk."""

    def __init__(
        self,
        name: str,
        tree: ast.Module,
        owner: Sources,
        annotation_names: frozenset[str] = frozenset(),
    ) -> None:
        self.name = name
        self.tree = tree
        self.owner = owner
        #: the names the module's annotations read, taken before
        #: :class:`_RuntimeView` strips them
        self.annotation_names = annotation_names

    def _resolve_import(self, node: ast.ImportFrom) -> str:
        """The absolute module name of a ``from ... import`` statement.

        ``""`` for one that climbs past the top package, which Python
        refuses to import.
        """
        if not node.level:
            return node.module or ""
        parts = self.name.split(".")
        # A package's ``__init__`` is addressed by the package name itself, so
        # one level up from a module is one part off its dotted name.
        keep = len(parts) - node.level + (1 if self.is_package else 0)
        if keep < 1:
            return ""
        return ".".join(parts[:keep] + ([node.module] if node.module else []))

    @property
    def is_package(self) -> bool:
        return self.name in self.owner.packages


def _import_bindings(
    module: _Module, node: ast.Import | ast.ImportFrom
) -> Iterator[tuple[str, str]]:
    """``(name, dotted name)`` for each name *node*, an import in *module*, binds.

    As Python binds them: ``import a.b`` binds ``a`` to ``a``, ``import a.b
    as x`` binds ``x`` to ``a.b``, ``from m import n as x`` binds ``x`` to
    ``m.n`` (a relative ``m`` read from *module*). A relative import that
    names no module (:meth:`_Module._resolve_import`) binds nothing.
    """
    if isinstance(node, ast.Import):
        for alias in node.names:
            head = alias.name.split(".")[0]
            yield (alias.asname, alias.name) if alias.asname else (head, head)
        return
    base = module._resolve_import(node)
    if base:
        for alias in node.names:
            if alias.name != "*":
                yield alias.asname or alias.name, f"{base}.{alias.name}"


#: The modules whose imports only a type checker or the compiler reads
#: (``from __future__ import annotations``): they import nothing a frame
#: could show.
_TYPING_MODULES = frozenset({"__future__", "typing", "typing_extensions"})


def _annotation_names(tree: ast.AST) -> frozenset[str]:
    """Every name the annotations of *tree* read, a quoted annotation included."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.arg | ast.AnnAssign):
            annotation = node.annotation
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            annotation = node.returns
        else:
            continue
        if annotation is not None:
            found |= _names_in_annotation(annotation)
    return frozenset(found)


def _names_in_annotation(annotation: ast.expr) -> set[str]:
    """The names *annotation* reads, those of a quoted annotation included."""
    found: set[str] = set()
    for node in ast.walk(annotation):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            with contextlib.suppress(SyntaxError):
                found |= _names_in_annotation(ast.parse(node.value, mode="eval").body)
    return found


def _exported(tree: ast.Module) -> set[str]:
    """The names the module's ``__all__`` lists."""
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign | ast.AugAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
                found |= {
                    element.value
                    for element in ast.walk(node.value)
                    if isinstance(element, ast.Constant)
                    and isinstance(element.value, str)
                }
    return found


def _import_effects(
    module: _Module, node: ast.Import | ast.ImportFrom
) -> Iterator[tuple[str, str, str]]:
    """``(name, target, what is imported)`` for each name *node* binds.

    The name and its dotted target as :func:`_import_bindings` reads them
    (the target ``""`` for a relative module that climbs past the top
    package), and what the statement says for it, ``import json as _codec``
    or ``from json import dumps``: what is kept of an import whose name no
    use stands for.
    """
    if isinstance(node, ast.Import):
        for alias in node.names:
            head = alias.name.split(".")[0]
            target = alias.name if alias.asname else head
            yield alias.asname or head, target, f"import {alias.name}{_as(alias)}"
        return
    base = module._resolve_import(node)
    written = base or "." * node.level + (node.module or "")
    for alias in node.names:
        said = f"from {written} import {alias.name}{_as(alias)}"
        yield alias.asname or alias.name, f"{base}.{alias.name}" if base else "", said


def _as(alias: ast.alias) -> str:
    """`` as x`` for an alias that renames what it imports, else nothing."""
    return f" as {alias.asname}" if alias.asname else ""


def _effect(effect: str) -> ast.stmt:
    """The statement that stands for the import *effect* in a dumped tree.

    A name no source can spell, ``<import mpl_toolkits.mplot3d>``, rather than
    a string: a string first in a body would be taken for a docstring and
    stripped, losing the import, or would be kept where a docstring was
    removed above it.
    """
    return ast.Expr(value=ast.Name(id=f"<{effect}>", ctx=ast.Load()))


def _is_effect(node: ast.AST) -> bool:
    """Whether *node* is a statement :func:`_effect` made."""
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Name)
        and node.value.id.startswith("<")
    )


@dataclasses.dataclass(frozen=True)
class _Binding:
    """One way a scope gives a name its value: an import, or anything else."""

    #: what an import binds the name to; "" for any other binding (a
    #: ``def``, an assignment, a parameter) and for an import of no module
    target: str
    #: inside an ``if``, ``try``, ``with``, ``for``, ``while`` or ``match`` of
    #: its scope, so that it may or may not be the binding a read meets
    guarded: bool
    #: what the import says for the name (:func:`_import_effects`); "" for a
    #: binding that is no import
    effect: str = ""


class _Scope:
    """The names one scope binds: the module, a class body, or a function, lambda or comprehension."""

    def __init__(
        self,
        kind: Literal["module", "class", "function", "comprehension"],
        parent: _Scope | None,
    ) -> None:
        self.kind = kind
        self.parent = parent
        self.bindings: dict[str, list[_Binding]] = {}
        self.global_names: set[str] = set()
        self.nonlocal_names: set[str] = set()

    def clean(self, name: str) -> str:
        """What *name* is bound to when one import, run whatever happens, is all that binds it here; "" otherwise.

        Only such a name is read as its target. A name two imports bind, or an
        import and an assignment, or an import under an ``if`` or a ``try``,
        is read as it is written, and its imports stay in the dump.
        """
        bindings = self.bindings.get(name, [])
        if len(bindings) == 1 and bindings[0].target and not bindings[0].guarded:
            return bindings[0].target
        return ""

    def owner(self, name: str, top: _Scope) -> _Scope | None:
        """The scope a read of *name* here reads from, as Python finds it; None for a builtin.

        This scope first, unless it declares the name global; then the
        enclosing functions, never a class body (a method does not see the
        names of its class); then the module.
        """
        if name in self.global_names:
            return top if name in top.bindings else None
        if name in self.bindings and name not in self.nonlocal_names:
            return self
        scope = self.parent
        while scope is not None:
            if scope.kind != "class" and name in scope.bindings:
                return scope
            scope = scope.parent
        return None


def _enclosing_function(scope: _Scope, name: str) -> _Scope:
    """The function a ``nonlocal`` *name* in *scope* binds in: the nearest enclosing one that binds it.

    The nearest enclosing function when none binds it yet (its binding may
    come later in its body); *scope* itself where there is no enclosing
    function, which Python refuses to compile.
    """
    nearest = None
    outer = scope.parent
    while outer is not None:
        if outer.kind == "function":
            if name in outer.bindings:
                return outer
            nearest = nearest or outer
        outer = outer.parent
    return nearest or scope


def _parameters(args: ast.arguments) -> list[str]:
    """The names *args* binds in the function's own scope."""
    every = [*args.posonlyargs, *args.args, *args.kwonlyargs]
    every += [arg for arg in (args.vararg, args.kwarg) if arg is not None]
    return [arg.arg for arg in every]


class _ScopeBuilder(ast.NodeVisitor):
    """Every binding of a module, in the scope Python gives it, and every read with the scope it is made in."""

    def __init__(self, module: _Module) -> None:
        self.module = module
        self.top = _Scope("module", None)
        self.scope = self.top
        #: how many compound statements of the current scope enclose the visit
        self.depth = 0
        self.reads: list[tuple[ast.Name, _Scope]] = []
        #: every import, with its scope and whether it is guarded there
        self.imports: list[tuple[ast.Import | ast.ImportFrom, _Scope, bool]] = []
        #: id of a statement -> every name it binds in the scope whose body
        #: holds it (the module, a class body)
        self.binds: dict[int, set[str]] = {}
        #: id of a scope -> the entry of its own body being visited
        self.statements: dict[int, ast.AST] = {}
        #: id of a class statement -> the scope of its body
        self.class_scopes: dict[int, _Scope] = {}
        #: id of the scope of a class body -> its class statement
        self.class_nodes: dict[int, ast.ClassDef] = {}

    def visit_Module(self, node: ast.Module) -> None:
        for statement in node.body:
            self.statements[id(self.top)] = statement
            self.visit(statement)

    def _bind(self, name: str, binding: _Binding, scope: _Scope | None = None) -> None:
        """Record *binding* of *name* in *scope* (the current one by default), or where ``global`` or ``nonlocal`` sends it."""
        scope = scope or self.scope
        if name in scope.global_names:
            scope = self.top
        elif name in scope.nonlocal_names:
            scope = _enclosing_function(scope, name)
        scope.bindings.setdefault(name, []).append(binding)
        statement = self.statements.get(id(scope))
        if statement is not None:
            self.binds.setdefault(id(statement), set()).add(name)

    def _nested(
        self,
        kind: Literal["class", "function", "comprehension"],
        names: Iterable[str],
        body: Iterable[ast.AST],
    ) -> _Scope:
        outer, depth = self.scope, self.depth
        scope = _Scope(kind, outer)
        self.scope, self.depth = scope, 0
        for name in names:
            self._bind(name, _Binding("", guarded=False))
        for node in body:
            self.statements[id(scope)] = node
            self.visit(node)
        self.scope, self.depth = outer, depth
        return scope

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.reads.append((node, self.scope))
        else:
            self._bind(node.id, _Binding("", guarded=self.depth > 0))

    def _import(self, node: ast.Import | ast.ImportFrom) -> None:
        self.imports.append((node, self.scope, self.depth > 0))
        for name, target, effect in _import_effects(self.module, node):
            self._bind(name, _Binding(target, self.depth > 0, effect))

    visit_Import = _import
    visit_ImportFrom = _import

    def visit_Global(self, node: ast.Global) -> None:
        self.scope.global_names.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.scope.nonlocal_names.update(node.names)

    def _function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    ) -> None:
        # The name, the decorators and the defaults belong to the enclosing scope.
        if not isinstance(node, ast.Lambda):
            self._bind(node.name, _Binding("", guarded=self.depth > 0))
            for decorator in node.decorator_list:
                self.visit(decorator)
        for default in [*node.args.defaults, *node.args.kw_defaults]:
            if default is not None:
                self.visit(default)
        body = [node.body] if isinstance(node, ast.Lambda) else node.body
        self._nested("function", _parameters(node.args), body)

    visit_FunctionDef = _function
    visit_AsyncFunctionDef = _function
    visit_Lambda = _function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._bind(node.name, _Binding("", guarded=self.depth > 0))
        for part in [
            *node.decorator_list,
            *node.bases,
            *(k.value for k in node.keywords),
        ]:
            self.visit(part)
        scope = self._nested("class", (), node.body)
        self.class_scopes[id(node)] = scope
        self.class_nodes[id(scope)] = node

    def _comprehension(
        self, node: ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp
    ) -> None:
        # The first iterable is read where the comprehension stands.
        first, *rest = node.generators
        self.visit(first.iter)
        produced = (
            [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
        )
        self._nested("comprehension", (), [first.target, *first.ifs, *rest, *produced])

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        # PEP 572: the target binds in the nearest scope that is no
        # comprehension (a class body's comprehension may not hold one).
        self.visit(node.value)
        scope = self.scope
        while scope.kind == "comprehension" and scope.parent is not None:
            scope = scope.parent
        self._bind(node.target.id, _Binding("", guarded=self.depth > 0), scope)

    visit_ListComp = _comprehension
    visit_SetComp = _comprehension
    visit_GeneratorExp = _comprehension
    visit_DictComp = _comprehension

    def _guarded(self, node: ast.AST) -> None:
        self.depth += 1
        self.generic_visit(node)
        self.depth -= 1

    visit_For = _guarded
    visit_AsyncFor = _guarded
    visit_While = _guarded
    visit_With = _guarded
    visit_AsyncWith = _guarded
    visit_Try = _guarded
    visit_TryStar = _guarded
    visit_Match = _guarded

    def visit_If(self, node: ast.If) -> None:
        if not _is_type_checking(node.test):
            self._guarded(node)
            return
        # Only a type checker reads the body; it binds nothing at run time.
        self.depth += 1
        for statement in node.orelse:
            self.visit(statement)
        self.depth -= 1

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self._bind(node.name, _Binding("", guarded=True))
        self.generic_visit(node)

    def _pattern(self, node: ast.MatchAs | ast.MatchStar | ast.MatchMapping) -> None:
        name = node.rest if isinstance(node, ast.MatchMapping) else node.name
        if name:
            self._bind(name, _Binding("", guarded=True))
        self.generic_visit(node)

    visit_MatchAs = _pattern
    visit_MatchStar = _pattern
    visit_MatchMapping = _pattern


class _ScopeMap:
    """Where each read of a module reads from, and what each of its imports keeps in the dump."""

    def __init__(self, module: _Module) -> None:
        builder = _ScopeBuilder(module)
        builder.visit(module.tree)
        self.module = module
        self.top = builder.top
        #: id of a statement at the top or in a class body -> every name it
        #: binds in that scope, a ``global`` assignment in a function and a
        #: walrus target included
        self.binds = builder.binds
        #: id of a class statement -> the scope of its body
        self.class_scopes = builder.class_scopes
        #: id of the scope of a class body -> its class statement
        self.class_nodes = builder.class_nodes
        #: ids of the names read from the module's own scope
        self.top_reads: set[int] = set()
        #: id of a name read -> the dotted name it reads, where one import is
        #: all that binds it (:meth:`_Scope.clean`)
        self.canonical: dict[int, str] = {}
        #: id of a name read -> every dotted name it may read, for the walk
        self.candidates: dict[int, list[str]] = {}
        self._reads: set[tuple[int, str]] = set()
        self._targets: set[str] = set()
        for name, scope in builder.reads:
            self._read(name, scope)
        #: id of an import -> what its dump keeps of it
        self.kept: dict[int, list[str]] = {}
        #: the imports at the top of the module that no compound statement guards
        self.unguarded: list[ast.Import | ast.ImportFrom] = []
        for statement, scope, guarded in builder.imports:
            self.kept[id(statement)] = self._kept(statement, scope)
            if scope is self.top and not guarded:
                self.unguarded.append(statement)

    def _read(self, name: ast.Name, scope: _Scope) -> None:
        owner = scope.owner(name.id, self.top)
        if owner is None:
            return
        self._reads.add((id(owner), name.id))
        if owner is self.top:
            self.top_reads.add(id(name))
        target = owner.clean(name.id)
        if target:
            self.canonical[id(name)] = target
            self._targets.add(target)
        bindings = owner.bindings[name.id]
        found = [binding.target for binding in bindings if binding.target]
        if owner is self.top and any(not binding.effect for binding in bindings):
            found.append(f"{self.module.name}.{name.id}")
        self.candidates[id(name)] = found

    def _kept(self, statement: ast.Import | ast.ImportFrom, scope: _Scope) -> list[str]:
        """What the dump keeps of *statement*, one import in *scope*.

        Only the import of a clean name (:meth:`_Scope.clean`) can drop out:
        when something reads it, since its uses stand for it; and at the top of
        the module, when a use reads its target under another name, or when it
        is there for a type checker or for other modules
        (:meth:`Sources.for_types_or_others`). The imports of a guarded or
        rebound name always stay, as what each says: their uses are printed
        as written, so the kept imports are the only record of the targets.
        """
        kept = []
        for name, target, effect in _import_effects(self.module, statement):
            if not (scope.clean(name) and self._said(scope, name, target)):
                kept.append(effect)
        return kept

    def _said(self, scope: _Scope, name: str, target: str) -> bool:
        """Whether something other than the import itself says the clean import of *name* in *scope*."""
        if (id(scope), name) in self._reads:
            return True
        return scope is self.top and (
            target in self._targets
            or self.module.owner.for_types_or_others(self.module, name, target)
        )

    def read_from(self, node: ast.AST) -> list[str]:
        """Every dotted name *node* may read: a name, or an attribute chain off one."""
        attributes: list[str] = []
        value = node
        while isinstance(value, ast.Attribute):
            attributes.append(value.attr)
            value = value.value
        if not isinstance(value, ast.Name):
            return []
        suffix = "".join(f".{attribute}" for attribute in reversed(attributes))
        return [f"{dotted}{suffix}" for dotted in self.candidates.get(id(value), ())]


class _Canonical(ast.NodeTransformer):
    """A tree whose imported names read as the dotted names they are bound to.

    How a name is imported cannot change a frame; what it is bound to can.
    So ``_re.sub`` after ``import re as _re``, ``re.sub`` after ``import
    re`` and ``sub`` after ``from re import sub`` all read ``re.sub``, an
    import moved between a function and the top of its module reads the
    same, and ``plt.figure`` reads ``matplotlib.pyplot.figure`` or
    ``matplotlib.pylab.figure`` as the import says. A name is read from the
    scope that binds it (:class:`_ScopeMap`), so a parameter or a local of
    the same name is not the import, and only a name one unguarded import
    binds is read as its target. A name of the walk reads where it is
    defined (:meth:`Sources.canonical_name`). Each import keeps what
    :meth:`_ScopeMap._kept` says it keeps, as statements :func:`_effect`
    writes.
    """

    def __init__(
        self,
        sources: Sources,
        names: Mapping[int, str],
        kept: Mapping[int, list[str]],
    ) -> None:
        self.sources = sources
        #: id of a name in the tree -> the dotted name it reads
        self.names = names
        #: id of an import in the tree -> what is kept of it
        self.kept = kept

    def _named(self, node: ast.expr, dotted: str) -> ast.Name:
        name = ast.Name(id=self.sources.canonical_name(dotted), ctx=ast.Load())
        return ast.copy_location(name, node)

    def visit_Name(self, node: ast.Name) -> ast.expr:
        dotted = self.names.get(id(node))
        return self._named(node, dotted) if dotted else node

    def visit_Attribute(self, node: ast.Attribute) -> ast.expr:
        attributes: list[str] = []
        value: ast.expr = node
        while isinstance(value, ast.Attribute):
            attributes.append(value.attr)
            value = value.value
        root = self.names.get(id(value)) if isinstance(value, ast.Name) else None
        if root and isinstance(node.ctx, ast.Load):
            return self._named(node, ".".join([root, *reversed(attributes)]))
        self.generic_visit(node)
        return node

    def _import(self, node: ast.Import | ast.ImportFrom) -> list[ast.stmt]:
        # A name, never a string, so that a docstring strip cannot take it.
        return [_effect(effect) for effect in self.kept.get(id(node), [])]

    visit_Import = _import
    visit_ImportFrom = _import


def _imported_modules(
    module: _Module, node: ast.Import | ast.ImportFrom
) -> Iterator[str]:
    """The dotted names of the modules *node*, an import in *module*, may import.

    ``import a.b`` imports ``a.b``; ``from m import n`` imports ``m``, and
    ``m.n`` when that is a module (``from . import media``). A relative
    import that climbs past the top package names nothing. Each package
    above one of them runs too, which :meth:`Sources.runs` adds.
    """
    if isinstance(node, ast.Import):
        yield from (alias.name for alias in node.names)
        return
    base = module._resolve_import(node)
    if base:
        yield base
        yield from (f"{base}.{alias.name}" for alias in node.names)


#: What an assignment the walk takes by name may call: they build a value from
#: their arguments and change nothing a frame is drawn with. Anything else is
#: hashed with its module (:meth:`Sources._walked_in`).
_PURE_CALLS = frozenset(
    {
        "dataclasses.field",
        "dataclasses.fields",
        "float",
        "frozenset",
        "getattr",
        "logging.getLogger",
        "numpy.arange",
        "numpy.array",
        "numpy.dtype",
        "numpy.sqrt",
        "object",
        "os.path.abspath",
        "os.path.dirname",
        "re.compile",
        "round",
        "set",
        "struct.Struct",
        "threading.Lock",
        "tuple",
        "types.MappingProxyType",
        "typing.get_args",
        "weakref.WeakKeyDictionary",
    }
)


#: The modules of the standard library, on every version this runs on (3.12
#: to 3.14), so that an import counts alike on every machine.
_STANDARD_LIBRARY = frozenset(
    [
        "__future__",
        "_abc",
        "_aix_support",
        "_android_support",
        "_apple_support",
        "_ast",
        "_ast_unparse",
        "_asyncio",
        "_bisect",
        "_blake2",
        "_bz2",
        "_codecs",
        "_codecs_cn",
        "_codecs_hk",
        "_codecs_iso2022",
        "_codecs_jp",
        "_codecs_kr",
        "_codecs_tw",
        "_collections",
        "_collections_abc",
        "_colorize",
        "_compat_pickle",
        "_compression",
        "_contextvars",
        "_crypt",
        "_csv",
        "_ctypes",
        "_curses",
        "_curses_panel",
        "_datetime",
        "_dbm",
        "_decimal",
        "_elementtree",
        "_frozen_importlib",
        "_frozen_importlib_external",
        "_functools",
        "_gdbm",
        "_hashlib",
        "_heapq",
        "_hmac",
        "_imp",
        "_interpchannels",
        "_interpqueues",
        "_interpreters",
        "_io",
        "_ios_support",
        "_json",
        "_locale",
        "_lsprof",
        "_lzma",
        "_markupbase",
        "_md5",
        "_msi",
        "_multibytecodec",
        "_multiprocessing",
        "_opcode",
        "_opcode_metadata",
        "_operator",
        "_osx_support",
        "_overlapped",
        "_pickle",
        "_posixshmem",
        "_posixsubprocess",
        "_py_abc",
        "_py_warnings",
        "_pydatetime",
        "_pydecimal",
        "_pyio",
        "_pylong",
        "_pyrepl",
        "_queue",
        "_random",
        "_remote_debugging",
        "_scproxy",
        "_sha1",
        "_sha2",
        "_sha3",
        "_signal",
        "_sitebuiltins",
        "_socket",
        "_sqlite3",
        "_sre",
        "_ssl",
        "_stat",
        "_statistics",
        "_string",
        "_strptime",
        "_struct",
        "_suggestions",
        "_symtable",
        "_sysconfig",
        "_thread",
        "_threading_local",
        "_tkinter",
        "_tokenize",
        "_tracemalloc",
        "_types",
        "_typing",
        "_uuid",
        "_warnings",
        "_weakref",
        "_weakrefset",
        "_winapi",
        "_wmi",
        "_zoneinfo",
        "_zstd",
        "abc",
        "aifc",
        "annotationlib",
        "antigravity",
        "argparse",
        "array",
        "ast",
        "asyncio",
        "atexit",
        "audioop",
        "base64",
        "bdb",
        "binascii",
        "bisect",
        "builtins",
        "bz2",
        "cProfile",
        "calendar",
        "cgi",
        "cgitb",
        "chunk",
        "cmath",
        "cmd",
        "code",
        "codecs",
        "codeop",
        "collections",
        "colorsys",
        "compileall",
        "compression",
        "concurrent",
        "configparser",
        "contextlib",
        "contextvars",
        "copy",
        "copyreg",
        "crypt",
        "csv",
        "ctypes",
        "curses",
        "dataclasses",
        "datetime",
        "dbm",
        "decimal",
        "difflib",
        "dis",
        "doctest",
        "email",
        "encodings",
        "ensurepip",
        "enum",
        "errno",
        "faulthandler",
        "fcntl",
        "filecmp",
        "fileinput",
        "fnmatch",
        "fractions",
        "ftplib",
        "functools",
        "gc",
        "genericpath",
        "getopt",
        "getpass",
        "gettext",
        "glob",
        "graphlib",
        "grp",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "idlelib",
        "imaplib",
        "imghdr",
        "importlib",
        "inspect",
        "io",
        "ipaddress",
        "itertools",
        "json",
        "keyword",
        "lib2to3",
        "linecache",
        "locale",
        "logging",
        "lzma",
        "mailbox",
        "mailcap",
        "marshal",
        "math",
        "mimetypes",
        "mmap",
        "modulefinder",
        "msilib",
        "msvcrt",
        "multiprocessing",
        "netrc",
        "nis",
        "nntplib",
        "nt",
        "ntpath",
        "nturl2path",
        "numbers",
        "opcode",
        "operator",
        "optparse",
        "os",
        "ossaudiodev",
        "pathlib",
        "pdb",
        "pickle",
        "pickletools",
        "pipes",
        "pkgutil",
        "platform",
        "plistlib",
        "poplib",
        "posix",
        "posixpath",
        "pprint",
        "profile",
        "pstats",
        "pty",
        "pwd",
        "py_compile",
        "pyclbr",
        "pydoc",
        "pydoc_data",
        "pyexpat",
        "queue",
        "quopri",
        "random",
        "re",
        "readline",
        "reprlib",
        "resource",
        "rlcompleter",
        "runpy",
        "sched",
        "secrets",
        "select",
        "selectors",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "site",
        "smtplib",
        "sndhdr",
        "socket",
        "socketserver",
        "spwd",
        "sqlite3",
        "sre_compile",
        "sre_constants",
        "sre_parse",
        "ssl",
        "stat",
        "statistics",
        "string",
        "stringprep",
        "struct",
        "subprocess",
        "sunau",
        "symtable",
        "sys",
        "sysconfig",
        "syslog",
        "tabnanny",
        "tarfile",
        "telnetlib",
        "tempfile",
        "termios",
        "textwrap",
        "this",
        "threading",
        "time",
        "timeit",
        "tkinter",
        "token",
        "tokenize",
        "tomllib",
        "trace",
        "traceback",
        "tracemalloc",
        "tty",
        "turtle",
        "turtledemo",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uu",
        "uuid",
        "venv",
        "warnings",
        "wave",
        "weakref",
        "webbrowser",
        "winreg",
        "winsound",
        "wsgiref",
        "xdrlib",
        "xml",
        "xmlrpc",
        "zipapp",
        "zipfile",
        "zipimport",
        "zlib",
        "zoneinfo",
    ]
)

#: The exception classes Python builds in, on every version this runs on (3.12
#: to 3.14) and on every platform, so that what counts as one cannot differ
#: between machines. ``WindowsError`` is a builtin on Windows alone.
_BUILTIN_EXCEPTIONS = frozenset(
    [
        "ArithmeticError",
        "AssertionError",
        "AttributeError",
        "BaseException",
        "BaseExceptionGroup",
        "BlockingIOError",
        "BrokenPipeError",
        "BufferError",
        "BytesWarning",
        "ChildProcessError",
        "ConnectionAbortedError",
        "ConnectionError",
        "ConnectionRefusedError",
        "ConnectionResetError",
        "DeprecationWarning",
        "EOFError",
        "EncodingWarning",
        "EnvironmentError",
        "Exception",
        "ExceptionGroup",
        "FileExistsError",
        "FileNotFoundError",
        "FloatingPointError",
        "FutureWarning",
        "GeneratorExit",
        "IOError",
        "ImportError",
        "ImportWarning",
        "IndentationError",
        "IndexError",
        "InterruptedError",
        "IsADirectoryError",
        "KeyError",
        "KeyboardInterrupt",
        "LookupError",
        "MemoryError",
        "ModuleNotFoundError",
        "NameError",
        "NotADirectoryError",
        "NotImplementedError",
        "OSError",
        "OverflowError",
        "PendingDeprecationWarning",
        "PermissionError",
        "ProcessLookupError",
        "PythonFinalizationError",
        "RecursionError",
        "ReferenceError",
        "ResourceWarning",
        "RuntimeError",
        "RuntimeWarning",
        "StopAsyncIteration",
        "StopIteration",
        "SyntaxError",
        "SyntaxWarning",
        "SystemError",
        "SystemExit",
        "TabError",
        "TimeoutError",
        "TypeError",
        "UnboundLocalError",
        "UnicodeDecodeError",
        "UnicodeEncodeError",
        "UnicodeError",
        "UnicodeTranslateError",
        "UnicodeWarning",
        "UserWarning",
        "ValueError",
        "Warning",
        "WindowsError",
        "ZeroDivisionError",
    ]
)

#: What a decorator, a base or a class keyword may name without being hashed
#: with its module: they shape the function or the class they are given and
#: run nothing a frame is drawn with (see :meth:`Sources._inert`).
_INERT_DEFINITIONS = _BUILTIN_EXCEPTIONS | frozenset(
    {
        "abc.ABCMeta",
        "abc.abstractmethod",
        "classmethod",
        "collections.abc.Mapping",
        "dataclasses.dataclass",
        "enum.Enum",
        "enum.IntEnum",
        "enum.StrEnum",
        "functools.cache",
        "functools.cached_property",
        "functools.lru_cache",
        "object",
        "phonometry._internal.display.RichDisplay",
        "phonometry._internal.warnings.PhonometryWarning",
        "property",
        "staticmethod",
        "typing.Generic",
        "typing.NamedTuple",
        "typing.Protocol",
        "typing.final",
        "typing.overload",
    }
)


def _calls(node: ast.AST) -> Iterator[ast.Call]:
    """Every call evaluating *node* makes: none inside a lambda's body, which runs later."""
    if isinstance(node, ast.Lambda):
        arguments = node.args
        defaults = [*arguments.defaults, *arguments.kw_defaults]
        yield from (c for d in defaults if d is not None for c in _calls(d))
        return
    if isinstance(node, ast.Call):
        yield node
    for child in ast.iter_child_nodes(node):
        yield from _calls(child)


def _names_only(target: ast.expr) -> bool:
    """Whether the assignment target *target* is a name, or names unpacked (``_a, *_b``)."""
    if isinstance(target, ast.Starred):
        return _names_only(target.value)
    if isinstance(target, ast.Tuple | ast.List):
        return all(_names_only(element) for element in target.elts)
    return isinstance(target, ast.Name)


def _is_docstring(statement: ast.AST) -> bool:
    """Whether *statement* is a string on its own, as a docstring is."""
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


#: The statements whose body may or may not run.
_CONDITIONAL = (
    ast.If,
    ast.Try,
    ast.TryStar,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.With,
    ast.AsyncWith,
    ast.Match,
)


#: What defines code that runs later, if ever: a function or a lambda.
_DEFERRED = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def _unconditional_imports(node: ast.AST) -> Iterator[ast.Import | ast.ImportFrom]:
    """Every import inside *node* that runs whenever *node* does: none under an ``if``, a ``try``, a loop, a ``with`` or a ``match``.

    One in the body of the function *node* is, as the walk counts what it
    reaches as run, and so is one in a function *node* defines and then
    calls by name outside any condition (``return build()``). One in a
    function or a lambda *node* only defines (:data:`_DEFERRED`), a method
    included, is not, since nothing says it is ever called.
    """
    region = list(_runs_with(node))
    called = {
        part.func.id
        for part in region
        if isinstance(part, ast.Call) and isinstance(part.func, ast.Name)
    }
    for part in region:
        if isinstance(part, ast.Import | ast.ImportFrom):
            yield part
        elif (
            isinstance(part, ast.FunctionDef | ast.AsyncFunctionDef)
            and part is not node
            and part.name in called
        ):
            yield from _unconditional_imports(part)


def _runs_with(node: ast.AST, *, root: bool = True) -> Iterator[ast.AST]:
    """*node* and every node inside it that runs whenever it does.

    Nothing under an ``if``, a ``try``, a loop, a ``with`` or a ``match``
    (:data:`_CONDITIONAL`), and nothing in the body of a function or a
    lambda *node* defines (:data:`_DEFERRED`), though the definition
    itself is there.
    """
    yield node
    if isinstance(node, _CONDITIONAL) or (not root and isinstance(node, _DEFERRED)):
        return
    for child in ast.iter_child_nodes(node):
        yield from _runs_with(child, root=False)


def _with_packages(dotted: str) -> frozenset[str]:
    """*dotted* and every package above it: what importing it imports."""
    parts = dotted.split(".")
    return frozenset(".".join(parts[:cut]) for cut in range(1, len(parts) + 1))


def _does_nothing(statement: ast.stmt) -> bool:
    """Whether *statement* does nothing when it runs: ``pass``, or a constant on its own (``...``, a docstring)."""
    return isinstance(statement, ast.Pass) or (
        isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)
    )


def _at_run_time(statement: ast.stmt) -> ast.stmt | None:
    """*statement*, at the top of a module, without what only a type checker reads.

    An ``if TYPE_CHECKING:`` block goes, or keeps only its ``else``; any
    other statement is itself.
    """
    if not (isinstance(statement, ast.If) and _is_type_checking(statement.test)):
        return statement
    if not statement.orelse:
        return None
    kept = ast.If(test=statement.test, body=[ast.Pass()], orelse=statement.orelse)
    return ast.copy_location(kept, statement)


def _target_names(target: ast.expr) -> Iterator[str]:
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, ast.Tuple | ast.List):
        for element in target.elts:
            yield from _target_names(element)


class _RuntimeView(ast.NodeTransformer):
    """A tree with everything only a type checker reads taken out.

    Annotations are evaluated lazily or not at all, and no drawing code
    introspects them, so a parameter gaining ``: Axes`` cannot move a pixel.
    Leaving them in would break the fingerprint twice over: their expressions
    would enter the hash, and an unquoted annotation naming a package class
    would hand the dependency walk an edge no frame ever crosses. Both the
    walk and the hash therefore see this view, applied once at parse time.

    A bare declaration (``x: int`` with no value) binds nothing at run time
    and is dropped whole; an assigned one keeps its assignment and loses the
    annotation.
    """

    def visit_arg(self, node: ast.arg) -> ast.arg:
        node.annotation = None
        return node

    def _defun(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ast.FunctionDef | ast.AsyncFunctionDef:
        node.returns = None
        self.generic_visit(node)
        return node

    visit_FunctionDef = _defun
    visit_AsyncFunctionDef = _defun

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.stmt | None:
        if node.value is None:
            return None
        return ast.copy_location(
            ast.Assign(targets=[node.target], value=self.visit(node.value)), node
        )


class Sources:
    """Every module of the figures package, parsed once."""

    def __init__(self, root: pathlib.Path) -> None:
        self.root = root
        self.modules: dict[str, _Module] = {}
        self.packages: set[str] = set()
        self._engine_digest: str | None = None
        self._dumps: dict[Symbol, str] = {}
        self._statement_levels: dict[str, str] = {}
        self._hashed: dict[str, list[ast.stmt]] = {}
        self._reads_in: dict[int, tuple[frozenset[str], frozenset[str]]] = {}
        self._imported_by_reached: dict[frozenset[Symbol], frozenset[str]] = {}
        self._scopes: dict[str, _ScopeMap] = {}
        self._tops: dict[str, list[ast.stmt]] = {}
        self._runs: dict[str, set[str]] = {}
        self._starts: dict[Symbol, set[str]] = {}
        parsed: dict[str, ast.Module] = {}
        annotations: dict[str, frozenset[str]] = {}
        for where, prefix in _PACKAGES:
            package_root = root.joinpath(*where)
            if not package_root.is_dir():
                continue
            for path in sorted(package_root.rglob("*.py")):
                rel = path.relative_to(package_root).with_suffix("")
                parts = list(rel.parts[:-1] if rel.name == "__init__" else rel.parts)
                name = ".".join([*prefix, *parts])
                if path.name == "__init__.py":
                    self.packages.add(name)
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                annotations[name] = _annotation_names(tree)
                parsed[name] = ast.fix_missing_locations(_RuntimeView().visit(tree))
        # Every module name has to be known before the imports are resolved:
        # ``from . import media`` reads as a module reference or as a symbol
        # depending on whether ``figures.media`` exists.
        for name, tree in parsed.items():
            self.modules[name] = _Module(name, tree, self, annotations[name])
        #: every dotted name an import anywhere in the walk binds
        self.imported_anywhere = {
            target
            for module in self.modules.values()
            for node in ast.walk(module.tree)
            if isinstance(node, ast.Import | ast.ImportFrom)
            for _, target in _import_bindings(module, node)
        }

    def engine_digest(self) -> str:
        """:func:`engine_digest` of this tree, read once.

        :raises FileNotFoundError: when the tree has no ``engine-digests.json``.
        :raises ValueError: when its ``engine-digests.json`` does not hold the
            engines' digests.
        """
        if self._engine_digest is None:
            self._engine_digest = engine_digest(self.root)
        return self._engine_digest

    # -- name resolution ---------------------------------------------------

    def resolve(
        self, module: str, name: str, _seen: frozenset[Symbol] = frozenset()
    ) -> Symbol | None:
        """The ``(module, name)`` the walk reaches for *name* as seen from *module*.

        The module itself when its top binds the name by anything but one
        clean import (:meth:`_Scope.clean`): a ``def``, an assignment, a
        loop, or an import a guard decides or another binding rebinds. A
        clean import is followed to what it imports. None for a name the top
        does not bind, or one that leads out of the walk.
        """
        if module not in self.modules or (module, name) in _seen:
            return None
        top = self.scopes(module).top
        if not top.bindings.get(name):
            return None
        target = top.clean(name)
        if not target:
            return (module, name)
        return self.symbol_at(target, _seen | {(module, name)})

    def scopes(self, module: str) -> _ScopeMap:
        """Where each read of *module* reads from (:class:`_ScopeMap`), worked out once."""
        if module not in self._scopes:
            self._scopes[module] = _ScopeMap(self.modules[module])
        return self._scopes[module]

    def canonical_name(
        self, dotted: str, _seen: frozenset[Symbol] = frozenset()
    ) -> str:
        """*dotted*, a name of the walk read where it comes from, through re-exports.

        Where it is bound in the walk, or the dotted name outside the walk a
        re-export imports (``figures.theme._reexp`` reads ``json.dumps``
        when ``figures.theme`` imports ``dumps as _reexp`` from ``json``). A
        name outside the walk (``numpy.sqrt``), or one the walk cannot
        resolve, stays as it is.
        """
        parts = dotted.split(".")
        for cut in range(len(parts) - 1, 0, -1):
            module = ".".join(parts[:cut])
            if module in self.modules:
                found = self.origin(module, parts[cut], _seen)
                return ".".join([found, *parts[cut + 1 :]]) if found else dotted
        return dotted

    def origin(
        self, module: str, name: str, _seen: frozenset[Symbol] = frozenset()
    ) -> str:
        """The dotted name *name*, as seen from *module*, comes from; "" when the walk cannot tell.

        A name the top of *module* binds by anything but one clean import
        is read there, as ``module.name``: what binds it is hashed with that
        module, a guard or a rebinding included, and the walk reaches it
        (:meth:`resolve`). One clean import is followed, through the walk
        and out of it.
        """
        if module not in self.modules or (module, name) in _seen:
            return ""
        top = self.scopes(module).top
        if not top.bindings.get(name):
            return ""
        target = top.clean(name)
        if not target:
            return f"{module}.{name}"
        return self.canonical_name(target, _seen | {(module, name)})

    def canonical(self, module: str, node: ast.AST) -> ast.AST:
        """A copy of *node*, a part of *module*, with every imported name read as its dotted target.

        See :class:`_Canonical`.
        """
        scopes = self.scopes(module)
        copies: dict[int, Any] = {}
        tree = copy.deepcopy(node, copies)
        names, kept = {}, {}
        for original in ast.walk(node):
            twin = id(copies[id(original)])
            if id(original) in scopes.canonical:
                names[twin] = scopes.canonical[id(original)]
            elif id(original) in scopes.kept:
                kept[twin] = scopes.kept[id(original)]
        canonical: ast.AST = _Canonical(self, names, kept).visit(tree)
        return canonical

    def dump(self, symbol: Symbol) -> str:
        """The printed, canonical trees of every statement the walk reaches for *symbol* (:meth:`nodes`), taken once."""
        if symbol not in self._dumps:
            self._dumps[symbol] = "\x00".join(
                _dump(self.canonical(symbol[0], node)) for node in self.nodes(symbol)
            )
        return self._dumps[symbol]

    def top(self, module: str) -> list[ast.stmt]:
        """The statements at the top of *module* that run when it is imported, in their order.

        Without the module's docstring, and without what an ``if
        TYPE_CHECKING:`` block holds for a type checker: the block goes, or
        keeps only its ``else``.
        """
        if module not in self._tops:
            body = self.modules[module].tree.body
            if body and _is_docstring(body[0]):
                body = body[1:]
            self._tops[module] = [
                kept for kept in (_at_run_time(s) for s in body) if kept is not None
            ]
        return self._tops[module]

    def walked(self, module: str, statement: ast.stmt) -> bool:
        """Whether the walk reaches the top-level *statement* of *module* by name, rather than with the module.

        See :meth:`_walked_in`, for the top of the module.
        """
        return self._walked_in(module, self.scopes(module).top, statement)

    def _walked_in(self, module: str, scope: _Scope, statement: ast.stmt) -> bool:
        """Whether the walk reaches *statement*, one of the body of *scope* (the module or a class body), by name.

        Three forms are, and each binds exactly what the scopes say it binds
        (:attr:`_ScopeMap.binds`): a ``def`` or a ``class``, which a read of
        its name reaches with the other statements that bind the name (what
        it runs on import is hashed all the same, :meth:`_at_import`); an
        assignment to names, unpacked or not, that nothing else in the scope
        binds and whose value calls nothing but :data:`_PURE_CALLS`; and, at
        the top, an import of names nothing else there binds, which their
        uses stand for. Every other statement, whatever its kind, is hashed
        with its module (:meth:`hashed`). The assignment of a name the
        fingerprint leaves out on purpose (:data:`_IGNORED`, :data:`_TABLES`)
        stays with the walk whatever it calls.
        """
        if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            return True
        binds = self.scopes(module).binds.get(id(statement), set())
        if isinstance(statement, ast.Assign):
            if not all(_names_only(target) for target in statement.targets):
                return False
            left_out = {(module, name) for name in binds} & (_IGNORED | set(_TABLES))
            if not (left_out or self._pure(module, statement.value)):
                return False
        elif not (
            scope.kind == "module"
            and isinstance(statement, ast.Import | ast.ImportFrom)
        ):
            return False
        return all(len(scope.bindings[name]) == 1 for name in binds)

    def _pure(self, module: str, value: ast.expr) -> bool:
        """Whether every call *value*, an expression of *module*, makes when it is evaluated is one of :data:`_PURE_CALLS`.

        ``getattr`` only with an attribute name written as a string, whose
        attribute is then as plain to read as ``module.name``.
        """
        for call in _calls(value):
            callee = self._callee(module, call.func)
            if callee not in _PURE_CALLS:
                return False
            if callee == "getattr" and not (
                len(call.args) > 1
                and isinstance(call.args[1], ast.Constant)
                and isinstance(call.args[1].value, str)
            ):
                return False
        return True

    def _callee(self, module: str, func: ast.expr) -> str:
        """The dotted name *func*, what a call in *module* calls, reads; "" for one the module binds otherwise.

        A builtin is its own name (``frozenset``); an imported name or an
        attribute chain off one reads as its target (``numpy.array``,
        ``re.compile``); a name the module binds by anything but one clean
        import, or a call on anything but a name, is "".
        """
        attributes: list[str] = []
        value = func
        while isinstance(value, ast.Attribute):
            attributes.append(value.attr)
            value = value.value
        if not isinstance(value, ast.Name):
            return ""
        scopes = self.scopes(module)
        if id(value) in scopes.canonical:
            root = scopes.canonical[id(value)]
        elif id(value) in scopes.candidates:
            return ""
        else:
            root = value.id
        return self.canonical_name(".".join([root, *reversed(attributes)]))

    def _at_import(
        self, module: str, scope: _Scope, statement: ast.stmt
    ) -> ast.stmt | None:
        """What the ``def`` or ``class`` *statement*, in the body of *scope* in *module*, runs when it is defined, as a statement to hash; None for nothing.

        A ``def``'s decorators and the defaults that call something, without
        its parameters or its body; a ``class``'s decorators, bases and
        keywords (the metaclass among them), with the statements of its body
        the walk does not take by name and what each ``def`` and ``class``
        in it runs (:meth:`_class_body`), never a method's body. A default
        that calls nothing does nothing on import and is left out, and so is
        a decorator, a base or a keyword that runs nothing worth hashing
        (:meth:`_inert`): a ``class`` left with nothing adds nothing.
        """
        if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
            arguments = statement.args
            defaults = [
                default
                for default in [*arguments.defaults, *arguments.kw_defaults]
                if default is not None and any(_calls(default))
            ]
            decorators = self._live(module, scope, statement.decorator_list)
            if not (decorators or defaults):
                return None
            function = copy.copy(statement)
            function.args = ast.arguments(
                posonlyargs=[],
                args=[],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=defaults,
            )
            function.decorator_list, function.body = decorators, [ast.Pass()]
            function.returns, function.type_params = None, []
            return function
        if not isinstance(statement, ast.ClassDef):
            return None
        decorators = self._live(module, scope, statement.decorator_list)
        bases = self._live(module, scope, statement.bases)
        keywords = [
            keyword
            for keyword in statement.keywords
            if not self._inert(module, scope, keyword.value)
        ]
        body = self._class_body(module, statement)
        if not (decorators or bases or keywords or body):
            return None
        cls = copy.copy(statement)
        cls.decorator_list, cls.bases, cls.keywords = decorators, bases, keywords
        cls.body, cls.type_params = body or [ast.Pass()], []
        return cls

    def _live(
        self, module: str, scope: _Scope, parts: Iterable[ast.expr]
    ) -> list[ast.expr]:
        """The decorators or bases of *parts*, in the body of *scope* in *module*, that are not :meth:`_inert`."""
        return [part for part in parts if not self._inert(module, scope, part)]

    def _inert(self, module: str, scope: _Scope, part: ast.expr) -> bool:
        """Whether *part*, a decorator, a base or a class keyword in the body of *scope* in *module*, runs nothing worth hashing.

        A name of :data:`_INERT_DEFINITIONS`, called with arguments that call
        nothing impure (``lru_cache(maxsize=1)``, ``dataclass(frozen=True)``)
        or subscripted (``Mapping[str, R]``); or the ``setter``, ``getter``
        or ``deleter`` of a property the class body defines
        (:meth:`_properties`). A base defined in the walk is none of them,
        so the walk follows what the class reads.
        """
        if (
            scope.kind == "class"
            and isinstance(part, ast.Attribute)
            and part.attr in {"setter", "getter", "deleter"}
            and isinstance(part.value, ast.Name)
            and part.value.id in self._properties(module, scope)
        ):
            return True
        head, rest = part, []
        if isinstance(part, ast.Call):
            head, rest = part.func, [*part.args, *(k.value for k in part.keywords)]
        elif isinstance(part, ast.Subscript):
            head, rest = part.value, [part.slice]
        if self._callee(module, head) not in _INERT_DEFINITIONS:
            return False
        return all(self._pure(module, argument) for argument in rest)

    def _properties(self, module: str, scope: _Scope) -> set[str]:
        """The names the class body *scope* of *module* binds by a ``def`` that ``property`` decorates.

        Read as :meth:`_callee` reads a call, so a module that rebinds the
        name ``property`` defines no property with it.
        """
        node = self.scopes(module).class_nodes[id(scope)]
        return {
            statement.name
            for statement in node.body
            if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef)
            and any(
                self._callee(module, decorator) == "property"
                for decorator in statement.decorator_list
            )
        }

    def _class_body(self, module: str, node: ast.ClassDef) -> list[ast.stmt]:
        """What the body of the class *node* runs when the class is defined: as :meth:`hashed` reads the top of a module."""
        scope = self.scopes(module).class_scopes[id(node)]
        body = node.body[1:] if node.body and _is_docstring(node.body[0]) else node.body
        statements = [s for s in (_at_run_time(s) for s in body) if s is not None]
        return self._run_on_import(module, scope, statements)

    def _run_on_import(
        self, module: str, scope: _Scope, statements: Iterable[ast.stmt]
    ) -> list[ast.stmt]:
        """What *statements*, the body of *scope* in *module*, run when it runs, beyond what the walk takes by name.

        Each statement the walk does not take by name (:meth:`_walked_in`)
        whole, and what each ``def`` and ``class`` it does take runs when
        it is defined (:meth:`_at_import`), in their order. A statement that
        does nothing (``pass``, a string on its own as an attribute's
        docstring) is left out.
        """
        found: list[ast.stmt] = []
        for statement in statements:
            if _does_nothing(statement):
                continue
            if not self._walked_in(module, scope, statement):
                found.append(statement)
            elif (part := self._at_import(module, scope, statement)) is not None:
                found.append(part)
        return found

    def nodes(self, symbol: Symbol) -> list[ast.stmt]:
        """Every statement the walk reaches for *symbol*, in order: each ``def``, ``class`` or assignment the walk takes by name (:meth:`walked`) that binds it."""
        module, name = symbol
        if module not in self.modules:
            return []
        binds = self.scopes(module).binds
        return [
            statement
            for statement in self.top(module)
            if name in binds.get(id(statement), ())
            and not isinstance(statement, ast.Import | ast.ImportFrom)
            and self.walked(module, statement)
        ]

    def hashed(self, module: str) -> list[ast.stmt]:
        """The statements at the top of *module* hashed with it, in their order.

        Every one the walk does not take by name (:meth:`walked`), and what
        each ``def`` and ``class`` it does take runs when it is defined
        (:meth:`_at_import`): a decorator, a default that calls something, a
        base, or a statement of a class body runs on import whether or not
        the walk reaches the name.
        """
        if module not in self._hashed:
            top = self.scopes(module).top
            self._hashed[module] = self._run_on_import(module, top, self.top(module))
        return self._hashed[module]

    def module_level(self, module: str, symbols: Iterable[Symbol]) -> str:
        """What *module* does when it is imported, for a clip that reaches *symbols*, beyond what the walk reaches by name; "" for nothing.

        Two parts, joined. What the imports the walk takes by name keep
        (:meth:`effects`), a sorted set. Then every other statement at the
        top (:meth:`hashed`), canonical as a symbol is and in the order they
        stand: a bare call (``figures.theme``'s ``plt.rcParams.update({...})``),
        an ``if``, a ``try``, a loop or a ``with`` with all their branches,
        an assignment to a subscript, an attribute or a name bound more than
        once, an augmented assignment, an assignment that calls something
        impure, a type alias, what a ``def`` or ``class`` runs when it is
        defined, and any kind of statement besides; an import among them
        keeps what it says. An ``if TYPE_CHECKING:`` block is left out
        (:meth:`top`).
        """
        effects = self.effects(module, symbols)
        if module not in self._statement_levels:
            hashed = self.hashed(module)
            body = self.canonical(module, ast.Module(body=hashed, type_ignores=[]))
            self._statement_levels[module] = _dump(body) if hashed else ""
        statements = self._statement_levels[module]
        return "\x00".join([*effects, statements] if statements else effects)

    def effects(self, module: str, symbols: Iterable[Symbol]) -> list[str]:
        """What the imports at the top of *module* that the walk takes by name keep, for a clip that reaches *symbols*.

        An import runs on import whether or not its name is read, so each
        name one binds keeps what the statement imports (``import
        mpl_toolkits.mplot3d``), without the name it is bound to, unless
        something stands for it: a statement the clip reaches reads the
        name, so its uses read as the target; or a use reads the target
        under another name; or it is there for a type checker or for other
        modules (:meth:`for_types_or_others`); or what it imports is no
        third-party module (:meth:`_unread`); or the code the clip reaches
        imports every module it does already (:meth:`_reached_imports`), so
        it runs nothing more. A re-export keeps where its name comes from.
        """
        mod = self.modules[module]
        names, targets = self._read_at_top(module, symbols)
        imported = self._reached_imports(symbols)
        found: set[str] = set()
        for statement in self.scopes(module).unguarded:
            if not self.walked(module, statement):
                continue
            bound = zip(
                _import_effects(mod, statement),
                self._modules_imported(mod, statement),
                strict=True,
            )
            for (name, target, effect), modules in bound:
                if not target:
                    found.add(effect)
                elif not (
                    name in names
                    or target in targets
                    or self.for_types_or_others(mod, name, target)
                    or modules <= imported
                ):
                    found.add(self._unread(effect, target))
        found.discard("")
        return sorted(found)

    def _modules_imported(
        self, module: _Module, node: ast.Import | ast.ImportFrom
    ) -> Iterator[frozenset[str]]:
        """The modules each name *node*, an import in *module*, binds makes Python import, the packages above them included.

        ``import a.b`` imports ``a`` and ``a.b``; ``from m import n`` imports
        ``m`` and the packages above it, and ``m.n`` when that is a module,
        read where a re-export of the walk takes it (:meth:`canonical_name`).
        One name each, in the order the statement binds them.
        """
        if isinstance(node, ast.Import):
            yield from (_with_packages(alias.name) for alias in node.names)
            return
        base = module._resolve_import(node)
        for alias in node.names:
            dotted = self.canonical_name(f"{base}.{alias.name}") if base else ""
            yield _with_packages(dotted) if dotted else frozenset()

    def _reached_imports(self, symbols: Iterable[Symbol]) -> frozenset[str]:
        """Every module the code a clip that reaches *symbols* reaches imports, the packages above each included.

        An import that runs whenever a statement the walk reaches or hashes
        does (:func:`_reached_statements`, :func:`_unconditional_imports`),
        and an import at the top of a module whose top runs that such a
        statement reads, by its name or by its target. An import under an
        ``if``, a ``try``, a loop, a ``with`` or a ``match`` may never run,
        so it is no reason to leave another one out.
        """
        chosen = frozenset(symbols)
        if chosen not in self._imported_by_reached:
            found: set[str] = set()
            for module, statement in _reached_statements(self, chosen):
                mod = self.modules[module]
                for node in _unconditional_imports(statement):
                    found.update(*self._modules_imported(mod, node))
            for module in self.entered(chosen):
                found |= self._read_imports(module, chosen)
            self._imported_by_reached[chosen] = frozenset(found)
        return self._imported_by_reached[chosen]

    def _read_imports(self, module: str, symbols: frozenset[Symbol]) -> set[str]:
        """The modules the imports at the top of *module* whose name or target a statement reached for *symbols* reads make Python import."""
        mod = self.modules[module]
        names, targets = self._read_at_top(module, symbols)
        found: set[str] = set()
        for statement in self.scopes(module).unguarded:
            bound = zip(
                _import_effects(mod, statement),
                self._modules_imported(mod, statement),
                strict=True,
            )
            for (name, target, _), modules in bound:
                if name in names or target in targets:
                    found |= modules
        return found

    def _unread(self, effect: str, target: str) -> str:
        """What an import of *target* that no reached statement reads keeps: what it says, without the name it binds; "" for no third-party module.

        A module of the walk is entered anyway (:meth:`runs`); a module of
        the standard library changes nothing a frame is drawn with; and a
        module of the library outside the walk is its physics, which the
        walk does not follow (see "Known gaps").
        """
        origin = self.canonical_name(target)
        parts = origin.split(".")
        if parts[0] in _STANDARD_LIBRARY or parts[0] == _LIBRARY:
            return ""
        if any(
            ".".join(parts[:cut]) in self.modules for cut in range(1, len(parts) + 1)
        ):
            return ""
        said = effect.split(" as ")[0]
        return said if origin == target else f"{said} ({origin})"

    def _read_at_top(
        self, module: str, symbols: Iterable[Symbol]
    ) -> tuple[set[str], set[str]]:
        """What the statements of *module* a clip that reaches *symbols* reaches read: the names of its top, and the targets of clean imports.

        The statements the walk takes for a symbol of *symbols*, and the ones
        hashed with the module.
        """
        statements = [
            node
            for symbol in symbols
            if symbol[0] == module
            for node in self.nodes(symbol)
        ]
        names: set[str] = set()
        targets: set[str] = set()
        for statement in [*statements, *self.hashed(module)]:
            if id(statement) not in self._reads_in:
                scopes = self.scopes(module)
                read = [n for n in ast.walk(statement) if isinstance(n, ast.Name)]
                self._reads_in[id(statement)] = (
                    frozenset(n.id for n in read if id(n) in scopes.top_reads),
                    frozenset(
                        scopes.canonical[id(n)]
                        for n in read
                        if id(n) in scopes.canonical
                    ),
                )
            statement_names, statement_targets = self._reads_in[id(statement)]
            names |= statement_names
            targets |= statement_targets
        return names, targets

    def for_types_or_others(self, module: _Module, name: str, target: str) -> bool:
        """Whether the top-level import of *name*, bound to *target*, is there for a type checker or for other modules.

        For a type checker when an annotation reads the name (and nothing at
        run time does), or when it comes from ``typing``,
        ``typing_extensions`` or ``__future__``, which import nothing a frame
        could show: such
        an import is left out as one under ``if TYPE_CHECKING:`` is. For
        other modules when ``__all__`` lists it or another module of the
        walk imports it from this one: a re-export is reached through the
        modules that use it.
        """
        return (
            name in module.annotation_names
            or target.split(".")[0] in _TYPING_MODULES
            or name in _exported(module.tree)
            or f"{module.name}.{name}" in self.imported_anywhere
        )

    def symbol_at(
        self, dotted: str, _seen: frozenset[Symbol] = frozenset()
    ) -> Symbol | None:
        """The package symbol the dotted name *dotted* reaches, through re-exports.

        The longest leading part that is a module of the walk, and the name
        after it; None for a name outside the walk or a module itself.
        """
        parts = dotted.split(".")
        for cut in range(len(parts) - 1, 0, -1):
            module = ".".join(parts[:cut])
            if module in self.modules:
                return self.resolve(module, parts[cut], _seen)
        return None

    # -- the walk ----------------------------------------------------------

    def closure(self, roots: Iterable[Symbol]) -> set[Symbol]:
        """Every package symbol reachable from *roots*, roots included.

        Reaching a name reaches every statement the walk takes by name that
        binds it (:meth:`nodes`), and enters every module whose top that
        runs (:meth:`entered`): the rest of the top of each one
        (:meth:`hashed`) runs when it is imported, and ``figures.theme``
        registers the dark field map in a bare call, so what such a
        statement names is followed like what a function names.
        """
        seen: set[Symbol] = set()
        modules: set[str] = set()
        stack = list(roots)
        while stack:
            symbol = stack.pop()
            if symbol in seen or symbol in _IGNORED or symbol in _TABLES:
                continue
            module, name = symbol
            if module not in self.modules:
                continue
            if not self.scopes(module).top.bindings.get(name):
                continue
            seen.add(symbol)
            for node in self.nodes(symbol):
                stack.extend(self.referenced(module, node))
            for entered in self._enter(self.starts(symbol), modules):
                for statement in self.hashed(entered):
                    stack.extend(self.referenced(entered, statement))
        return seen

    def entered(self, symbols: Iterable[Symbol]) -> set[str]:
        """Every module whose top runs for a clip that reaches *symbols*.

        The module of each symbol and every module an import the walk
        reaches for it names (:meth:`starts`), and what running each of them
        runs in turn (:meth:`runs`): Python runs a module's top the first
        time anything imports it, whether or not the walk reads a name of
        it. These are the modules :meth:`closure` enters.
        """
        modules: set[str] = set()
        for symbol in symbols:
            self._enter(self.starts(symbol), modules)
        return modules

    def starts(self, symbol: Symbol) -> set[str]:
        """The modules reaching *symbol* runs: its own, and each module of the walk an import in a statement the walk takes for it names.

        An import inside a function the walk reaches runs when the function
        does.
        """
        if symbol not in self._starts:
            module = symbol[0]
            found = {module}
            for node in self.nodes(symbol):
                found |= self._imported(module, node)
            self._starts[symbol] = found
        return self._starts[symbol]

    def runs(self, module: str) -> set[str]:
        """The modules of the walk whose top runs when the top of *module* does.

        Every package above it (``figures.fields`` for
        ``figures.fields.elastic``), which Python runs first, and every
        module an import at its top names, guarded or not: the one a clean
        re-export passes a name through included, and the package a
        ``from . import x`` reads ``x`` from.
        """
        if module not in self._runs:
            parts = module.split(".")
            found = {".".join(parts[:cut]) for cut in range(1, len(parts))}
            for statement in self.top(module):
                taken = self.walked(module, statement)
                if not taken or isinstance(statement, ast.Import | ast.ImportFrom):
                    found |= self._imported(module, statement)
            self._runs[module] = found & self.modules.keys()
        return self._runs[module]

    def _enter(self, starts: Iterable[str], modules: set[str]) -> list[str]:
        """Add to *modules* each of *starts* and what running it runs (:meth:`runs`); the ones it did not hold yet."""
        pending, entered = list(starts), []
        while pending:
            module = pending.pop()
            if module not in modules:
                modules.add(module)
                entered.append(module)
                pending.extend(self.runs(module))
        return entered

    def _imported(self, module: str, node: ast.AST) -> set[str]:
        """Every module of the walk an import inside *node*, a part of *module*, names."""
        mod = self.modules[module]
        return {
            name
            for child in ast.walk(node)
            if isinstance(child, ast.Import | ast.ImportFrom)
            for name in _imported_modules(mod, child)
            if name in self.modules
        }

    def node(self, symbol: Symbol) -> ast.stmt | None:
        """The last statement the walk reaches for *symbol* (:meth:`nodes`); None for none."""
        found = self.nodes(symbol)
        return found[-1] if found else None

    def referenced(self, module: str, node: ast.AST) -> Iterator[Symbol]:
        """The package symbols *node* names, from inside *module*.

        A name, or an attribute chain off one, read from the scope that
        binds it (:meth:`_ScopeMap.read_from`): an import inside a function
        counts there as the module's do everywhere else; a name an import
        binds under a condition may be either target.
        """
        scopes = self.scopes(module)
        for child in ast.walk(node):
            for dotted in scopes.read_from(child):
                found = self.symbol_at(dotted)
                if found is not None:
                    yield found

    # -- the clips ---------------------------------------------------------

    def clips(self) -> dict[str, Symbol]:
        """``clip stem -> defining (module, function)`` from the registry."""
        registry = self.modules[_REGISTRY]
        mapping: dict[str, Symbol] = {}
        for node in ast.walk(registry.tree):
            if not isinstance(node, ast.AnnAssign | ast.Assign):
                continue
            targets = (
                list(_target_names(node.target))
                if isinstance(node, ast.AnnAssign)
                else [n for t in node.targets for n in _target_names(t)]
            )
            if "_ANIMATIONS" not in targets or not isinstance(node.value, ast.Dict):
                continue
            for key, value in zip(node.value.keys, node.value.values, strict=True):
                if (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and isinstance(value, ast.Name)
                ):
                    found = self.resolve(_REGISTRY, value.id)
                    if found is not None:
                        mapping[key.value] = found
        return mapping


# -- hashing ----------------------------------------------------------------


#: Stands in for "this parameter has no default" in the canonical argument
#: list of :func:`_flatten_parameters`. It is only ever dumped, never compiled,
#: so any node that cannot be confused with a real default will do; a bare name
#: no source can spell is the least confusable one.
_NO_DEFAULT = ast.Name(id="<no default>", ctx=ast.Load())


def _flatten_parameters(args: ast.arguments) -> None:
    """Rewrite *args* so that where the bare ``*`` sits stops mattering.

    Making a parameter keyword-only decides how a caller may write the call.
    It cannot change what the function computes, and therefore cannot change a
    frame, so it belongs with the docstrings and the import order rather than
    with the things this fingerprint watches. Without this, moving one star in
    one shared helper marks every clip that reaches it stale, and the
    re-render proves the frames identical.

    The parameters are laid out in source order with their defaults beside
    them, one slot each, so a parameter that gains or loses a default still
    moves the hash. The result is not a legal signature -- ``defaults`` is no
    longer a suffix -- but it is never compiled, only dumped.
    """
    ordered = [*args.posonlyargs, *args.args, *args.kwonlyargs]
    positional = len(args.posonlyargs) + len(args.args)
    padding = [_NO_DEFAULT] * (positional - len(args.defaults))
    defaults = [
        *padding,
        *args.defaults,
        *(d if d is not None else _NO_DEFAULT for d in args.kw_defaults),
    ]
    args.posonlyargs = []
    args.args = ordered
    args.kwonlyargs = []
    args.defaults = defaults
    args.kw_defaults = []


def _strip_docstrings(node: ast.AST) -> ast.AST:
    """A copy of *node* with every docstring removed and its stars flattened.

    Rewriting a docstring cannot change a frame, and a fingerprint that moves
    when the prose does would be ignored within a week. The same goes for
    where the keyword-only star sits; see :func:`_flatten_parameters`.
    """
    import copy

    clone = copy.deepcopy(node)
    for child in ast.walk(clone):
        if isinstance(
            child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Module
        ):
            body = child.body
            if body and _is_docstring(body[0]):
                child.body = body[1:] or [ast.Pass()]
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            _flatten_parameters(child.args)
    return clone


def _drop_empty_lists(tree: ast.AST) -> ast.AST:
    """*tree* without its empty lists, so every interpreter prints it alike.

    ``ast.dump`` does not print one tree the same way on every Python. 3.11
    and 3.12 print every empty list a node carries (``decorator_list=[]``,
    ``bases=[]``, ``posonlyargs=[]``, ``kw_defaults=[]``, ``type_ignores=[]``
    and the like, and on 3.12 the ``type_params=[]`` it gave each function
    and class), and 3.13 stopped printing them. Hashed as printed, the same
    sources fingerprinted one way on 3.11 and 3.12 and another on 3.13 and
    3.14, and the freshness check called every clip stale wherever it ran on
    the older two. With the empty lists removed each of them prints what 3.13
    prints by default, so the stamps already committed hold on all four. An
    optional field holding ``None`` needs nothing: every one of these versions
    leaves it out of the print already, and a ``None`` that is a literal in
    the source (``Constant``, ``MatchSingleton``) is printed by all of them.

    Mutates *tree*, which :func:`_strip_docstrings` has already copied.
    """
    for node in ast.walk(tree):
        for name in node._fields:
            value = getattr(node, name, None)
            if isinstance(value, list) and not value:
                with contextlib.suppress(AttributeError):
                    delattr(node, name)
    return tree


#: Printed the way 3.11 and 3.12 print, empty lists and all, where the
#: interpreter can choose. Once :func:`_drop_empty_lists` has run there is
#: no empty list left, so the print is what 3.13 gives by default; asking for
#: the older behaviour only means that without the drop the print would
#: change on every interpreter, not just the older ones, and a test run on
#: any of them would say so.
_SHOW_EMPTY: dict[str, bool] = (
    {"show_empty": True} if sys.version_info >= (3, 13) else {}
)


def _dump(node: ast.AST) -> str:
    return ast.dump(
        _drop_empty_lists(_strip_docstrings(node)),
        annotate_fields=True,
        include_attributes=False,
        **_SHOW_EMPTY,
    )


def _is_type_checking(test: ast.expr) -> bool:
    """Is *test* the ``TYPE_CHECKING`` guard, however it was imported?"""
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"


def _literals(sources: Sources, symbols: Iterable[Symbol]) -> set[str]:
    """Every string literal in what the walk reaches for *symbols*, f-string fragments included.

    Each statement it reaches by name (:meth:`Sources.nodes`) and the rest of
    the top of each module (:meth:`Sources.hashed`).
    """
    out: set[str] = set()
    for _, node in _reached_statements(sources, symbols):
        for child in ast.walk(_strip_docstrings(node)):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                out.add(child.value)
    return out


def _reached_statements(
    sources: Sources, symbols: Iterable[Symbol]
) -> Iterator[tuple[str, ast.stmt]]:
    """``(module, statement)`` for every statement a clip that reaches *symbols* reaches.

    Each one the walk takes by name for a symbol (:meth:`Sources.nodes`),
    and the rest of the top of each module whose top runs
    (:meth:`Sources.entered`, :meth:`Sources.hashed`).
    """
    chosen = list(symbols)
    for symbol in chosen:
        yield from ((symbol[0], node) for node in sources.nodes(symbol))
    for module in sorted(sources.entered(chosen)):
        yield from ((module, statement) for statement in sources.hashed(module))


_META = set(r"[](){}|?*+.^$")


#: Escapes that stand for a character class or a position rather than for a
#: character (``\d``, ``\b``, a backreference), so a run ends at them. Every
#: other escape (``\$``, ``\(``, ``\\``) is the character itself.
_CLASS_ESCAPES = set("0123456789AbBdDsSwWZzGN")


def _pattern_runs(pattern: str) -> list[str]:
    """The plain-text runs of a regex, i.e. what it prints verbatim.

    A string a pattern translates necessarily contains all of these, which
    is what lets a clip's own text say which patterns belong to it.
    """
    runs: list[str] = []
    current: list[str] = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "\\" and index + 1 < len(pattern):
            escaped = pattern[index + 1]
            if escaped in _CLASS_ESCAPES:
                runs.append("".join(current))
                current = []
            elif escaped in "nrt":
                current.append({"n": "\n", "r": "\r", "t": "\t"}[escaped])
            else:
                current.append(escaped)
            index += 2
            continue
        if char in _META:
            runs.append("".join(current))
            current = []
        else:
            current.append(char)
        index += 1
    runs.append("".join(current))
    return [run for run in runs if len(run) >= _MIN_PATTERN_RUN]


def _table_entries(
    sources: Sources,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """``(_ES_EXACT items, _ES_PATTERNS items)`` read straight from the AST."""
    exact, patterns = (sources.node(table) for table in _TABLES)
    return _exact_entries(exact), _pattern_entries(patterns)


def _exact_entries(node: ast.stmt | None) -> list[tuple[str, str]]:
    """The literal ``(English, Spanish)`` items of *node*, the ``_ES_EXACT`` dict."""
    if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)):
        return []
    pairs = (
        _literal_pair(key, value)
        for key, value in zip(node.value.keys, node.value.values, strict=True)
    )
    return [pair for pair in pairs if pair is not None]


def _pattern_entries(node: ast.stmt | None) -> list[tuple[str, str]]:
    """The literal ``(pattern, replacement)`` items of *node*, the ``_ES_PATTERNS`` list."""
    if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.List)):
        return []
    pairs = (
        _literal_pair(element.elts[0], element.elts[1])
        for element in node.value.elts
        if isinstance(element, ast.Tuple) and len(element.elts) == 2
    )
    return [pair for pair in pairs if pair is not None]


def _literal_pair(key: ast.expr | None, value: ast.expr) -> tuple[str, str] | None:
    if key is None:  # ``{**other}`` inside the table literal
        return None
    try:
        left = ast.literal_eval(key)
        right = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return None
    if isinstance(left, str) and isinstance(right, str):
        return (left, right)
    return None


def _selected_translations(
    literals: set[str], exact: list[tuple[str, str]], patterns: list[tuple[str, str]]
) -> list[str]:
    """The table entries the clip's own strings reach.

    An exact entry is selected when the clip writes its key verbatim. A
    pattern is selected when *every* run of plain text it prints is written
    somewhere in the clip, which is how the labels assembled with an
    f-string are recognised: the pattern's fixed text is, necessarily, the
    fixed text of the f-string, split at the interpolations. Requiring all
    the runs rather than any one of them is what keeps a pattern of some
    other figure from attaching itself to a clip through a run as common as
    ``" to "``.
    """
    chosen: list[str] = []
    for key, value in exact:
        if key in literals or _key_is_written(key, literals):
            chosen.append(f"exact\x00{key}\x00{value}")
    for pattern, repl in patterns:
        runs = _pattern_runs(pattern)
        if runs and all(_run_is_written(run, literals) for run in runs):
            chosen.append(f"pattern\x00{pattern}\x00{repl}")
    return sorted(chosen)


def _key_is_written(key: str, literals: set[str]) -> bool:
    """Whether the clip writes an exact-table key it assembles with numbers.

    ``"$L$ = 0.30 m · $m$ = 4"`` is an entry of the exact table -- a label
    with no words for the pattern list to key on -- and the clip builds it as
    ``f"$L$ = {length:.2f} m · $m$ = {ratio:.0f}"``. Taking the numbers out
    leaves exactly the fragments the source writes, so a key whose every
    non-numeric piece is written counts as this clip's.
    """
    import re as _re

    pieces = [
        piece for piece in _re.split(r"[\d]+", key) if len(piece.strip()) >= _MIN_SPLIT
    ]
    return bool(pieces) and all(
        any(piece in literal for literal in literals) for piece in pieces
    )


def _run_is_written(run: str, literals: set[str]) -> bool:
    """Whether the clip writes *run*, whole or split across an interpolation.

    ``"Sabine, $T$ = 300 ms"`` is built as ``f"{name}, $T$ = {ms} ms"``, so
    the pattern's run ``"Sabine, $T$ = "`` sits in no single fragment: the
    name comes from a variable and only ``", $T$ = "`` is written literally.
    A run therefore also counts when it splits in two and both halves are
    written -- one split, both halves at least three characters, so the rule
    cannot degenerate into "every run is written character by character".
    """
    if any(run in literal for literal in literals):
        return True
    for cut in range(_MIN_SPLIT, len(run) - _MIN_SPLIT + 1):
        head, tail = run[:cut], run[cut:]
        if any(head in literal for literal in literals) and any(
            tail in literal for literal in literals
        ):
            return True
    return False


def engine_digest(root: pathlib.Path) -> str:
    """One hash of what the engines compute, from ``engine-digests.json``.

    Only the digests and the fluid-energy record count: where they were
    measured (the ``environment`` and ``measured_on`` blocks) is not what the
    engines compute.

    :raises FileNotFoundError: when *root* has no ``engine-digests.json``.
    :raises ValueError: when the file does not hold the engines' digests (it
        is not JSON, not an object, or lacks one of the two records), naming
        the file and ``make engine-digests``, which writes it again.
    """
    path = root / ENGINE_DIGESTS
    if not path.exists():
        msg = (
            f"{path} is missing; record the engines' digests with `make engine-digests`"
        )
        raise FileNotFoundError(msg)
    numbers = _engine_records(path)
    return hashlib.sha256(json.dumps(numbers, sort_keys=True).encode()).hexdigest()


#: The records of ``engine-digests.json`` that say what the engines compute.
_ENGINE_RECORDS = ("scenarios", "fluid_energy")


def _json_kind(value: object) -> str:
    """What JSON calls *value*, which is no object: an array, a string, a number, true or false, null."""
    if isinstance(value, list):
        return "an array"
    if isinstance(value, str):
        return "a string"
    if isinstance(value, bool):
        return "true or false"
    if isinstance(value, int | float):
        return "a number"
    return "null"


def _engine_records(path: pathlib.Path) -> dict[str, object]:
    """The records of the digest file *path* that :func:`engine_digest` hashes.

    :raises ValueError: when *path* is not JSON, not an object, or lacks one
        of :data:`_ENGINE_RECORDS`, naming *path* and its remedy.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:  # not UTF-8, or not JSON
        reason = f"not JSON: {exc}"
    else:
        if not isinstance(data, dict):
            reason = f"{_json_kind(data)} where an object belongs"
        elif missing := [key for key in _ENGINE_RECORDS if key not in data]:
            reason = f"no {' and no '.join(missing)} record"
        else:
            return {key: data[key] for key in _ENGINE_RECORDS}
    msg = (
        f"{path} does not hold the engines' digests ({reason}); "
        "record them again with `make engine-digests`"
    )
    raise ValueError(msg)


def _is_engine(dotted: str) -> bool:
    """Whether the dotted name *dotted* is the simulation package or inside it."""
    return dotted == "phonometry.simulation" or dotted.startswith(
        "phonometry.simulation."
    )


def _names_engine(module: str, attr: str) -> bool:
    """Whether ``from <module> import <attr>`` reaches the simulation package."""
    return _is_engine(f"{module}.{attr}" if attr else module)


def _imports_engine(module: _Module, node: ast.Import | ast.ImportFrom) -> bool:
    """Whether *node*, an import inside *module*, reaches the simulation package.

    A relative import is read the way the module's own imports are
    (:meth:`_Module._resolve_import`), so ``from ..simulation import FDTD2D``
    inside a function of ``phonometry._plot`` counts.
    """
    if isinstance(node, ast.Import):
        return any(_is_engine(alias.name) for alias in node.names)
    target = module._resolve_import(node)
    return bool(target) and any(
        _names_engine(target, alias.name) for alias in node.names
    )


def _reaches_engine(module: _Module, node: ast.AST) -> bool:
    """Whether *node*, one node of a tree inside *module*, reaches the simulation package."""
    if isinstance(node, ast.Import | ast.ImportFrom):
        return _imports_engine(module, node)
    scopes = module.owner.scopes(module.name)
    return any(_is_engine(dotted) for dotted in scopes.read_from(node))


def _uses_engine(module: _Module, node: ast.AST) -> bool:
    """Whether *node* reaches the simulation package, by an import or by a name.

    An import, relative ones included; a name the module or *node* imported
    from it; or an attribute chain off a name bound to a package above it
    (``phonometry.simulation.FDTD2D`` after ``import phonometry``). Each
    name is read from the scope that binds it (:meth:`_ScopeMap.read_from`);
    a name an import binds under a condition counts by either target.
    """
    return any(_reaches_engine(module, child) for child in ast.walk(node))


def steps_an_engine(sources: Sources, symbols: Iterable[Symbol]) -> bool:
    """Whether a clip that reaches *symbols* uses the simulation package.

    Either something it reaches imports the package where it uses it (the
    field builders do, inside the function; a library helper may do it with
    a relative import), or it names what a module it reaches imported from
    the package at the top (a material such as ``ALUMINUM``), or it reaches
    the package through the attributes of one above it
    (``phonometry.simulation.FDTD2D`` after ``import phonometry``).
    """
    return any(
        _uses_engine(sources.modules[module], node)
        for module, node in _reached_statements(sources, symbols)
    )


def engine_clips(root: pathlib.Path) -> set[str]:
    """The registered clips that step an FDTD engine."""
    sources = Sources(root)
    return {
        clip
        for clip, entry in sources.clips().items()
        if steps_an_engine(sources, sources.closure([entry, *_EXTRA_ROOTS]))
    }


def fingerprint_parts(
    sources: Sources, clip: str, entry: Symbol
) -> tuple[list[str], list[str]]:
    """``(code lines, translation lines)`` a clip's fingerprint is taken over.

    :raises FileNotFoundError: when the clip steps an FDTD engine and the tree
        has no ``engine-digests.json``.
    :raises ValueError: when the clip steps an FDTD engine and the tree's
        ``engine-digests.json`` does not hold the engines' digests.
    """
    roots = [entry, *_EXTRA_ROOTS]
    symbols = sources.closure(roots)
    code = sorted(
        f"{module}.{name}\x00{sources.dump((module, name))}" for module, name in symbols
    )
    # Plus what every module whose top runs for the clip does when it is
    # imported, beyond the statements the walk takes by name
    # (``Sources.entered``, ``Sources.module_level``). One such statement is
    # ``figures.theme``'s ``plt.rcParams.update({...})``: the base font size,
    # the grid and its alpha, i.e. how every frame looks.
    for module in sorted(sources.entered(symbols)):
        level = sources.module_level(module, symbols)
        if level:
            code.append(f"{module}.<module>\x00{level}")
    # A clip that steps an engine shows the engine's numbers, so it is tied to
    # the engine's golden digests, which move only when those numbers do.
    if steps_an_engine(sources, symbols):
        code.append(f"<engine>\x00{sources.engine_digest()}")
    code.sort()
    exact, patterns = _table_entries(sources)
    text = _selected_translations(_literals(sources, symbols), exact, patterns)
    return code, text


def fingerprints(root: pathlib.Path) -> dict[str, str]:
    """The fingerprint of every registered clip, computed from *root*'s sources.

    :raises FileNotFoundError: when a clip steps an FDTD engine and *root* has
        no ``engine-digests.json``.
    :raises ValueError: when a clip steps an FDTD engine and *root*'s
        ``engine-digests.json`` does not hold the engines' digests.
    """
    sources = Sources(root)
    out: dict[str, str] = {}
    for clip, entry in sorted(sources.clips().items()):
        code, text = fingerprint_parts(sources, clip, entry)
        digest = hashlib.sha256()
        for line in code:
            digest.update(line.encode("utf-8"))
            digest.update(b"\n")
        digest.update(b"--translations--\n")
        for line in text:
            digest.update(line.encode("utf-8"))
            digest.update(b"\n")
        out[clip] = digest.hexdigest()[:16]
    return out


# -- the manifest -----------------------------------------------------------

_HEADER = """\
# What each committed clip was drawn by, one line per clip.
#
# The clips are not regenerated in CI (an FDTD run plus four video encodes
# each), so nothing else can tell that the code drawing a clip has moved since
# the clip was written. Each hash covers the clip's builder, everything it
# reaches inside scripts/figures (the shared clip tail, the theme, the
# translation machinery), inside phonometry._plot (the drawing helpers it
# calls) and inside phonometry.io (the encode path), the translation-table
# entries its own strings select and, for a clip that steps an FDTD engine,
# the engines' golden digests (engine-digests.json); it is taken over the
# syntax tree, so comments and docstrings do not move it. See
# scripts/animation_fingerprint.py.
#
# Each line: the clip, the fingerprint of the code that drew it, and the
# ffmpeg encoder that wrote its WebM (av1_nvenc or libsvtav1).
#
# Written by the renderer. To refresh one clip, re-render it:
#     make animations ANIM=<clip>
# (CONTRIBUTING.md, Clips: the ffmpeg it needs, or a GPU node).
"""


def _manifest_lines() -> list[list[str]]:
    if not MANIFEST.exists():
        return []
    rows: list[list[str]] = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if text and not text.startswith("#"):
            rows.append(text.split())
    return rows


def read_manifest() -> dict[str, str]:
    """The stamped fingerprints, ``clip -> hash``."""
    return {row[0]: row[1] for row in _manifest_lines() if len(row) >= 2}


def read_encoders() -> dict[str, str]:
    """The encoder each clip's WebM was written by; a clip with none is left out."""
    return {row[0]: row[2] for row in _manifest_lines() if len(row) >= 3}


def write_manifest(stamps: dict[str, str], encoders: dict[str, str]) -> None:
    body = "".join(
        f"{clip} {stamps[clip]}"
        + (f" {encoders[clip]}" if clip in encoders else "")
        + "\n"
        for clip in sorted(stamps)
    )
    MANIFEST.write_text(_HEADER + body, encoding="utf-8")


@contextlib.contextmanager
def _locked(path: pathlib.Path) -> Iterator[None]:
    """Hold an exclusive lock on *path* for the block, on POSIX and on Windows.

    The lock file is never removed: unlinking it after the release lets a
    later run create a fresh inode and lock that one while another run is
    still inside the old one, which is the very race this guards.

    :param path: The lock file, created when missing and never truncated.
    """
    with path.open("a+b") as handle:
        if sys.platform == "win32":
            import msvcrt

            # msvcrt locks a byte range, and LK_LOCK gives up with EDEADLK
            # (EDEADLOCK on Windows, the same number) after ten tries a second
            # apart; a run behind a long batch keeps waiting, as flock does.
            while True:
                handle.seek(0)
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                    break
                except OSError as exc:
                    if exc.errno != errno.EDEADLK:
                        raise
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


def stamp(
    clips: Iterable[str],
    root: pathlib.Path | None = None,
    *,
    encoder: ClipEncoder | None,
    current: Mapping[str, str] | None = None,
) -> None:
    """Record the current fingerprint of *clips*, leaving the rest alone.

    Called by the renderer once a clip's four variants are on disk, so the
    stamp and the files it describes are written together and a re-render
    cannot forget to refresh it.

    Read-modify-write under a lock: re-rendering several clips at once is the
    normal way to work through a batch, and two runs finishing together would
    otherwise each write back the manifest they read, losing one of the two
    stamps -- the one failure mode of this file that would be invisible until
    CI asked for the missing clip.

    :param encoder: The encoder that wrote the clips' WebM, or None to keep
        the one recorded (re-extracted posters).
    :param current: The fingerprints of *root*'s clips, for a caller that
        has already taken them on a tree nothing changes since (a node run,
        on the archive it sent); None takes them here, every registered
        clip's, which takes from twenty seconds to a minute.
    :raises FileNotFoundError: when a clip steps an FDTD engine and the tree
        has no ``engine-digests.json``.
    :raises ValueError: when *encoder* is None and a clip has none recorded,
        or when a clip steps an FDTD engine and the tree's
        ``engine-digests.json`` does not hold the engines' digests.
    """
    names = list(clips)
    if not names:
        return
    if current is None:
        current = fingerprints(root or _SCRIPTS.parent)
    with _locked(MANIFEST.with_suffix(".lock")):
        stamps = read_manifest()
        encoders = read_encoders()
        for clip in names:
            if clip not in current:
                continue
            stamps[clip] = current[clip]
            if encoder is not None:
                encoders[clip] = encoder
            elif clip not in encoders:
                msg = f"{clip} has no encoder recorded; render it, not only its posters"
                raise ValueError(msg)
        write_manifest(stamps, encoders)
