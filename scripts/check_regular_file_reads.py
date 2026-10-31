#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a reader in the library that opens a file without asking what it is.

A name a caller or the environment hands the library can hold something other
than a file: a named pipe no one writes to keeps an open waiting for a writer
that may never come, a device such as ``/dev/zero`` keeps a read going
without end, and a directory holds nothing to read. Every reader of such a
name refuses each before it waits on it, through the shared check of
``src/phonometry/_internal/json_input.py``: :func:`open_regular` and
:func:`read_at_most` look at the name, open it without waiting and ask the
open file again, and :func:`not_regular_at` says what is at a name that a
reader of another library is about to open itself.

This reads every module under ``src/phonometry`` but the shared one and
reports two shapes:

- **An open of its own**: ``open()``, ``io.open()``, ``io.FileIO()`` or
  ``os.open()``, a ``.open()`` with no mode or a mode that reads without
  writing (``"rb"``, ``"r"``), and ``.read_bytes()`` and ``.read_text()``. A
  reader opens a file through the shared check instead; a mode that writes
  (``"wb"``, ``"xb"``, ``"ab"``, ``"r+b"``) is a writer's, and a ``.open()``
  whose first argument is not a text is no file's.
- **A reader of another library that opens the name itself**: SciPy's
  ``wavfile.read``, python-soundfile's ``read``, ``info``, ``blocks`` and
  ``SoundFile``, NumPy's ``load``, ``loadtxt``, ``genfromtxt``, ``fromfile``
  and ``memmap``, the ``open`` of ``wave``, ``aifc``, ``gzip``, ``bz2``,
  ``lzma``, ``tarfile``, ``codecs`` and Pillow's ``Image``,
  ``zipfile.ZipFile``, each unless its mode writes, and the ``copyfile``,
  ``copy`` and ``copy2`` of ``shutil``, which read their source by its name.
  Each must follow, in the same function, a call of a check on the same name:
  one of the three shared functions, or a function of the library whose first
  parameter it hands to one of them (found by following such calls until no
  new one turns up, so ``require_regular_audio(path)`` counts, and so does a
  reader that calls it on its own first parameter). The name is compared as
  written, once ``str()``, ``Path()`` and ``os.fspath()`` around it are taken
  off.

A check is known by the module that defines it, never by the last part of its
name alone: a call is followed to the function it reaches through the
module's imports (relative ones included, and a name a package imports from
one of its modules), the module's own functions, the functions around it, and
``self`` or ``cls`` in a method. So ``np.info(path)`` asks nothing of the name
though the library's ``info`` is a check, and neither does a method of another
object called ``read_at_most``, or a function of the reader's own module that
shares a check's name and checks nothing. A call the check cannot follow
counts as no check.

A call is named by what its module imports: ``import soundfile as snd``,
``from scipy.io.wavfile import read as wav_read`` and ``from io import
FileIO`` are followed, and so is a name bound to a module or a reader by an
assignment (``snd = soundfile``) anywhere in the module. A name nothing binds
is taken at its word, with the spellings the library uses (``sf`` for
python-soundfile, ``np`` for NumPy, ``wavfile`` for SciPy's module, ``Image``
for Pillow's), so that a module handed in as a parameter is read too.

The order is read from the source, not from the paths the function can take:
a check inside one branch of an ``if`` and a read after the ``if`` pass. A
``.open()`` given its mode through a name is not read either, nor is a reader
reached through ``getattr()`` or a ``functools.partial``. The check is there
to keep the readers on the shared route, and the tests of each reader (a pipe,
a device and a directory at the name, each refused within seconds) are what
prove they refuse.

A read of the library's own files, which no caller names (the package's data
through ``importlib.resources``, its own modules), goes in :data:`EXEMPT`,
keyed by file and function with the reason; an entry that covers nothing is
reported too.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ast_scan import ROOT, exempted, python_files, relative

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Iterator, Mapping, Sequence

#: The library this reads, the default when no path is given.
SOURCE = ROOT / "src" / "phonometry"
#: The module that holds the shared check, whose opens are the check itself,
#: by the end of its path, so that another checkout of the library is read the
#: same way.
OWNER = ("phonometry", "_internal", "json_input.py")

