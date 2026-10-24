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
  a wave field. A statement at the top of a module that the walk reaches
  counts as reached too, with what it names: ``figures.theme`` registers the
  dark field map that way;
* and inside ``phonometry.io``, the encode path every clip's frames go
  through (``write_video`` and the pipe into ffmpeg), except the encoder
  presets of ``quality``, which a clip's own encoder and options bypass;
* ``figures.theme.set_theme``, which is not called by the clip but decides
  the palette and the rcParams every frame is drawn with, and everything it
  reaches;
* the translation table entries the clip's own strings select (see
  :func:`_selected_translations`).

Two decisions keep the fingerprint from crying wolf, which matters more here
than anywhere else in the repo: a false positive costs a several-minute
re-render, so an alarm nobody believes would be worse than no alarm.

* **The hash is over the AST, not the source text.** Reformatting, a
  reflowed comment or a rewritten docstring cannot move it; only a change to
  what the code *does* can. Nor can the interpreter that reads it: the tree
  is printed without its empty lists, which is the one place Python 3.11 to
  3.14 print the same tree differently (:func:`_drop_empty_lists`).
* **The two big translation tables are excluded wholesale** and re-entered
  entry by entry. ``_ES_EXACT`` has thousands of lines and changes with every
  figure that gains a Spanish string; hashing it whole would mark all
  forty-two clips stale every time any unrelated figure is translated.

Known gaps, deliberately
------------------------

* **The library's physics.** A clip calls ``phonometry`` for its numbers,
  and outside ``phonometry._plot`` and ``phonometry.io`` this walk stops at
  the package boundary. Extending it there would trade a real but rare miss
  for a constant stream of false positives from refactors that change no
  pixel, and a library change that moves a number moves the static figures
  with it, where ``check_figures.py`` does catch it. Drawing code is another
  matter: a change to the colour a helper picks moves no number and still
  redraws every clip that asks for it, so ``phonometry._plot`` is walked
  like ``scripts/figures``.

  A clip that steps one of the FDTD engines is the exception, because its
  frames *are* the engine's numbers. It is tied to the engines' golden
  digests (``engine-digests.json``, see ``scripts/engine_digests.py``),
  which change when what the engines compute changes and never when their
  source is only rewritten: a reworded error message in the engine would
  otherwise mark every field clip stale. A clip counts as one that steps an
  engine when anything it reaches imports ``phonometry.simulation``.
* **Pattern translations reached only through an f-string.** The selection
  below matches a table pattern against the clip's literal text, and a label
  assembled at run time from several pieces may not be recognisable in the
  source. The code half still covers the usual case, because a string that
  gains a pattern normally gains it *because* the code that builds it
  changed.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import json
