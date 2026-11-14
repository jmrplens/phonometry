#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every script decodes what a child process prints in an encoding it names.

The scripts read what git, ffmpeg, ffprobe, node and Python children print:
the names git lists with ``-z``, ffprobe's JSON, the glossary node dumps.
``subprocess.run(..., text=True)`` decodes that output with the locale's
encoding unless it is told otherwise, which on Windows under Python 3.12 to
3.14 is the ANSI code page (cp1252 on an English runner), while git, ffmpeg
and node write UTF-8. A name or a word that holds a character outside ASCII
then comes back misread, ``acústica`` as ``acÃºstica``, with no error: the
llms.txt generator, the catalogue-link gate and the figure gates looked
for files that do not exist under those names.

This reads every module under ``scripts/`` and fails on a call to
``subprocess.run``, ``check_output``, ``Popen``, ``call`` or ``check_call``,
under any name a script calls it by (imported as, assigned to or taken as a
parameter that defaults to it), that asks for text (``text`` or
``universal_newlines``) without naming its ``encoding``.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

pytestmark = pytest.mark.whole_tree

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"

#: The functions of :mod:`subprocess` that decode a child's output for text.
SPAWNS = frozenset({"run", "check_output", "Popen", "call", "check_call"})

#: The keywords that ask a spawn for text instead of bytes.
TEXT_KEYWORDS = frozenset({"text", "universal_newlines"})

#: Spawns left as they are, by module and function, with the reason. The
#: one entry reads ffmpeg's own banner, ``SVT-AV1 Encoder Lib v4.2.0``,
#: from a black frame encoded to nowhere, so its text is ASCII in every
#: encoding; and the function is in the fingerprint of every clip
#: (``scripts/animation_fingerprint.py``), whose syntax tree any keyword
#: added to the call moves, so naming the encoding there marks all 43 clips
#: as drawn by changed code until each is drawn again.
KEPT = {
    ("scripts/figures/media.py", "read_svt_av1_version"): (
        "reads ffmpeg's ASCII banner; the call is in every clip's fingerprint"
    ),
}


def _asks_for_text(call: ast.Call) -> bool:
    """Whether a call passes ``text`` or ``universal_newlines`` as anything but false."""
    for keyword in call.keywords:
        if keyword.arg not in TEXT_KEYWORDS:
            continue
        value = keyword.value
        if isinstance(value, ast.Constant) and value.value in (False, None):
            continue
        return True
    return False


def _is_spawn(value: ast.expr | None, names: set[str]) -> bool:
    """Whether an expression names a spawn: ``subprocess.run`` or a name bound to one."""
    if isinstance(value, ast.Attribute):
        return (
            value.attr in SPAWNS
            and isinstance(value.value, ast.Name)
            and value.value.id == "subprocess"
        )
    return isinstance(value, ast.Name) and value.id in names


def _spawn_names(tree: ast.Module) -> frozenset[str]:
    """The bare names a module calls a spawn of :mod:`subprocess` by.

    The spawns' own names, which a script imports or takes as a parameter
    (``run=subprocess.run``, so that a test can hand it another), and any
    name an import, an assignment or a parameter's default binds to one.
    """
    names = set(SPAWNS)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            names.update(
                alias.asname or alias.name
                for alias in node.names
                if alias.name in SPAWNS
            )
    grew = True
    while grew:
        grew = False
        for node in ast.walk(tree):
            bound: list[str] = []
            if isinstance(node, ast.Assign) and _is_spawn(node.value, names):
                bound = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.arguments):
                positional = [*node.posonlyargs, *node.args]
                pairs = list(
                    zip(
                        positional[len(positional) - len(node.defaults) :],
                        node.defaults,
                        strict=True,
                    )
                )
                pairs += [
                    (arg, default)
                    for arg, default in zip(
                        node.kwonlyargs, node.kw_defaults, strict=True
                    )
                    if default is not None
                ]
                bound = [arg.arg for arg, default in pairs if _is_spawn(default, names)]
            for name in bound:
                if name not in names:
                    names.add(name)
                    grew = True
    return frozenset(names)


def text_spawns_without_encoding(source: str) -> list[int]:
    """The lines of the spawns in *source* that decode text in no named encoding.

    :param source: A module's text.
    :return: One line number per such call, in order.
    """
    tree = ast.parse(source)
    bare = _spawn_names(tree)
    found: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _asks_for_text(node):
            continue
        if any(keyword.arg == "encoding" for keyword in node.keywords):
            continue
        func = node.func
        if (isinstance(func, ast.Attribute) and func.attr in SPAWNS) or (
            isinstance(func, ast.Name) and func.id in bare
        ):
            found.append(node.lineno)
    return sorted(found)


def _enclosing_function(tree: ast.Module, line: int) -> str | None:
    """The name of the innermost function whose body holds *line*."""
    found: tuple[int, str] | None = None
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.lineno <= line <= (node.end_lineno or node.lineno)
            and (found is None or node.lineno > found[0])
        ):
            found = (node.lineno, node.name)
    return None if found is None else found[1]


def test_every_script_names_the_encoding_of_what_a_child_prints() -> None:
    """No spawn under ``scripts/`` leaves the decoding of its output to the locale.

    Each spawn :data:`KEPT` lists is still one to keep, so an entry the code
    no longer needs fails here too instead of excusing a later call.
    """
    offenders: list[str] = []
    kept: set[tuple[str, str | None]] = set()
    for path in sorted(SCRIPTS.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        name = path.relative_to(SCRIPTS.parent).as_posix()
        for line in text_spawns_without_encoding(source):
            where = (name, _enclosing_function(ast.parse(source), line))
            if where in KEPT:
                kept.add(where)
            else:
                offenders.append(f"{name}:{line}")
    assert offenders == []
    assert sorted(kept) == sorted(KEPT), "an entry of KEPT names no spawn left to keep"


@pytest.mark.parametrize(
    "source",
    [
        'subprocess.run(["git", "ls-files", "-z"], capture_output=True, text=True)',
        'subprocess.check_output(["git", "log"], text=True)',
        'subprocess.Popen(["node"], stdout=PIPE, universal_newlines=True)',
        'subprocess.run(["git"], text=flag)',
        'from subprocess import run\nrun(["ffprobe"], capture_output=True, text=True)',
        'from subprocess import check_output as out\nout(["git"], text=True)',
        'def probe(*, runner=subprocess.run):\n    runner(["ffprobe"], text=True)',
        'spawn = subprocess.run\nspawn(["node"], capture_output=True, text=True)',
        'def probe(path, run=None):\n    run(["ffprobe", path], text=True)',
    ],
)
def test_a_spawn_that_decodes_text_in_the_locale_is_found(source: str) -> None:
    """Each form of a text spawn, written without ``encoding``."""
    assert text_spawns_without_encoding(source) == [source.count("\n") + 1]


@pytest.mark.parametrize(
    "source",
    [
        'subprocess.run(["git"], capture_output=True, text=True, encoding="utf-8")',
        'subprocess.run(["git"], capture_output=True, encoding="utf-8")',
        'subprocess.run(["git"], capture_output=True)',
        'subprocess.run(["git"], text=False)',
        'subprocess.check_output(["git"], universal_newlines=None)',
        'other.run(["git"], text=True, encoding="utf-8", errors="replace")',
        "pool.map(job, text=True)",
    ],
)
def test_a_spawn_that_names_its_encoding_or_reads_bytes_passes(source: str) -> None:
    """An encoding named, bytes read and a call that spawns nothing are no offence."""
    assert text_spawns_without_encoding(source) == []