#: The shared functions that look at what a name holds before it is read.
CHECKS = frozenset({"not_regular_at", "open_regular", "read_at_most"})
#: The package every module of the library is named from.
PACKAGE = "phonometry"
#: The module that holds :data:`CHECKS`, by the name it is imported by.
SHARED = f"{PACKAGE}._internal.json_input"
#: :data:`CHECKS` by the module that defines them.
_SHARED_CHECKS = frozenset(f"{SHARED}.{name}" for name in CHECKS)

#: The readers of other libraries that open a name themselves, by the module
#: that holds them and their name.
FOREIGN_READERS = frozenset(
    {
        "scipy.io.wavfile.read",
        "soundfile.read",
        "soundfile.info",
        "soundfile.blocks",
        "soundfile.SoundFile",
        "numpy.load",
        "numpy.loadtxt",
        "numpy.genfromtxt",
        "numpy.fromfile",
        "numpy.memmap",
        "wave.open",
        "aifc.open",
        "gzip.open",
        "bz2.open",
        "lzma.open",
        "tarfile.open",
        "zipfile.ZipFile",
        "codecs.open",
        "PIL.Image.open",
        "shutil.copyfile",
        "shutil.copy",
        "shutil.copy2",
    }
)
#: The opens of Python's own, by the module that holds them, with the position
#: of the mode among their arguments; ``os.open`` takes flags, and counts
#: whatever they are.
OWN_OPENS = {
    "builtins.open": 1,
    "io.open": 1,
    "_io.open": 1,
    "io.FileIO": 1,
    "_io.FileIO": 1,
    "os.open": None,
}
#: The readers of :data:`FOREIGN_READERS` that write when their mode says so,
#: and the position of the mode among their arguments.
_MODE_POSITION = {
    reader: 1
    for reader in FOREIGN_READERS
    if reader.endswith((".open", ".SoundFile", ".ZipFile"))
}
#: The modules the library names by a short spelling, for a name no import of
#: the module binds: a module handed in as a parameter, or bound by a call
#: (``sf = _import_soundfile(...)``).
_SPELLINGS = {
    "sf": "soundfile",
    "np": "numpy",
    "wavfile": "scipy.io.wavfile",
    "Image": "PIL.Image",
    "FileIO": "io.FileIO",
    "open": "builtins.open",
}
#: The calls taken off a name before two names are compared.
_WRAPPERS = frozenset({"str", "Path", "PurePath", "fspath"})
#: The methods that read a whole file by its name.
_WHOLE_FILE_READS = frozenset({"read_bytes", "read_text"})

#: The reads of the library's own files, which no caller names, keyed by the
#: file relative to the repository and the function that holds the read.
EXEMPT: dict[tuple[str, str], str] = {
    ("src/phonometry/_version.py", "<module>"): (
        "the VERSION file of a source checkout, two directories above the "
        "package, read only when the package is not installed"
    ),
    ("src/phonometry/_internal/catalogue.py", "read_packaged"): (
        "a published table of the package's own data, through importlib.resources"
    ),
    ("src/phonometry/aircraft/anp_fleet.py", "_table_text"): (
        "an ANP table of the package's own data when the package is inside a zip "
        "archive; a caller's table, and the package's on a file system, go "
        "through read_at_most"
    ),
    ("src/phonometry/simulation/_remote/client.py", "_inline_bootstrap"): (
        "the library's own bootstrap module, sent to a node as its source"
    ),
    ("src/phonometry/simulation/_remote/package.py", "package_from"): (
        "the files of the imported phonometry package itself, each taken only "
        "when is_file() finds a regular file there"
    ),
    ("src/phonometry/simulation/_video_job.py", "_ScratchVideo.__init__"): (
        "the video the node's own encoder wrote, in the scratch directory the "
        "node made for the run; no caller names it"
    ),
    ("src/phonometry/simulation/video.py", "_node_video"): (
        "_PartialFile.open, a method of the library's own that creates the "
        "partial video exclusively; no file is read"
    ),
}


@dataclass(frozen=True)
class Finding:
    """One read of a file by its name that skips the shared check."""

    path: pathlib.Path
    line: int
    function: str
    shape: str
    source: str

    @property
    def key(self) -> tuple[str, str]:
        """The file relative to the repository, and the function, as EXEMPT keys them."""
        return relative(self.path), self.function

    def describe(self) -> str:
        """One line naming the place, the shape and the code."""
        return (
            f"{relative(self.path)}:{self.line}  {self.function}  "
            f"{self.shape}: {self.source}"
        )