import pathlib
import sys
from typing import TYPE_CHECKING, Literal

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
    """One parsed source file: its symbols and what its imports point at."""

    def __init__(self, name: str, tree: ast.Module, owner: Sources) -> None:
        self.name = name
        self.tree = tree
        self.owner = owner
        self.symbols: dict[str, ast.AST] = {}
        #: local name -> (module, attribute); an empty attribute is the module
        self.imports: dict[str, tuple[str, str]] = {}
        #: top-level statements that define no name (see :meth:`collect`)
        self.body: list[ast.stmt] = []

    def collect(self, node: ast.stmt) -> None:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            self.symbols[node.name] = node
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                for name in _target_names(target):
                    self.symbols[name] = node
        elif isinstance(node, ast.AnnAssign):
            for name in _target_names(node.target):
                self.symbols[name] = node
        elif isinstance(node, ast.Import):
            for alias in node.names:
                self.imports[alias.asname or alias.name.split(".")[0]] = (
                    alias.name,
                    "",
                )
        elif isinstance(node, ast.ImportFrom):
            module = self._resolve_import(node)
            for alias in node.names:
                where = (module, alias.name) if module else ("", "")
                if module and f"{module}.{alias.name}" in self.owner.modules:
                    where = (f"{module}.{alias.name}", "")
                self.imports[alias.asname or alias.name] = where
        elif isinstance(node, ast.If | ast.Try):
            # Guarded imports (``if TYPE_CHECKING:``) and the sys.path dance.
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.stmt):
                    self.collect(child)
        elif isinstance(node, ast.Expr):
            # A bare top-level expression defines no name, and one of them
            # decides how every frame looks: the ``plt.rcParams.update({...})``
            # block of ``figures.theme`` sets the base font size, the grid and
            # its alpha. Collected under a synthetic name so the walk can pull
            # it in with the module's other roots.
            self.body.append(node)

    def _resolve_import(self, node: ast.ImportFrom) -> str:
        """The absolute module name of a ``from ... import`` statement."""
        if not node.level:
            return node.module or ""
        parts = self.name.split(".")
        # A package's ``__init__`` is addressed by the package name itself, so
        # one level up from a module is one part off its dotted name.
        base = parts[: len(parts) - node.level + (1 if self.is_package else 0)]
        return ".".join(base + ([node.module] if node.module else []))

    @property
    def is_package(self) -> bool:
        return self.name in self.owner.packages


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
        parsed: dict[str, ast.Module] = {}
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
                parsed[name] = ast.fix_missing_locations(_RuntimeView().visit(tree))
        # Every module name has to be known before the imports are resolved:
        # ``from . import media`` reads as a module reference or as a symbol
        # depending on whether ``figures.media`` exists.
        for name, tree in parsed.items():
            self.modules[name] = _Module(name, tree, self)
        for module in self.modules.values():
            for node in module.tree.body:
                module.collect(node)

    def engine_digest(self) -> str:
        """:func:`engine_digest` of this tree, read once.

        :raises FileNotFoundError: when the tree has no ``engine-digests.json``.
        """
        if self._engine_digest is None:
            self._engine_digest = engine_digest(self.root)
        return self._engine_digest

    # -- name resolution ---------------------------------------------------

    def resolve(
        self, module: str, name: str, _seen: frozenset[Symbol] = frozenset()
    ) -> Symbol | None:
        """The defining ``(module, name)`` of *name* as seen from *module*."""
        mod = self.modules.get(module)
        if mod is None or (module, name) in _seen:
            return None
        if name in mod.symbols:
            return (module, name)
        target = mod.imports.get(name)
        if target is None or not target[1]:
            return None
        return self.resolve(target[0], target[1], _seen | {(module, name)})

    def module_of(self, module: str, name: str) -> str | None:
        """The module *name* refers to, when it is an imported module."""
        mod = self.modules.get(module)
        if mod is None:
            return None
        target = mod.imports.get(name)
        if target is not None and not target[1] and target[0] in self.modules:
            return target[0]
        if f"{module}.{name}" in self.modules:
            return f"{module}.{name}"
        return None

    # -- the walk ----------------------------------------------------------

    def closure(self, roots: Iterable[Symbol]) -> set[Symbol]:
        """Every package symbol reachable from *roots*, roots included.

        Reaching a symbol reaches the top-level statements of its module too
        (:attr:`_Module.body`), which run when the module is imported:
        ``figures.theme`` registers the dark field map in one, so what such
        a statement names is followed like what a function names.
        """
        seen: set[Symbol] = set()
        modules: set[str] = set()
        stack = list(roots)
        while stack:
            symbol = stack.pop()
            if symbol in seen or symbol in _IGNORED or symbol in _TABLES:
                continue
            node = self.node(symbol)
            if node is None:
                continue
            seen.add(symbol)
            stack.extend(self.referenced(symbol[0], node))
            if symbol[0] not in modules:
                modules.add(symbol[0])
                for statement in self.modules[symbol[0]].body:
                    stack.extend(self.referenced(symbol[0], statement))
        return seen

    def node(self, symbol: Symbol) -> ast.AST | None:
        mod = self.modules.get(symbol[0])
        return None if mod is None else mod.symbols.get(symbol[1])

    def referenced(self, module: str, node: ast.AST) -> Iterator[Symbol]:
        """The package symbols *node* names, from inside *module*."""
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                found = self.resolve(module, child.id)
                if found is not None:
                    yield found
            elif isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name):
                target = self.module_of(module, child.value.id)
                if target is not None:
                    found = self.resolve(target, child.attr)
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
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
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


def _module_level(body: list[ast.stmt]) -> str:
    """The part of a module body that can reach a frame, hashed stably.

    Two things are taken out, both because leaving them in makes a change
    that cannot move a pixel look like one, which is the false alarm this
    module says it would rather not raise than raise wrongly.

    A block guarded by ``if TYPE_CHECKING:`` is read by a type checker and by
    nothing else. No name it binds exists while the clip renders, so moving
    an import under that guard changes what mypy sees and nothing else.

    Import *order* goes too, but the imports themselves stay: they are
    hashed as a sorted set. Sorting them is what an import sorter does, and
    it cannot change which name ends up bound to which module. Dropping them
    would not be safe, because the walk stops at the package boundary, so for
    ``import numpy as np`` the statement is the only record the fingerprint
    has that the name points where it did.
    """
    live = [
        s for s in body if not (isinstance(s, ast.If) and _is_type_checking(s.test))
    ]
    imports = sorted(
        _dump(s)
        for s in live
        if isinstance(s, (ast.Import, ast.ImportFrom)) and not _typing_only_import(s)
    )
    rest = [s for s in live if not isinstance(s, (ast.Import, ast.ImportFrom))]
    return "\x00".join([*imports, _dump(ast.Module(body=rest, type_ignores=[]))])


def _typing_only_import(node: ast.stmt) -> bool:
    """Is *node* an import that only a type checker reads?

    ``from __future__ import annotations`` changes how annotations are
    evaluated, and the annotations themselves are removed from the runtime
    view before anything is hashed, so the switch controls nothing that can
    reach a frame. ``from typing import TYPE_CHECKING`` binds the guard whose
    whole block is already taken out above. Either statement appearing or
    disappearing is an artefact of typing work, not of drawing work.

    Only the exact single-name forms are dropped: ``from typing import
    TYPE_CHECKING, cast`` binds ``cast``, which is a real runtime name, and
    stays recorded whole.
    """
    if not isinstance(node, ast.ImportFrom):
        return False
    if node.module == "__future__":
        return True
    return node.module == "typing" and [a.name for a in node.names] == ["TYPE_CHECKING"]