def _callee(call: ast.Call) -> str | None:
    """The name a call is made through: ``f`` of ``f()`` and of ``a.b.f()``."""
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _receiver(call: ast.Call) -> str | None:
    """The last name before the method: ``b`` of ``a.b.f()``, ``a`` of ``a.f()``."""
    if not isinstance(call.func, ast.Attribute):
        return None
    value = call.func.value
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute):
        return value.attr
    return None


def _subject(node: ast.expr) -> str:
    """A name as written, with ``str()``, ``Path()`` and ``os.fspath()`` taken off."""
    while (
        isinstance(node, ast.Call)
        and _callee(node) in _WRAPPERS
        and len(node.args) == 1
        and not node.keywords
    ):
        node = node.args[0]
    return ast.unparse(node)


def _first_argument(call: ast.Call) -> ast.expr | None:
    """The first argument of *call*, positional or the only keyword one."""
    if call.args:
        first = call.args[0]
        return None if isinstance(first, ast.Starred) else first
    if len(call.keywords) == 1 and call.keywords[0].arg is not None:
        return call.keywords[0].value
    return None


def _mode(call: ast.Call, position: int) -> ast.expr | None:
    """The mode a call opens with: the argument at *position* or ``mode=``."""
    for keyword in call.keywords:
        if keyword.arg == "mode":
            return keyword.value
    if len(call.args) > position:
        return call.args[position]
    return None


def _reads_only(mode: ast.expr | None) -> bool:
    """Whether a mode reads without writing; an unknown mode counts as a read."""
    if mode is None:
        return True
    if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
        return "r" in mode.value and "+" not in mode.value
    return True


def _dotted(node: ast.expr) -> list[str] | None:
    """``["a", "b", "f"]`` for ``a.b.f``, or ``None`` when no name starts it."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return parts[::-1]


def _resolved(parts: Sequence[str], aliases: Mapping[str, str]) -> str:
    """A dotted name with its first part replaced by what it is bound to."""
    head = aliases.get(parts[0]) or _SPELLINGS.get(parts[0], parts[0])
    return ".".join([head, *parts[1:]])


def _imported_from(node: ast.ImportFrom, package: str) -> str | None:
    """The module a ``from`` import takes its names from, a relative one resolved.

    *package* is the package of the module that holds the import, empty for a
    module outside any; ``None`` when the import climbs out of it.
    """
    if not node.level:
        return node.module
    parts = package.split(".") if package else []
    up = node.level - 1
    if up > len(parts):
        return None
    base = parts[: len(parts) - up]
    if node.module:
        base.extend(node.module.split("."))
    return ".".join(base) or None


def _imported(node: ast.Import | ast.ImportFrom, package: str = "") -> dict[str, str]:
    """The names one import binds, each with the dotted name it stands for.

    ``import a.b`` binds ``a``, ``import a.b as c`` binds ``c`` to ``a.b``,
    ``from a import f as g`` binds ``g`` to ``a.f``. A relative import is read
    from *package*, the package of the module that holds it, so
    ``from ._audio_file import open_audio`` in ``phonometry.io`` binds
    ``open_audio`` to ``phonometry.io._audio_file.open_audio``.
    """
    if isinstance(node, ast.ImportFrom):
        module = _imported_from(node, package)
        if module is None:
            return {}
        return {
            alias.asname or alias.name: f"{module}.{alias.name}"
            for alias in node.names
            if alias.name != "*"
        }
    bound: dict[str, str] = {}
    for alias in node.names:
        head = alias.name.split(".", 1)[0]
        bound[alias.asname or head] = alias.name if alias.asname else head
    return bound


def aliases_of(tree: ast.AST, package: str = "") -> dict[str, str]:
    """What each name of a module the imports and assignments bind stands for.

    The imports as :func:`_imported` reads them, the relative ones from
    *package*; then a name bound by an assignment to a dotted name
    (``snd = soundfile``, ``reader = sf.read``) stands for what that name
    stands for, the assignments taken in the order of the source.
    """
    aliases: dict[str, str] = {}
    assignments: list[tuple[str, list[str], tuple[int, int]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            aliases.update(_imported(node, package))
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(target := node.targets[0], ast.Name)
            and (parts := _dotted(node.value)) is not None
        ):
            assignments.append((target.id, parts, (node.lineno, node.col_offset)))
    for name, parts, _place in sorted(assignments, key=lambda bound: bound[2]):
        aliases[name] = _resolved(parts, aliases)
    return aliases


def _names(call: ast.Call, aliases: Mapping[str, str]) -> set[str]:
    """What *call* calls, by the module that holds it, as far as it can be told.

    The whole dotted name, resolved through *aliases*, and, for a method of
    something no name starts (``self.sf.read``), the module the last name
    before the method is spelt as.
    """
    names: set[str] = set()
    parts = _dotted(call.func)
    if parts is not None:
        names.add(_resolved(parts, aliases))
    receiver = _receiver(call)
    callee = _callee(call)
    if receiver is not None and callee is not None:
        names.add(_resolved([receiver, callee], aliases))
    return names


def _own_open(call: ast.Call, aliases: Mapping[str, str]) -> bool:
    """Whether *call* opens or reads a file by its name, by itself."""
    callee = _callee(call)
    names = _names(call, aliases)
    for name, position in OWN_OPENS.items():
        if name in names:
            return position is None or _reads_only(_mode(call, position))
    if not names.isdisjoint(FOREIGN_READERS):
        return False
    if callee in _WHOLE_FILE_READS and isinstance(call.func, ast.Attribute):
        return True
    if callee == "open" and isinstance(call.func, ast.Attribute):
        mode = _mode(call, 0)
        if mode is None:
            return True
        # A first argument that is not a text is no mode: a method of
        # another object that is called open.
        return (
            isinstance(mode, ast.Constant)
            and isinstance(mode.value, str)
            and _reads_only(mode)
        )
    return False


def _foreign_read(call: ast.Call, aliases: Mapping[str, str]) -> bool:
    """Whether *call* is a reader of another library that opens a name itself."""
    found = _names(call, aliases) & FOREIGN_READERS
    if not found:
        return False
    position = _MODE_POSITION.get(min(found))
    return position is None or _reads_only(_mode(call, position))


def _functions(tree: ast.AST) -> Iterator[tuple[str, ast.AST]]:
    """Every function with its qualified name, and the module as ``<module>``."""

    def walk(node: ast.AST, scope: str) -> Iterator[tuple[str, ast.AST]]:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                inner = f"{scope}.{child.name}" if scope else child.name
                if not isinstance(child, ast.ClassDef):
                    yield inner, child
                yield from walk(child, inner)

    yield "<module>", tree
    yield from walk(tree, "")


def _own_calls(scope: ast.AST) -> list[ast.Call]:
    """The calls of *scope* in source order, leaving out those of nested functions.

    The body of a class belongs to the scope that holds the class, its methods
    to themselves.
    """
    calls: list[ast.Call] = []
    pending = list(ast.iter_child_nodes(scope))
    while pending:
        node = pending.pop()
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if isinstance(node, ast.Call):
            calls.append(node)
        pending.extend(ast.iter_child_nodes(node))
    calls.sort(key=lambda call: (call.lineno, call.col_offset))
    return calls


@dataclass(frozen=True)
class _Scope:
    """A function of a module, or the module itself, with the calls it makes."""

    path: pathlib.Path
    name: str
    node: ast.AST
    calls: list[ast.Call]
    aliases: Mapping[str, str]
    #: The dotted name the module is imported by.
    module: str = ""
    #: The functions and classes the module defines, by their qualified
    #: names, ``True`` for a class.
    defined: Mapping[str, bool] = field(default_factory=dict)

    @property
    def qualified(self) -> str:
        """The function by the module that defines it: ``phonometry.io._wav.read_wav``."""
        return f"{self.module}.{self.name}"


def module_name(path: pathlib.Path) -> str:
    """The dotted name *path* is imported by.

    Read from the last directory called ``phonometry`` above it down, the
    ``__init__`` of a package left off; a module outside the package is
    named by its file alone.
    """
    parts = path.resolve().with_suffix("").parts
    tops = [index for index, part in enumerate(parts[:-1]) if part == PACKAGE]
    named = list(parts[tops[-1] :]) if tops else [parts[-1]]
    if named[-1] == "__init__" and len(named) > 1:
        named.pop()
    return ".".join(named)


def _package_of(path: pathlib.Path, module: str) -> str:
    """The package a relative import of the module at *path* is read from."""
    if path.name == "__init__.py":
        return module
    return module.rpartition(".")[0]


def _definitions(tree: ast.AST) -> dict[str, bool]:
    """Each function and class *tree* defines, by its qualified name, ``True`` for a class."""
    defined: dict[str, bool] = {}

    def walk(node: ast.AST, scope: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                inner = f"{scope}.{child.name}" if scope else child.name
                defined[inner] = isinstance(child, ast.ClassDef)
                walk(child, inner)

    walk(tree, "")
    return defined


def _top_level_imports(tree: ast.Module) -> Iterator[ast.Import | ast.ImportFrom]:
    """The imports a module makes as it is imported, ``if`` and ``try`` blocks included."""
    pending: list[ast.stmt] = list(tree.body)
    while pending:
        statement = pending.pop()
        if isinstance(statement, ast.Import | ast.ImportFrom):
            yield statement
        elif isinstance(statement, ast.If | ast.Try):
            pending.extend(statement.body)
            pending.extend(statement.orelse)
            if isinstance(statement, ast.Try):
                pending.extend(statement.finalbody)
                for handler in statement.handlers:
                    pending.extend(handler.body)


def exports_of(path: pathlib.Path, tree: ast.Module) -> dict[str, str]:
    """What each name a module imports stands for, by the module's own name.

    ``from ._audio_file import open_audio`` in ``phonometry/io/__init__.py``
    makes ``phonometry.io.open_audio`` stand for
    ``phonometry.io._audio_file.open_audio``, so that a module that imports
    it from the package reaches the function itself.
    """
    module = module_name(path)
    package = _package_of(path, module)
    return {
        f"{module}.{name}": target
        for node in _top_level_imports(tree)
        for name, target in _imported(node, package).items()
    }


def _canonical(name: str, exports: Mapping[str, str]) -> str:
    """*name* followed through the imports of :func:`exports_of` to where it is defined."""
    seen = {name}
    while True:
        parts = name.split(".")
        for end in range(len(parts), 0, -1):
            head = ".".join(parts[:end])
            if head in exports:
                name = ".".join([exports[head], *parts[end:]])
                break
        else:
            return name
        if name in seen:
            return name
        seen.add(name)


def _local(name: str, scope: _Scope) -> str | None:
    """The function or class of the module that *name* is, seen from *scope*.

    Looked up as Python looks a name up: in the function itself, in the
    functions around it (a class around it is skipped, as Python skips it),
    then at the top of the module.
    """
    parts = [] if scope.name == "<module>" else scope.name.split(".")
    for end in range(len(parts), -1, -1):
        prefix = ".".join(parts[:end])
        if prefix and scope.defined.get(prefix):
            continue
        candidate = f"{prefix}.{name}" if prefix else name
        if candidate in scope.defined:
            return f"{scope.module}.{candidate}"
    return None


def _owner(scope: _Scope) -> str | None:
    """The class *scope* is a method of, by its qualified name, or ``None``."""
    owner = scope.name.rpartition(".")[0]
    return owner if owner and scope.defined.get(owner) else None


def qualified_callee(
    call: ast.Call, scope: _Scope, exports: Mapping[str, str]
) -> str | None:
    """The function *call* reaches, by the module that defines it, or ``None``.

    ``self.f()`` and ``cls.f()`` in a method reach ``f`` of its class; a bare
    or dotted name is read through the functions of the module and the
    functions around the call, then through what the module imports, and
    followed through :func:`exports_of`. A call that starts from anything
    else (``handle.read_at_most(path)``, ``np.info(path)`` once ``np`` is
    NumPy) reaches no function of the library.
    """
    parts = _dotted(call.func)
    if parts is None:
        return None
    head, rest = parts[0], parts[1:]
    owner = _owner(scope)
    if head in {"self", "cls"} and len(rest) == 1 and owner is not None:
        return f"{scope.module}.{owner}.{rest[0]}"
    local = _local(head, scope)
    if local is not None:
        return ".".join([local, *rest])
    if head in scope.aliases:
        return _canonical(".".join([scope.aliases[head], *rest]), exports)
    return None


def _scopes(path: pathlib.Path, tree: ast.AST) -> list[_Scope]:
    """Every function of *tree*, and the module, each with its own calls."""
    module = module_name(path)
    aliases = aliases_of(tree, _package_of(path, module))
    defined = _definitions(tree)
    return [
        _Scope(path, name, node, _own_calls(node), aliases, module, defined)
        for name, node in _functions(tree)
    ]


def _first_parameter(function: ast.AST) -> str | None:
    """The first parameter of a function that is not ``self`` or ``cls``."""
    if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
        return None
    for parameter in (*function.args.posonlyargs, *function.args.args):
        if parameter.arg not in {"self", "cls"}:
            return parameter.arg
    return None


def checking_functions(
    scopes: Sequence[_Scope], exports: Mapping[str, str]
) -> frozenset[str]:
    """:data:`CHECKS` and every function that hands its first parameter to one.

    Each by the module that defines it (:func:`qualified_callee`), followed
    until no new function turns up, so a reader that checks its name through
    a helper counts as a check for its own callers, and a function that hands
    its name to a namesake of a check (``np.info``) does not.
    """
    # Each function with the callees it hands its first parameter to, worked
    # out once; the search below only grows the set of checks.
    candidates: list[tuple[str, set[str]]] = []
    for scope in scopes:
        parameter = _first_parameter(scope.node)
        if parameter is None or not isinstance(
            scope.node, ast.FunctionDef | ast.AsyncFunctionDef
        ):
            continue
        handed = {
            callee
            for call in scope.calls
            if (argument := _first_argument(call)) is not None
            and _subject(argument) == parameter
            and (callee := qualified_callee(call, scope, exports)) is not None
        }
        if handed:
            candidates.append((scope.qualified, handed))
    found = set(_SHARED_CHECKS)
    grew = True
    while grew:
        grew = False
        for name, handed in candidates:
            if name not in found and not handed.isdisjoint(found):
                found.add(name)
                grew = True
    return frozenset(found)


def _checked_before(
    scope: _Scope,
    read: ast.Call,
    checks: frozenset[str],
    exports: Mapping[str, str],
) -> bool:
    """Whether a check of the name *read* opens comes before it in *scope*."""
    argument = _first_argument(read)
    if argument is None:
        return False
    name = _subject(argument)
    place = (read.lineno, read.col_offset)
    for call in scope.calls:
        if call is read or (call.lineno, call.col_offset) >= place:
            continue
        checked = _first_argument(call)
        if (
            checked is not None
            and _subject(checked) == name
            and qualified_callee(call, scope, exports) in checks
        ):
            return True
    return False


def scan(
    scope: _Scope, checks: frozenset[str], exports: Mapping[str, str]
) -> list[Finding]:
    """Every read of a file by its name in *scope* that skips the shared check."""
    findings: list[Finding] = []
    for call in scope.calls:
        if _own_open(call, scope.aliases):
            shape = "an open of its own; read through open_regular or read_at_most"
        elif _foreign_read(call, scope.aliases) and not _checked_before(
            scope, call, checks, exports
        ):
            shape = (
                "a reader of another library with no check of the name before it; "
                "ask not_regular_at, or a check of the library, first"
            )
        else:
            continue
        findings.append(
            Finding(scope.path, call.lineno, scope.name, shape, ast.unparse(call))
        )
    return findings


def check(files: Sequence[pathlib.Path]) -> tuple[list[Finding], list[tuple[str, str]]]:
    """The findings :data:`EXEMPT` does not cover, and its entries that cover none.

    :param files: The modules to read; the shared module is left out.
    """
    trees = {
        path: ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for path in files
    }
    scopes = [scope for path, tree in trees.items() for scope in _scopes(path, tree)]
    exports = {
        name: target
        for path, tree in trees.items()
        for name, target in exports_of(path, tree).items()
    }
    checks = checking_functions(scopes, exports)
    findings = [
        finding
        for scope in scopes
        if scope.path.resolve().parts[-len(OWNER) :] != OWNER
        for finding in scan(scope, checks, exports)
    ]
    return exempted(findings, EXEMPT)


def main(argv: Sequence[str] | None = None) -> int:
    """Report every read that skips the shared check; 1 when there is one."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "paths",
        nargs="*",
        help="modules or directories to read (default: src/phonometry)",
    )
    args = parser.parse_args(argv)
    files = python_files(args.paths, SOURCE)
    findings, stale = check(files)
    if args.paths:
        # An exemption is stale only against the whole library.
        stale = []
    for finding in findings:
        print(finding.describe())
    for file, function in stale:
        print(f"{file}  {function}  exempt, but reads nothing there any more")
    if findings or stale:
        print(
            f"\n{len(findings)} read(s) of a file by its name skip the shared check, "
            f"and {len(stale)} exemption(s) cover none.",
            file=sys.stderr,
        )
        return 1
    print(
        f"Every reader of the {len(files)} modules read asks what a name holds first."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