def _literals(sources: Sources, symbols: Iterable[Symbol]) -> set[str]:
    """Every string literal in *symbols*, f-string fragments included."""
    out: set[str] = set()
    for symbol in symbols:
        node = sources.node(symbol)
        if node is None:
            continue
        for child in ast.walk(_strip_docstrings(node)):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                out.add(child.value)
    return out


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
    i18n = sources.modules["figures.i18n"]
    exact: list[tuple[str, str]] = []
    patterns: list[tuple[str, str]] = []
    node = i18n.symbols.get("_ES_EXACT")
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
        for key, value in zip(node.value.keys, node.value.values, strict=True):
            pair = _literal_pair(key, value)
            if pair is not None:
                exact.append(pair)
    node = i18n.symbols.get("_ES_PATTERNS")
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
        for element in node.value.elts:
            if isinstance(element, ast.Tuple) and len(element.elts) == 2:
                pair = _literal_pair(element.elts[0], element.elts[1])
                if pair is not None:
                    patterns.append(pair)
    return exact, patterns


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
    measured (the ``environment`` block) is not what the engines compute.

    :raises FileNotFoundError: when *root* has no ``engine-digests.json``.
    """
    path = root / ENGINE_DIGESTS
    if not path.exists():
        msg = (
            f"{path} is missing; record the engines' digests with `make engine-digests`"
        )
        raise FileNotFoundError(msg)
    data = json.loads(path.read_text(encoding="utf-8"))
    numbers = {"scenarios": data["scenarios"], "fluid_energy": data["fluid_energy"]}
    return hashlib.sha256(json.dumps(numbers, sort_keys=True).encode()).hexdigest()


def _names_engine(module: str, attr: str) -> bool:
    """Whether ``from <module> import <attr>`` reaches the simulation package."""
    if module == "phonometry":
        return attr == "simulation"
    return module == "phonometry.simulation" or module.startswith(
        "phonometry.simulation."
    )


def _imports_engine(node: ast.Import | ast.ImportFrom) -> bool:
    if isinstance(node, ast.Import):
        return any(_names_engine(alias.name, "") for alias in node.names)
    return (
        node.level == 0
        and node.module is not None
        and any(_names_engine(node.module, alias.name) for alias in node.names)
    )


def _uses_engine(module: _Module, node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Import | ast.ImportFrom) and _imports_engine(child):
            return True
        if isinstance(child, ast.Name) and child.id in module.imports:
            target, attr = module.imports[child.id]
            if _names_engine(target, attr):
                return True
    return False


def steps_an_engine(sources: Sources, symbols: Iterable[Symbol]) -> bool:
    """Whether a clip that reaches *symbols* uses the simulation package.

    Either something it reaches imports the package where it uses it (the
    field builders do, inside the function), or it names what a module it
    reaches imported from the package at the top (a material such as
    ``ALUMINUM``).
    """
    chosen = list(symbols)
    nodes = [(module, sources.node((module, name))) for module, name in chosen]
    for module in {module for module, _ in chosen}:
        nodes.extend((module, statement) for statement in sources.modules[module].body)
    return any(
        node is not None and _uses_engine(sources.modules[module], node)
        for module, node in nodes
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
    """
    roots = [entry, *_EXTRA_ROOTS]
    symbols = sources.closure(roots)
    code = sorted(
        f"{module}.{name}\x00{_dump(sources.node((module, name)))}"  # type: ignore[arg-type]
        for module, name in symbols
    )
    # Plus the top-level statements of every module the clip reaches. They
    # define no name, so the walk cannot reach them by reference, and one of
    # them is ``figures.theme``'s ``plt.rcParams.update({...})``: the base font
    # size, the grid and its alpha, i.e. how every frame looks.
    for module in sorted({module for module, _ in symbols}):
        body = sources.modules[module].body
        if body:
            code.append(f"{module}.<module>\x00" + _module_level(body))
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
#     python scripts/generate_graphs.py --animations --anim <clip>
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
    :raises ValueError: when *encoder* is None and a clip has none recorded.
    """
    import fcntl

    names = list(clips)
    if not names:
        return
    if current is None:
        current = fingerprints(root or _SCRIPTS.parent)
    # The lock file is never removed: unlinking it after the release lets a
    # later run create a fresh inode and lock that one while another run is
    # still inside the old one, which is the very race this guards.
    lock = MANIFEST.with_suffix(".lock")
    with lock.open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            stamps = read_manifest()
            encoders = read_encoders()
            for clip in names:
                if clip not in current:
                    continue
                stamps[clip] = current[clip]
                if encoder is not None:
                    encoders[clip] = encoder
                elif clip not in encoders:
                    msg = (
                        f"{clip} has no encoder recorded; "
                        "render it, not only its posters"
                    )
                    raise ValueError(msg)
            write_manifest(stamps, encoders)
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
