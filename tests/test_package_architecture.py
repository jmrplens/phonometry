#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Architecture rules for the phonometry package layout (Phase 1 overhaul).

Static (ast-based) enforcement of the dependency policy between the domain
subpackages, plus a fresh-interpreter smoke import per subpackage. The edge
whitelist is the contract from the modularization plan: keep it tight; adding
an edge is an explicit, reviewed decision.
"""

from __future__ import annotations

import ast
import dataclasses
import functools
import re
import subprocess
import sys
from pathlib import Path
from typing import Literal, TypeGuard

import pytest

_SCRIPTS = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_parameter_annotations as cpa
import check_return_overloads as return_overloads
from ast_scan import live_bindings, python_files

SRC = Path(__file__).resolve().parent.parent / "src" / "phonometry"

#: The transverse toolbox every domain is allowed to import: normalized
#: frequency selectivity, general signal analysis, the metrology proper and the
#: state of the medium. One package until 4.0 split it in three; ``fluids``
#: joined because every domain needs a medium and eleven identical edges would
#: have recorded nothing.
TOOLBOX: frozenset[str] = frozenset({"filters", "fluids", "signals", "metrology"})

#: Cross-package edges allowed IN ADDITION to `pkg -> pkg` (internal),
#: `* -> _internal` and `* -> TOOLBOX`. "root" = modules still at the top
#: level of the package (shrinks to the facade set as the migration proceeds).
ALLOWED_EDGES: set[tuple[str, str]] = {
    ("environment", "materials"),  # air_absorption -> ISO 354 helpers
    # the binaural analysis of a soundscape (ISO/TS 12913-3 Table D.1) reports
    # the ISO 532-1 loudness and the ECMA-418-2 tonality, roughness and
    # fluctuation strength of each ear, which the psychoacoustics domain
    # implements; psychoacoustics imports nothing from environment
    ("environment", "psychoacoustics"),
    ("aircraft", "environment"),  # atmospheric absorption reuse
    ("vibration", "hearing"),  # multiple-shock SEXES tables
    # swept-sine distortion reuses the ISO 18233 sweep / Farina
    # inverse-filter machinery of room.impulse_response
    ("electroacoustics", "room"),
    # predicted panel R reuses the plate coincidence frequency (radiation)
    ("building", "vibration"),
    # double-wall cavity fill uses the porous equivalent-fluid model
    ("building", "materials"),
    # the plateau-method prediction reads its three constants per material
    # from the solids catalogue, where Norton & Karczub Table 3.1 is held once
    ("building", "solids"),
    # HVAC plenum and machine enclosures reuse the room constant
    # R = S*alpha/(1 - alpha) of the steady-state room field
    ("noise_control", "room"),
    # an enclosure or a cabin is rated by the ISO 717-1 reference-curve
    # shift, the same procedure the building ratings already implement
    ("noise_control", "building"),
    # the insulation of an enclosure is a difference of two sound powers,
    # so it reuses the A-weighting corrections and the background
    # correction of the sound power measurement methods it cites
    ("noise_control", "emission"),
    # ISO 9295:2015 Annex A is the ISO 9613-1 air absorption written in
    # nepers per metre and evaluated up to 22,4 kHz, so the high-frequency
    # sound power methods read the one implementation of it
    ("emission", "environment"),
    # ISO 8297 Table 3 takes the air absorption of an industrial plant from
    # ISO 3891, whose Annex A (SAE ARP 866A) is transcribed once, in
    # aircraft.atmospheric_absorption; aircraft imports nothing from emission
    ("emission", "aircraft"),
    # the level functions detect io.Signal so a read measurement carries
    # its own fs and calibration; io imports no toolbox code back at
    # module level, so import stays acyclic
    ("signals", "io"),
    # write(bext="loudness") fills the five R128 fields from the
    # library's own BS.1770 implementation (a lazy import inside the
    # writer: reading a file never pays for it)
    ("io", "broadcast"),
    # the filters detect io.Signal for the same reason the level functions
    # do: a read measurement carries its own fs and calibration, and asking
    # the caller to repeat either is asking for a transcription error. Same
    # direction as ("signals", "io"), so the graph stays acyclic
    ("filters", "io"),
    # data qualification runs on the record as read, so it takes the object
    # the reader returns for the same reason
    ("metrology", "io"),
    # the electroacoustic, room and speech measurements read their record
    # from a file too, so they take the object the reader returns and
    # resolve its rate and calibration through the same contract. Same
    # direction as the edges above, so the graph stays acyclic
    ("electroacoustics", "io"),
    ("room", "io"),
    ("speech", "io"),
    ("psychoacoustics", "io"),
    ("underwater", "io"),
    ("emission", "io"),
    ("environment", "io"),
    ("materials", "io"),
    ("building", "io"),
    # the acceleration and force records go through the same contract as the
    # pressure ones, except that they take the exemption: their quantity is
    # not a pressure, so a factor the object carries is never applied
    ("vibration", "io"),
    # the EBU R 128 family reads its rate off the object too. This is the one
    # place the edge goes both ways -- ("io", "broadcast") above -- and it is
    # still not a cycle at import time, because io's side is deferred into the
    # writer, so importing phonometry.io never pulls broadcast in
    ("broadcast", "io"),
    # a simulation writes its run straight to a video through io's encoder
    # pipe and options record (write_fdtd_animation and its elastic twin);
    # the imports are lazy, inside the writers, or under TYPE_CHECKING, but
    # for the remote wire table's (simulation._remote.wire imports io._video
    # at module level, and is itself imported only once a run goes to a
    # node), and io imports nothing from simulation, so the graph stays
    # acyclic
    ("simulation", "io"),
}


def _package_of(path: Path) -> str:
    rel = path.relative_to(SRC)
    return rel.parts[0] if len(rel.parts) > 1 else "root"


def _iter_modules() -> list[Path]:
    return [p for p in SRC.rglob("*.py") if p.name != "__init__.py" or p.parent != SRC]


#: The files of the package that run as scripts outside it, each with the
#: modules of the package it may import by absolute name. The node bootstrap
#: is the one: a node runs it before the package is there (from the node
#: image, or sent inline), so it has no package to be relative to, and once
#: the client has sent the package it imports it from the node's cache by
#: name. Every other file imports the package relatively.
SCRIPT_SELF_IMPORTS: dict[str, frozenset[str]] = {
    "simulation/_remote/bootstrap.py": frozenset(
        {"phonometry", "phonometry.simulation._remote"}
    ),
}


def _is_main_guard(node: ast.stmt) -> bool:
    """Whether *node* is ``if __name__ == "__main__":``."""
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Eq)
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value == "__main__"
    )


def _absolute_self_imports(tree: ast.AST) -> set[str]:
    """The modules of this package *tree* imports by absolute name, in any form.

    ``import phonometry.x``, with or without ``as``, counts as much as
    ``from phonometry.x import y``: either would bypass the relative-import
    rules below.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        else:
            continue
        found.update(
            name
            for name in names
            if name == "phonometry" or name.startswith("phonometry.")
        )
    return found


def _unlisted_self_imports(rel: str, tree: ast.AST) -> set[str]:
    """The absolute self-imports of the file *rel* that its entry does not list."""
    return _absolute_self_imports(tree) - SCRIPT_SELF_IMPORTS.get(rel, frozenset())


def _edges() -> set[tuple[str, str, str]]:
    """(from_pkg, to_pkg, 'file: import') for every relative import in src."""
    out: set[tuple[str, str, str]] = set()
    for path in _iter_modules():
        pkg = _package_of(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        unlisted = _unlisted_self_imports(path.relative_to(SRC).as_posix(), tree)
        if unlisted:
            pytest.fail(
                f"{path.relative_to(SRC)}: absolute self-import "
                f"{', '.join(repr(name) for name in sorted(unlisted))} "
                "(use relative imports)"
            )
        for node in ast.walk(tree):
            # An absolute import is a third-party one here: the package's own
            # were refused above.
            if not isinstance(node, ast.ImportFrom) or node.level == 0:
                continue
            where = f"{path.relative_to(SRC)}: {ast.dump(node)[:60]}"
            out.update((pkg, to_pkg, where) for to_pkg in _reached_packages(path, node))
    return out


def _reached_packages(path: Path, node: ast.ImportFrom) -> set[str]:
    """The top-level packages the relative import *node* in *path* reaches.

    The dots climb from the package the module sits in, at whatever depth:
    ``from .. import fdtd`` in ``simulation/_remote/wire.py`` reaches
    ``simulation``, as ``from ..fdtd import FDTDRun`` does there, while the
    same two dots in ``simulation/fdtd.py`` reach the root package. A name
    imported from the root package itself (``from .. import io`` one
    directory down) is the package it names; a module of the root package,
    or a name that is not a package, is ``"root"``.
    """
    here = path.relative_to(SRC).parent.parts
    anchor = here[: max(len(here) - node.level + 1, 0)]
    target = [*anchor, *(node.module.split(".") if node.module else [])]
    heads = [target[0]] if target else [alias.name for alias in node.names]
    return {head if (SRC / head).is_dir() else "root" for head in heads}


#: Family-to-family edges allowed inside a domain. The subgroups exist to
#: separate audiences, so an import across them is a claim that one audience's
#: work feeds the other's, and it should be written down rather than noticed.
ALLOWED_FAMILY_EDGES: set[tuple[str, str, str]] = {
    # EN 12354 predicts from the ratings the measurement methods define.
    ("building", "prediction", "measurement"),
    # A metadiffuser well is a slit absorber: it reuses the porous air state.
    ("materials", "diffusers", "absorbers"),
    # Every sound quality metric is read off a loudness pattern.
    ("psychoacoustics", "quality", "loudness"),
    # IEC TS 61400-11-2 ends the search for tones at the receptor where the
    # ISO 9613-1 air attenuation over the distance reaches 20 dB.
    ("environment", "assessment", "propagation"),
}


def _family_edges() -> set[tuple[str, str, str, str]]:
    """(domain, from_family, to_family, 'file: import') per crossing import."""
    out: set[tuple[str, str, str, str]] = set()
    for path in SRC.rglob("*.py"):
        rel = path.relative_to(SRC).parts
        if len(rel) < 3 or path.name == "__init__.py":
            continue
        domain, family = rel[0], rel[1]
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.level != 2:
                continue
            target = (node.module or "").split(".")[0]
            if target and target != family and (SRC / domain / target).is_dir():
                out.add((domain, family, target, str(path.relative_to(SRC))))
    return out


def test_family_edges_are_whitelisted() -> None:
    """A subgroup reaching into another one is a decision, not an accident."""
    violations = [
        f"{domain}: {frm} -> {to} ({where})"
        for domain, frm, to, where in _family_edges()
        if (domain, frm, to) not in ALLOWED_FAMILY_EDGES
    ]
    assert not violations, "unlisted family-to-family imports:\n" + "\n".join(
        violations
    )


def test_the_scripts_allowed_an_absolute_self_import_are_scripts_that_make_it() -> None:
    """Each listed file runs as a script and imports by name exactly what it lists.

    A listed import the file no longer makes is a stale entry, and one it
    makes beyond its list is refused like any other.
    """
    for rel, listed in SCRIPT_SELF_IMPORTS.items():
        path = SRC / rel
        assert path.is_file(), f"{rel} is listed but does not exist"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert any(_is_main_guard(node) for node in tree.body), (
            f'{rel} is listed as a script but has no `if __name__ == "__main__":`'
        )
        assert _absolute_self_imports(tree) == listed, rel


def test_an_absolute_self_import_is_refused_unless_the_list_names_it() -> None:
    """The guard sees each way of writing the import, and the list admits nothing else."""
    every_form = ast.parse(
        "import phonometry\n"
        "import phonometry.signals as signals\n"
        "from phonometry import filters\n"
        "from phonometry.simulation._remote import node\n"
        "def later():\n"
        "    import phonometry.io\n"
    )
    names = {
        "phonometry",
        "phonometry.signals",
        "phonometry.simulation._remote",
        "phonometry.io",
    }
    assert _absolute_self_imports(every_form) == names
    # A relative import, or a package whose name only starts the same, is not one.
    assert not _absolute_self_imports(
        ast.parse("from . import node\nfrom .. import io\nimport phonometryx\n")
    )
    # A file the list does not name is allowed none, a module beside the
    # script included; the script is allowed what it lists and nothing more.
    assert _unlisted_self_imports("simulation/_remote/node.py", every_form) == names
    for rel, listed in SCRIPT_SELF_IMPORTS.items():
        assert _unlisted_self_imports(rel, every_form) == names - listed


@pytest.mark.parametrize(
    ("rel", "line", "reached"),
    [
        ("simulation/fdtd.py", "from .compute import Compute", {"simulation"}),
        ("simulation/fdtd.py", "from .._internal import frozen", {"_internal"}),
        ("simulation/fdtd.py", "from .. import io", {"io"}),
        ("simulation/fdtd.py", "from .. import _version", {"root"}),
        ("simulation/_remote/wire.py", "from . import bootstrap", {"simulation"}),
        ("simulation/_remote/wire.py", "from .. import fdtd", {"simulation"}),
        ("simulation/_remote/wire.py", "from ..fdtd import FDTDRun", {"simulation"}),
        (
            "simulation/_remote/wire.py",
            "from ... import io, signals",
            {"io", "signals"},
        ),
        ("simulation/_remote/wire.py", "from ...io import Signal", {"io"}),
        ("simulation/__init__.py", "from .fdtd import FDTDRun", {"simulation"}),
    ],
)
def test_a_relative_import_reaches_the_package_its_dots_climb_to(
    rel: str, line: str, reached: set[str]
) -> None:
    """The dots of a relative import are counted from where the module sits."""
    node = ast.parse(line).body[0]
    assert isinstance(node, ast.ImportFrom)
    assert _reached_packages(SRC / rel, node) == reached


def test_internal_imports_no_domain_code() -> None:
    for frm, to, where in _edges():
        if frm == "_internal":
            assert to == "_internal", f"_internal must stay leaf-level: {where}"


def test_cross_package_edges_are_whitelisted() -> None:
    violations = []
    for frm, to, where in _edges():
        if (
            frm == to
            or to in ("_internal", "root")
            or frm in ("root", "_plot", "_report")
        ):
            # root modules are unrestricted during the migration; the facade
            # (__init__) legitimately imports everything. _plot and
            # _report are rendering leaves that reference domain classes only
            # under TYPE_CHECKING (see the guarantee test below).
            continue
        if to in TOOLBOX:
            continue
        if to in ("_plot", "_report"):
            # lazy .plot()/.report() imports only; enforced structurally by the
            # fact that _plot/_report modules import domain classes under
            # TYPE_CHECKING.
            continue
        if (frm, to) not in ALLOWED_EDGES:
            violations.append(f"{frm} -> {to} ({where})")
    assert not violations, "unlisted cross-package imports:\n" + "\n".join(violations)


def test_render_modules_only_type_check_domain_imports() -> None:
    """A rendering leaf must not reach domain code at module level.

    ``rglob``, not ``glob``: the rendering trees grew subpackages, and a
    non-recursive scan left every module inside them outside this gate.

    How many dots escape the tree depends on how deep the module sits, so the
    threshold is measured rather than fixed at ``level == 2``. For
    ``_plot/common.py`` one dot is ``_plot`` and two reach the package root;
    for ``_plot/geometry/emission.py`` two dots are still ``_plot`` and it
    takes three. An import escapes when its level exceeds the module's own
    depth below the rendering root.

    ``_internal`` is not domain code and is exempt. Counting dots is a proxy
    for "reaches the domain", and it is the right proxy for every package but
    this one: the eight modules under ``_internal`` import numpy, scipy and the
    standard library and **nothing from this package at all**, so importing one
    can no more drag a domain module into a rendering leaf than importing numpy
    can. Without the exemption the shared guards would have to be imported
    inside every function that validates an argument, which is a worse file for
    a rule that was never about them.
    """
    exempt = "_internal"
    checked = False
    for sub in ("_plot", "_report"):
        render_dir = SRC / sub
        if not render_dir.is_dir():
            continue
        checked = True
        for path in sorted(render_dir.rglob("*.py")):
            depth = len(path.relative_to(render_dir).parts)
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:  # module level only
                if not isinstance(node, ast.ImportFrom) or node.level <= depth:
                    continue
                if (node.module or "").split(".")[0] == exempt:
                    continue
                pytest.fail(
                    f"{path.relative_to(SRC)}:{node.lineno}: module-level "
                    f"import of domain code '{'.' * node.level}"
                    f"{node.module or ''}' (must live under TYPE_CHECKING)"
                )
    if not checked:
        pytest.skip("neither _plot nor _report created yet")


@pytest.mark.parametrize(
    "pkg",
    sorted(p.name for p in SRC.iterdir() if p.is_dir() and not p.name.startswith("__")),
)
def test_subpackage_imports_in_fresh_interpreter(pkg: str) -> None:
    subprocess.run(
        [sys.executable, "-c", f"import phonometry.{pkg}"],
        check=True,
        capture_output=True,
        timeout=120,
    )


def test_subpackage_reexports_cover_facade_imports() -> None:
    """Every name the facade imports from a domain submodule must also be
    reachable on the subpackage namespace (the ``env.name`` usage pattern).

    The check is on the top-level package of the import, at whatever depth the
    module sits: ``from .vibration.human.exposure import daily_exposure`` has
    to leave ``vibration.daily_exposure`` reachable.
    """
    import importlib

    facade = ast.parse((SRC / "__init__.py").read_text(encoding="utf-8"))
    missing: list[str] = []
    for node in facade.body:
        if not isinstance(node, ast.ImportFrom) or node.level != 1 or not node.module:
            continue
        parts = node.module.split(".")
        # A domain module is ``<pkg>.<module>`` or, since the domains grew a
        # second level, ``<pkg>.<family>.<module>``. Checking only the
        # two-part form silently stopped covering a domain the day it grew.
        if len(parts) < 2 or parts[0].startswith("_"):
            continue
        pkg = importlib.import_module(f"phonometry.{parts[0]}")
        missing.extend(
            f"phonometry.{parts[0]}.{alias.name}"
            for alias in node.names
            if not hasattr(pkg, alias.name)
        )
    assert not missing, (
        "facade imports not re-exported by their subpackage:\n" + "\n".join(missing)
    )


def _orphan_code_directories(src: Path) -> list[str]:
    """The directories under *src* that hold a module but no ``__init__.py``.

    A module is what Python could import: a hidden file (macOS writes ``._``
    files beside every file it copies to a foreign disk) or a directory with a
    dot in its name cannot be, and setuptools leaves both out of the wheel.
    """
    holding = {
        path.parent
        for path in src.rglob("*.py")
        if not path.name.startswith(".")
        and not any("." in part for part in path.parent.relative_to(src).parts)
    }
    return sorted(
        directory.relative_to(src.parent).as_posix()
        for directory in holding
        if not (directory / "__init__.py").is_file()
    )


def test_every_directory_of_code_is_a_package() -> None:
    """A directory that holds a module holds an ``__init__.py`` too.

    Without one, Python imports the directory here as a namespace package and
    every test passes; but the wheel takes only directories with an
    ``__init__.py`` (``namespaces = false`` in ``pyproject.toml``), so the
    code is in no wheel, and the package a client ships to a node leaves it
    out as well.
    """
    orphans = _orphan_code_directories(SRC)
    assert not orphans, (
        "a directory of modules without an __init__.py imports here as a "
        "namespace package, but is in no wheel and on no node; add the "
        "__init__.py: " + ", ".join(orphans)
    )


def test_collected_test_modules_have_unique_import_names() -> None:
    """Two test modules that import under one name break the whole collection.

    With the default import mode pytest names a module by walking up from the
    file while ``__init__.py`` exists: a file inside a package keeps its dotted
    path, and a file outside one is imported by its bare basename. No folder
    that holds a test file has an ``__init__.py``, so every test file competes
    for its basename, and a second ``test_spain.py`` anywhere is an import
    mismatch that only shows up when the whole tree is collected at once.
    Renaming test files to follow their modules, which is what the taxonomy
    work does, is exactly how the collision gets introduced.

    ``src`` is scanned too, because pytest collects from the repository root
    and a module named ``test_*.py`` there would match the default patterns.
    It would sit inside a package, so it would import under its dotted name
    and could not collide, and this check knows that rather than assuming it.
    """
    import collections

    root = Path(__file__).resolve().parent.parent

    def import_name(path: Path) -> str:
        parts = [path.stem]
        parent = path.parent
        while (parent / "__init__.py").exists():
            parts.append(parent.name)
            parent = parent.parent
        return ".".join(reversed(parts))

    collected = [
        path
        for directory in ("tests", "src")
        for pattern in ("test_*.py", "*_test.py")
        for path in (root / directory).rglob(pattern)
    ]
    counts = collections.Counter(import_name(path) for path in collected)
    duplicates = {name: count for name, count in counts.items() if count > 1}
    assert not duplicates, f"test modules sharing an import name: {duplicates}"


def test_sonar_configuration_names_files_that_exist() -> None:
    """A path-keyed analyzer exemption is silently lost when the file moves.

    There are no exemptions at present: the parameter counts that motivated
    them were fixed by grouping the parameters instead, so nothing is hidden
    from the analyzer. An empty configuration therefore passes. What must never
    happen again is an entry left pointing at a path the taxonomy work moved,
    which is what this checks the moment one is added back.
    """
    import re

    root = Path(__file__).resolve().parent.parent
    config = (root / "sonar-project.properties").read_text(encoding="utf-8")
    keyed = re.findall(r"resourceKey=(\S+)", config)
    excluded = [
        path
        for line in re.findall(r"^sonar\.cpd\.exclusions=(\S+)$", config, re.MULTILINE)
        for path in line.split(",")
    ]
    missing = [path for path in keyed + excluded if not (root / path).exists()]
    assert not missing, f"sonar-project.properties names missing files: {missing}"


#: The names the top level holds itself, because they belong to no single
#: domain. Everything else it publishes is a domain package, and every function
#: and class lives in the package that owns it. ``Signal`` is the one name in
#: both places: ``phonometry.io`` owns it and the top level re-exports it,
#: because it is the type every package that takes measured audio accepts.
ROOT_ONLY: frozenset[str] = frozenset(
    {
        "PhonometryWarning",
        "ReportMetadata",
        "Signal",
        "__version__",
    }
)


def test_every_public_name_is_reachable_from_its_domain() -> None:
    """A name published only by the root is a name with no documented home.

    ``plot_excitation`` was one: it lives in the private ``_plot.room``, the
    root re-exported it, and ``phonometry.room`` did not, so the twenty-third
    of the twenty-four geometry plots was reachable through the flat shortcut
    and through no module path at all. A reader following the domain, which is
    how the documentation teaches the library, could not find it.
    """
    import inspect

    import phonometry

    domains = {
        name
        for name in dir(phonometry)
        if not name.startswith("_") and inspect.ismodule(getattr(phonometry, name))
    }
    published: dict[str, list[str]] = {}
    for domain in sorted(domains):
        for name in getattr(getattr(phonometry, domain), "__all__", ()):
            published.setdefault(name, []).append(domain)

    orphans = sorted(set(phonometry.__all__) - set(published) - ROOT_ONLY - domains)
    assert not orphans, (
        "public names the root publishes and no domain package does: "
        f"{orphans}. Export each from the package that owns it, or add it to "
        "ROOT_ONLY if it genuinely belongs to no domain."
    )


def test_no_docstring_documents_a_parameter_that_is_gone() -> None:
    """A `:param` for an argument the signature no longer has is a lie.

    Converting the visco-thermal models to take a `Fluid` left twenty-five of
    these behind: `johnson_champoux_allard` alone still documented six floats
    it no longer accepts, so a reader following its own docstring got a
    `TypeError`. Nothing caught it, because a docstring is prose to every gate
    the repository has, and the generated reference tables are built from the
    signature rather than from the text beside it, so the two drifted apart
    without either looking wrong on its own.
    """
    import ast
    import pathlib

    stale: list[str] = []
    for path in sorted(pathlib.Path("src/phonometry").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            doc = ast.get_docstring(node) or ""
            if not doc:
                continue
            named = {
                a.arg
                for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            }
            if node.args.vararg is not None:
                named.add(node.args.vararg.arg)
            if node.args.kwarg is not None:
                named.add(node.args.kwarg.arg)
            for line in doc.split("\n"):
                text = line.strip()
                if not text.startswith(":param "):
                    continue
                name = text[len(":param ") :].split(":")[0].strip()
                if name in named:
                    continue
                # A varargs docstring names the collection it documents rather
                # than the parameter: `:param fields:` for `*field`. Only that
                # one name is excused, not every name in a variadic function.
                if node.args.vararg is not None and name.rstrip("s") == (
                    node.args.vararg.arg.rstrip("s")
                ):
                    continue
                stale.append(
                    f"{path.relative_to('src')}:{node.lineno} {node.name} "
                    f"documents ':param {name}:', which it does not take"
                )

    assert not stale, (
        "docstrings naming parameters the signature does not have:\n  "
        + "\n  ".join(stale)
    )


#: The floats a `Fluid` withdrew from the signatures that used to take them
#: one by one. A curated row still naming one of these describes an API that
#: is gone; every other word in a row is prose and stays out of the check.
WITHDRAWN_FLUID_FLOATS = frozenset(
    {
        "air",
        "air_density",
        "atmospheric_pressure_pa",
        "density",
        "heat_capacity_ratio",
        "prandtl_number",
        "specific_heat_capacity",
        "specific_heat_ratio",
        "speed_of_sound",
        "static_pressure_pa",
        "temperature_c",
        "thermal_conductivity",
        "viscosity",
    }
)


def test_no_curated_row_offers_a_fluid_float_that_is_gone() -> None:
    """The other half of the gate on the curated table.

    ``check_api_reference.py`` asks that every public name have a row. It does
    not ask that a row describe the signature it names, so the ten rows the
    fluid conversion left behind kept offering `speed_of_sound` and
    `air_density` to functions that take a `Fluid`, and the table read as
    current while documenting an API that raises `TypeError`. The vocabulary
    is closed to the floats a `Fluid` replaced, so a name is flagged only where
    the signature really has no such argument.
    """
    import inspect
    import pathlib
    import re

    import phonometry

    published: dict[str, object] = {}
    for domain in sorted(dir(phonometry)):
        if domain.startswith("_"):
            continue
        package = getattr(phonometry, domain)
        if not inspect.ismodule(package):
            continue
        for name in getattr(package, "__all__", ()):
            published.setdefault(name, getattr(package, name, None))

    row = re.compile(r"^\|\s*`([A-Za-z_][\w.]*)`\s*\|\s*`function`\s*\|(.*)\|\s*$")
    index = pathlib.Path("docs/reference/api/index.md")
    stale: list[str] = []
    for number, line in enumerate(index.read_text(encoding="utf-8").splitlines(), 1):
        match = row.match(line)
        if match is None:
            continue
        name, body = match.group(1), match.group(2)
        function = published.get(name)
        if not callable(function):
            continue
        try:
            accepted = set(inspect.signature(function).parameters)
        except (TypeError, ValueError):  # pragma: no cover - builtins only
            continue
        cited = set(re.findall(r"`([a-z_]\w*)`", body.split("|")[0]))
        stale.extend(
            f"{index}:{number} {name} offers '{gone}'"
            for gone in sorted(cited & WITHDRAWN_FLUID_FLOATS - accepted)
        )

    assert not stale, (
        "curated rows offering an argument the signature does not take:\n  "
        + "\n  ".join(stale)
    )


def test_no_docstring_breaks_its_own_field_list() -> None:
    """Prose between two `:param:` lines ends the field list where it sits.

    Sphinx and every reader built on it stop the list at the first line that is
    not a field or its continuation, so the parameters after the break vanish
    from the generated table and the prose is printed after **Returns**. Two
    docstrings did it: `unlined_rectangular_duct_attenuation`, where a
    paragraph about the second model swallowed `:param wrapped:`, and
    `require_summary_class`, where two sentences sat between `:param field:`
    and `:raises:`. Neither looked wrong in the source, which is why this reads
    the shape rather than the words.
    """
    import ast
    import pathlib

    fields = (":param", ":return", ":raises", ":ivar", ":type", ":rtype", ":vartype")
    broken: list[str] = []
    for path in sorted(pathlib.Path("src/phonometry").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            lines = (ast.get_docstring(node) or "").split("\n")
            marked = [i for i, line in enumerate(lines) if line.startswith(fields)]
            if len(marked) < 2:
                continue
            for index in range(marked[0], marked[-1]):
                line = lines[index]
                if line and not line.startswith((*fields, " ", "\t")):
                    broken.append(
                        f"{path.relative_to('src')}:{node.lineno} {node.name} "
                        f"breaks its field list at {line[:50]!r}"
                    )
                    break

    assert not broken, "docstrings with prose inside the field list:\n  " + "\n  ".join(
        broken
    )


#: A field marker at the start of a docstring line.
_FIELD_MARKERS = (
    ":param",
    ":return",
    ":raises",
    ":warns",
    ":ivar",
    ":type",
    ":rtype",
    ":vartype",
)

#: A sentence of a field that is nothing but a cross-reference: the tail of a
#: sentence another field, or a clause written into it, cut off.
_LONE_REFERENCE = re.compile(r"(?:^|[.!?]\s+)(:\w+:`[^`]+`)\.(?:\s|$)")


def _field_texts(docstring: str) -> list[str]:
    """Each field of a docstring's field list, its continuation lines joined."""
    texts: list[list[str]] = []
    current: list[str] | None = None
    for line in docstring.split("\n"):
        if line.startswith(_FIELD_MARKERS):
            current = [line.strip()]
            texts.append(current)
        elif current is not None and line.startswith((" ", "\t")):
            current.append(line.strip())
        else:
            current = None
    return [" ".join(text) for text in texts]


def _split_fields(source: str) -> list[str]:
    """The fields of *source*'s docstrings another field or clause cut in two."""
    return [
        f"{node.lineno} {node.name}: ...{text[-70:]!r}"
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        for text in _field_texts(ast.get_docstring(node) or "")
        if text[-1:].isalnum() or text[-1:] in ",;" or _LONE_REFERENCE.search(text)
    ]


def test_no_docstring_field_is_cut_in_two() -> None:
    """A field written into the middle of another field's sentence cuts it.

    `weighting_filter` once read ``:return: ... a bare array back; a`` with
    ``:raises TypeError:`` on the next line and the rest of the return text
    under it, and `duct_path` once wrote ``criterion`` into the first line of
    a ``:raises TypeError:`` whose sentence went on below, leaving
    ``:class:`DuctElement`.`` as a sentence of its own. The page then ends the
    return text mid-sentence and prints it inside the exception. A field
    whose text stops on a word or a comma, or holds a sentence that is only a
    cross-reference, is cut in two.
    """
    cut = [
        f"{path.relative_to('src')}:{finding}"
        for path in sorted(Path("src/phonometry").rglob("*.py"))
        for finding in _split_fields(path.read_text(encoding="utf-8"))
    ]
    assert not cut, "docstring fields cut in two:\n  " + "\n  ".join(cut)


def test_a_field_cut_in_two_is_found() -> None:
    """Both ways a field was cut are read, and a whole field list is not."""
    cut_return = '''
def f(x):
    """Weight a signal.

    :return: The weighted record. A bare array gives an array back; a
    :raises TypeError: if ``x`` is not a text.
        :class:`Signal` gives a Signal.
    """
'''
    cut_raises = '''
def g(elements, criterion):
    """Route a duct path.

    :raises TypeError: If an entry of ``elements`` is not a, or ``criterion`` is not a
        text.
        :class:`DuctElement`.
    """
'''
    whole = '''
def h(elements, criterion):
    """Route a duct path.

    :return: The weighted record. A bare array gives an array back; a
        :class:`Signal` gives a Signal.
    :raises TypeError: If an entry of ``elements`` is not a
        :class:`DuctElement`, or ``criterion`` is not a text.
    """
'''
    assert len(_split_fields(cut_return)) == 1
    assert len(_split_fields(cut_raises)) == 1
    assert _split_fields(whole) == []


def test_every_warning_a_package_can_raise_is_published() -> None:
    """A warning you cannot name is a warning you cannot filter.

    ``HVACWarning`` fires whenever a relative efficiency lands below the 50 %
    floor Long Table 13.6 is tabulated from, which is the deliberate case as
    well as the mistaken one, and ``phonometry.noise_control`` did not publish
    it while publishing its sibling ``PlaneWaveWarning``. A caller could see it
    and could not write the ``filterwarnings`` rule for it; only the blanket
    ``PhonometryWarning`` rule reached it, which silences twenty-six others too.
    """
    import importlib
    import inspect
    import pkgutil

    import phonometry

    unpublished: list[str] = []
    for domain in sorted(
        name
        for name in dir(phonometry)
        if not name.startswith("_") and inspect.ismodule(getattr(phonometry, name))
    ):
        package = getattr(phonometry, domain)
        exported = set(getattr(package, "__all__", ()))
        for _, modname, _ in pkgutil.walk_packages(
            getattr(package, "__path__", []), prefix=f"phonometry.{domain}."
        ):
            if "._" in modname:
                continue
            try:
                module = importlib.import_module(modname)
            # An optional dependency is absent
            except Exception:
                continue
            for name, obj in vars(module).items():
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Warning)
                    and obj.__module__ == modname
                    and not name.startswith("_")
                    and name not in exported
                ):
                    unpublished.append(f"phonometry.{domain} does not publish {name}")

    assert not unpublished, (
        "warning classes a package can raise but does not publish:\n  "
        + "\n  ".join(sorted(set(unpublished)))
        + "\nExport each, so a caller can filter it by name."
    )


def test_a_published_field_type_is_published_too() -> None:
    """A type you can receive but cannot name is a type you cannot use.

    ``TrackMeasure`` and ``RailJoints`` were two of the six digits of the
    CNOSSOS-EU track descriptor. ``TrackDescriptor`` declared both as fields and
    ``from_code`` handed them back, so a caller held a ``TrackMeasure`` it had
    no supported way to import: the other four digits were published and these
    two were not. The round-trip test had the same gap, asserting digits 1, 2, 3
    and 6 and skipping the two it could not name either.

    The annotations are resolved, not skipped when they will not resolve: the
    modules import ``Mapping``, ``NDArray`` and the other names an annotation
    uses for the type checker only, so they are supplied, together with every
    published name, and an annotation that still does not resolve fails the
    test. Catching the failure and moving on had left 177 of the 494
    published dataclasses unchecked, every catalogue row among them, so a
    field typed with a type nobody publishes could not have been seen.
    """
    import collections.abc
    import dataclasses
    import inspect
    import numbers
    import typing

    from numpy.typing import ArrayLike, NDArray

    import phonometry
    from phonometry._internal.types import BandFraction, WindowSpec

    domains = {
        name
        for name in dir(phonometry)
        if not name.startswith("_") and inspect.ismodule(getattr(phonometry, name))
    }
    published = {
        name: getattr(getattr(phonometry, domain), name)
        for domain in domains
        for name in getattr(getattr(phonometry, domain), "__all__", ())
    }
    localns: dict[str, object] = {
        **published,
        "Callable": collections.abc.Callable,
        "Hashable": collections.abc.Hashable,
        "Iterable": collections.abc.Iterable,
        "Iterator": collections.abc.Iterator,
        "Mapping": collections.abc.Mapping,
        "Sequence": collections.abc.Sequence,
        "ArrayLike": ArrayLike,
        "NDArray": NDArray,
        "Real": numbers.Real,
        "BandFraction": BandFraction,
        "WindowSpec": WindowSpec,
    }

    def parts(annotation: object) -> typing.Iterator[object]:
        yield annotation
        for argument in typing.get_args(annotation):
            yield from parts(argument)

    unresolved: list[str] = []
    unreachable: list[str] = []
    for domain in sorted(domains):
        package = getattr(phonometry, domain)
        for owner in getattr(package, "__all__", ()):
            obj = getattr(package, owner, None)
            if not dataclasses.is_dataclass(obj):
                continue
            # A published instance (``DEFAULT_EXPANDER``) is read through its
            # class: an instance carries no module globals, so its annotations
            # could only resolve from ``localns``.
            record = obj if isinstance(obj, type) else type(obj)
            try:
                hints = typing.get_type_hints(record, localns=localns)
            except NameError as error:
                unresolved.append(f"phonometry.{domain}.{owner}: {error}")
                continue
            for field, annotation in hints.items():
                if field.startswith("_"):
                    continue
                for part in parts(annotation):
                    if not inspect.isclass(part):
                        continue
                    module = getattr(part, "__module__", "")
                    if not module.startswith("phonometry."):
                        continue
                    if part.__name__ in published:
                        continue
                    unreachable.append(
                        f"phonometry.{domain}.{owner}.{field} is a "
                        f"{part.__name__}, defined in {module}"
                    )

    assert not unresolved, (
        "published dataclasses whose annotations do not resolve:\n  "
        + "\n  ".join(sorted(unresolved))
        + "\nSupply the missing name here, or import it where it is used."
    )
    assert not unreachable, (
        "types a published dataclass exposes but no package publishes:\n  "
        + "\n  ".join(sorted(set(unreachable)))
        + "\nExport each from the package that owns the dataclass."
    )


def test_no_public_name_is_published_by_two_domains() -> None:
    """One name, one owner: what makes the flat root a shortcut and not a map.

    Two domains exporting the same spelling is what forces a rename at the
    root (see ``environmental_expanded_uncertainty``), and it is what would
    make ``from phonometry import <domain>`` ambiguous about which module a
    call reaches.
    """
    import inspect

    import phonometry

    published: dict[str, list[str]] = {}
    for domain in sorted(
        name
        for name in dir(phonometry)
        if not name.startswith("_") and inspect.ismodule(getattr(phonometry, name))
    ):
        for name in getattr(getattr(phonometry, domain), "__all__", ()):
            published.setdefault(name, []).append(domain)

    shared = {name: owners for name, owners in published.items() if len(owners) > 1}
    assert not shared, f"names published by more than one domain: {shared}"


def _message_text(node: ast.Assign) -> str | None:
    """The literal text of a ``msg = ...`` assignment, or ``None``.

    Refusals are written as one assignment and raised on the next line, and
    most of them are parenthesised over several lines, which the parser has
    already folded into a single constant. An f-string keeps only its literal
    runs: what an interpolation puts there is not visible statically.
    """
    if len(node.targets) != 1:
        return None
    target = node.targets[0]
    if not isinstance(target, ast.Name) or target.id != "msg":
        return None
    value = node.value
    if isinstance(value, ast.Constant):
        return value.value if isinstance(value.value, str) else None
    if isinstance(value, ast.JoinedStr):
        return "".join(
            part.value
            for part in value.values
            if isinstance(part, ast.Constant) and isinstance(part.value, str)
        )
    return None


#: The modules whose float constants are spelled by name.
_FLOAT_CONSTANT_OWNERS = frozenset({"np", "numpy", "math"})

#: The modules whose float constants are spelled by name, as imported.
_FLOAT_CONSTANT_MODULES = frozenset({"numpy", "math"})

#: Their float constants: a comparison with one is a comparison with a float
#: literal written out by name, ``x == np.inf`` as much as ``x == 1e308``.
_FLOAT_CONSTANT_NAMES = frozenset(
    {
        "inf",
        "nan",
        "pi",
        "e",
        "tau",
        "euler_gamma",
        "Inf",
        "Infinity",
        "NAN",
        "NaN",
        "NINF",
        "PINF",
        "infty",
    }
)


def _is_float_constant(node: ast.expr, names: _ScopeNames | None = None) -> bool:
    """Whether *node* is a float literal, signed, named or spelled ``float("inf")``.

    Named by numpy or ``math`` (``np.inf``, ``math.pi``), through a name
    that may hold the module where it is read (``import math as m``, then
    ``m.pi``), or by a name that may hold one of their constants there
    (``from math import pi``), as *names*, the scope it is read in, has it.
    """
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        node = node.operand
    if isinstance(node, ast.Constant):
        return isinstance(node.value, float)
    if isinstance(node, ast.Name):
        return names is not None and names.may_hold(node, "constant")
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        owner = node.value
        return node.attr in _FLOAT_CONSTANT_NAMES and (
            owner.id in _FLOAT_CONSTANT_OWNERS
            or (names is not None and names.may_hold(owner, "owner"))
        )
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "float"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    )


#: How a dtype argument spells ``bool``: the builtin, numpy's names for it,
#: and the strings numpy reads as it.
_BOOL_DTYPE_NAMES = frozenset({"bool", "bool_", "bool8", "?", "b1"})

#: The byte-order marks numpy reads before a dtype string, ``"|b1"`` or
#: ``"=?"``, which change nothing for a boolean.
_BYTE_ORDER_MARKS = "|=<>"


#: The comprehensions, each a scope of its own for the variables it loops over.
_COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)

#: The scopes that run when called, not where they are written.
_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)

#: The nodes that open a scope of their own for the names bound in them.
_NESTED_SCOPES = (
    ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef, *_COMPREHENSIONS,
)  # fmt: skip

_Comprehension = ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp

_Scope = (
    ast.Module
    | ast.FunctionDef
    | ast.AsyncFunctionDef
    | ast.Lambda
    | ast.ClassDef
    | _Comprehension
)


def _parameters(arguments: ast.arguments) -> list[ast.arg]:
    """Every parameter of a function, positional, keyword-only and starred."""
    starred = [arguments.vararg, arguments.kwarg]
    return [
        *arguments.posonlyargs,
        *arguments.args,
        *arguments.kwonlyargs,
        *(parameter for parameter in starred if parameter is not None),
    ]


def _type_parameters(scope: ast.AST) -> set[str]:
    """The type parameters a generic function or class declares, ``def f[T]``."""
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {
            parameter.name
            for parameter in scope.type_params
            if isinstance(parameter, (ast.TypeVar, ast.ParamSpec, ast.TypeVarTuple))
        }
    return set()


def _outer_parts(scope: ast.AST) -> list[ast.AST]:
    """The parts of a nested *scope* that Python evaluates in the scope around it.

    A class's decorators, bases and keywords, a function's decorators,
    defaults and annotations, and a comprehension's first iterable.
    """
    if isinstance(scope, _COMPREHENSIONS):
        return [scope.generators[0].iter]
    if isinstance(scope, ast.ClassDef):
        return [*scope.decorator_list, *scope.bases, *scope.keywords]
    if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        return []
    arguments = scope.args
    defaults: list[ast.AST] = [*arguments.defaults]
    defaults.extend(default for default in arguments.kw_defaults if default)
    if isinstance(scope, ast.Lambda):
        return defaults
    annotations = [p.annotation for p in _parameters(arguments) if p.annotation]
    returns = [scope.returns] if scope.returns else []
    return [*scope.decorator_list, *defaults, *annotations, *returns]


def _scope_body(scope: _Scope) -> list[ast.AST]:
    """The statements, or the expressions, that run in *scope* itself.

    A lambda's expression; a comprehension's result, its loop variables, its
    conditions and every iterable after the first.
    """
    if isinstance(scope, ast.Lambda):
        return [scope.body]
    if isinstance(scope, _COMPREHENSIONS):
        generators = scope.generators
        results: list[ast.AST] = (
            [scope.key, scope.value] if isinstance(scope, ast.DictComp) else [scope.elt]
        )
        return [
            *results,
            *(generator.target for generator in generators),
            *(condition for generator in generators for condition in generator.ifs),
            *(generator.iter for generator in generators[1:]),
        ]
    return list(scope.body)


def _own_nodes(scope: _Scope) -> tuple[list[ast.AST], list[_Scope]]:
    """The nodes that run in *scope*, in the order of the source, and the scopes nested directly in it.

    A nested function's, class's or comprehension's body is its own scope's;
    its decorators, defaults, annotations, bases or first iterable run here.
    """
    own: list[ast.AST] = []
    nested: list[_Scope] = []
    pending = _scope_body(scope)[::-1]
    while pending:
        node = pending.pop()
        own.append(node)
        if isinstance(node, _NESTED_SCOPES):
            nested.append(node)
            pending.extend(_outer_parts(node)[::-1])
        else:
            pending.extend(list(ast.iter_child_nodes(node))[::-1])
    return own, nested


def _walrus_targets(comprehension: _Comprehension) -> set[str]:
    """The names a ``:=`` in *comprehension* binds, which belong to the scope around it.

    Read through the comprehensions nested in it, which hand theirs on the
    same way, and not into a function, class or lambda nested there.
    """
    names: set[str] = set()
    pending = list(ast.iter_child_nodes(comprehension))
    while pending:
        node = pending.pop()
        if isinstance(node, ast.NamedExpr):
            names.add(node.target.id)
        if isinstance(node, _COMPREHENSIONS) or not isinstance(node, _NESTED_SCOPES):
            pending.extend(ast.iter_child_nodes(node))
    return names


#: What the reader follows a name to: numpy's boolean, a float constant of
#: numpy or ``math``, or one of those modules.
_Kind = Literal["bool", "constant", "owner"]

#: One binding of a name: the node that binds it, and what it binds the name
#: to, ``None`` for anything the reader does not follow.
_Binding = tuple[ast.AST, _Kind | None]


def _imported_kind(node: ast.ImportFrom, name: str) -> _Kind | None:
    """What ``from <module> import <name>`` binds: numpy's boolean, a float constant, or neither."""
    if node.level != 0:
        return None
    if node.module in {"numpy", "np"} and name in _BOOL_DTYPE_NAMES:
        return "bool"
    if node.module in _FLOAT_CONSTANT_MODULES and name in _FLOAT_CONSTANT_NAMES:
        return "constant"
    return None


def _import_kinds(node: ast.Import | ast.ImportFrom) -> list[tuple[str, _Kind | None]]:
    """Each name *node* binds, with what it binds the name to.

    ``import numpy as n`` and ``import math.x`` bind the module itself, an
    owner of float constants; a star import binds no name the reader sees.
    """
    if isinstance(node, ast.ImportFrom):
        return [
            (alias.asname or alias.name, _imported_kind(node, alias.name))
            for alias in node.names
            if alias.name != "*"
        ]
    found: list[tuple[str, _Kind | None]] = []
    for alias in node.names:
        bound = alias.asname or alias.name.partition(".")[0]
        module = alias.name if alias.asname else bound
        found.append((bound, "owner" if module in _FLOAT_CONSTANT_MODULES else None))
    return found


def _statement_bindings(
    own: list[ast.AST],
) -> tuple[dict[str, list[_Binding]], set[str], set[str]]:
    """Each name the statements among *own* bind, with every binding of it, and the names declared ``global`` and ``nonlocal``.

    An assignment, a ``del``, a loop, ``with``, ``except`` or ``match`` name,
    a ``def`` or a ``class``, an import, and a ``:=`` in a comprehension,
    which binds in the scope around the comprehension.
    """
    flow: dict[str, list[_Binding]] = {}
    declared_global: set[str] = set()
    declared_nonlocal: set[str] = set()
    for node in own:
        bound: list[tuple[str, _Kind | None]] = []
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            bound.append((node.id, None))
        elif isinstance(node, _COMPREHENSIONS):
            bound.extend((name, None) for name in _walrus_targets(node))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            bound.extend(_import_kinds(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.append((node.name, None))
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)):
            bound.extend([(node.name, None)] if node.name else [])
        elif isinstance(node, ast.MatchMapping) and node.rest:
            bound.append((node.rest, None))
        elif isinstance(node, ast.Global):
            declared_global.update(node.names)
        elif isinstance(node, ast.Nonlocal):
            declared_nonlocal.update(node.names)
        for name, kind in bound:
            flow.setdefault(name, []).append((node, kind))
    return flow, declared_global, declared_nonlocal


def _expression_names(
    scope: ast.Lambda | _Comprehension, own: list[ast.AST]
) -> set[str]:
    """The names a lambda or a comprehension binds for the whole of its run.

    A lambda's parameters and the names a ``:=`` in it binds, there or in a
    comprehension of it; a comprehension's loop variables alone, its ``:=``
    binding in the scope around it.
    """
    if isinstance(scope, _COMPREHENSIONS):
        return {
            name.id
            for generator in scope.generators
            for name in ast.walk(generator.target)
            if isinstance(name, ast.Name)
        }
    names = {parameter.arg for parameter in _parameters(scope.args)}
    for node in own:
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, _COMPREHENSIONS):
            names.update(_walrus_targets(node))
    return names


@dataclasses.dataclass(eq=False)
class _ScopeNames:
    """What one scope binds of the names the reader follows, and where it reads the rest.

    A read takes the binding Python gives the name where it is read
    (:meth:`may_hold`).
    """

    #: The scope.
    scope: _Scope
    #: The module the scope is written in, whose blocks place each binding.
    tree: ast.Module
    #: Each name the scope's statements bind, with every binding of it.
    flow: dict[str, list[_Binding]]
    #: The names it binds for the whole of its run: a function's parameters
    #: and type parameters, a generic class's, a comprehension's loop
    #: variables, a lambda's parameters.
    entry: frozenset[str]
    #: The names it declares ``global``, which are the module's.
    declared_global: frozenset[str]
    #: The names it declares ``nonlocal``, which are a function's around it.
    declared_nonlocal: frozenset[str]
    #: The scope it reads a name it does not bind from: the function or the
    #: module around it, past any class body.
    outer: _ScopeNames | None
    #: Where in *outer* it reads it: the class or the comprehension that runs
    #: there, or ``None`` for a function or a lambda, which reads the name as
    #: it stands once *outer* has run.
    at: ast.AST | None
    #: What the scopes nested in it bind its names to through ``global`` or
    #: ``nonlocal``, whenever they run.
    from_inside: dict[str, set[_Kind]] = dataclasses.field(default_factory=dict)

    def binds(self, name: str) -> bool:
        """Whether *name* is the scope's own, bound in it and declared neither ``global`` nor ``nonlocal``."""
        declared = name in self.declared_global or name in self.declared_nonlocal
        return not declared and (name in self.flow or name in self.entry)

    def module(self) -> _ScopeNames:
        """The module's names, which a name declared ``global`` reads."""
        names = self
        while names.outer is not None:
            names = names.outer
        return names

    def kinds(self, name: str, point: ast.AST | None) -> set[_Kind]:
        """What *name*, read at *point* of this scope or once it has run (``None``), may be bound to.

        The scope that holds the name is found as Python finds it: this one
        when it binds the name, the module for a name declared ``global``,
        the function around for one declared ``nonlocal``, and otherwise the
        scope around, read where this one runs (a class body, a
        comprehension) or once it has run (past a function or a lambda,
        which run when called). There, the bindings that may reach the read
        (:func:`ast_scan.live_bindings`): the later of two in a row, either
        of two in the branches of an ``if``, one on an earlier turn of a loop
        around the read, any of them when none runs before it; with whatever
        a scope nested there binds the name to through ``global`` or
        ``nonlocal``, which may run at any time.
        """
        names: _ScopeNames | None = self
        called = False
        while names is not None:
            if name in names.declared_global:
                names, point = names.module(), None
                continue
            if name in names.declared_nonlocal:
                names, point = names.outer, None
                continue
            if names.binds(name) or names.outer is None:
                found = set(names.from_inside.get(name, ()))
                bindings = names.flow.get(name, [])
                if any(kind is not None for _, kind in bindings):
                    nodes = [node for node, _ in bindings]
                    live = live_bindings(names.tree, nodes, point)
                    found.update(
                        kind
                        for node, kind in bindings
                        if kind is not None and any(node is other for other in live)
                    )
                return found
            called = called or isinstance(names.scope, _FUNCTIONS)
            names, point = names.outer, None if called else names.at
        return set()

    def may_hold(self, name: ast.Name, kind: _Kind) -> bool:
        """Whether *name*, read in this scope, may be bound to *kind* where it is read."""
        return kind in self.kinds(name.id, name)


def _nested_names(
    tree: ast.Module, scope: _Scope, around: _ScopeNames, own: list[ast.AST]
) -> _ScopeNames:
    """What *scope*, whose own nodes are *own*, binds, and where it reads the names it does not.

    *around* is the scope it is written in. A function and a lambda read
    the names around them as they stand once that scope has run; a class
    body and a comprehension run where they are written and read them
    there. None reads a class body's names: a scope written in one reads
    from the scope around the class, where the class statement runs, and a
    generic class's type parameters hide those names for it.
    """
    hidden: frozenset[str] = frozenset()
    outer: _ScopeNames | None = around
    at: ast.AST | None = None if isinstance(scope, _FUNCTIONS) else scope
    if isinstance(around.scope, ast.ClassDef):
        hidden = around.entry
        outer = around.outer
        at = None if isinstance(scope, _FUNCTIONS) else around.at
    if isinstance(scope, (ast.Lambda, *_COMPREHENSIONS)):
        entry = frozenset(_expression_names(scope, own)) | hidden
        empty: frozenset[str] = frozenset()
        return _ScopeNames(scope, tree, {}, entry, empty, empty, outer, at)
    flow, declared_global, declared_nonlocal = _statement_bindings(own)
    entry = frozenset(_type_parameters(scope)) | hidden
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        entry |= {parameter.arg for parameter in _parameters(scope.args)}
    return _ScopeNames(
        scope,
        tree,
        flow,
        entry,
        frozenset(declared_global),
        frozenset(declared_nonlocal),
        outer,
        at,
    )


def _send_declared(names: _ScopeNames) -> None:
    """Hand what *names*' scope binds a name it declares ``global`` or ``nonlocal`` to, to the scope that holds the name.

    The module for ``global``; for ``nonlocal``, the nearest function around
    that binds the name. The scope may run at any time, so what it binds
    joins every read of the name there.
    """
    for name in names.declared_global | names.declared_nonlocal:
        kinds = {kind for _, kind in names.flow.get(name, []) if kind is not None}
        target: _ScopeNames | None = names.module()
        if name not in names.declared_global:
            target = names.outer
            while target is not None and not target.binds(name):
                target = None if name in target.declared_global else target.outer
        if target is not None and kinds:
            target.from_inside.setdefault(name, set()).update(kinds)


def _alias_scopes(tree: ast.Module) -> list[tuple[list[ast.AST], _ScopeNames]]:
    """Each scope of *tree*, as its own nodes and what it binds and reads of numpy and ``math``.

    A ``from numpy import bool_ as flag``, a ``from math import pi`` or an
    ``import math as m`` binds its name where Python binds it: in the scope
    that imports it, and in the functions, classes and comprehensions
    nested there that do not bind the name themselves; in the module when a
    function that declares the name ``global`` imports it, and in the
    function around when one declares it ``nonlocal``, which a pass over
    every scope collects before any name is read. A class body's methods
    and comprehensions do not see the class's names; a comprehension's loop
    variable and a generic function's or class's type parameter hide the
    import. A read takes the bindings the name may hold where it is read
    (:meth:`_ScopeNames.kinds`), so a later binding of the name, an
    assignment as much as an import, replaces an earlier one. A name
    assigned ``bool`` or a constant is not followed.
    """
    own, nested = _own_nodes(tree)
    flow, _, _ = _statement_bindings(own)
    none: frozenset[str] = frozenset()
    module = _ScopeNames(tree, tree, flow, none, none, none, None, None)
    found = [(own, module)]
    pending = [(inner, module) for inner in nested]
    while pending:
        scope, around = pending.pop()
        own, nested = _own_nodes(scope)
        names = _nested_names(tree, scope, around, own)
        found.append((own, names))
        pending.extend((inner, names) for inner in nested)
    for _, names in found:
        _send_declared(names)
    return found


def _is_dtype_call(node: ast.expr) -> TypeGuard[ast.Call]:
    """Whether *node* is a call to a ``dtype`` constructor, ``np.dtype(...)``."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "dtype"
    )


def _is_bool_dtype(node: ast.expr, names: _ScopeNames | None = None) -> bool:
    """Whether *node* names the boolean dtype, in a spelling the scan recognises.

    ``bool``; a name that may hold numpy's boolean where it is read, as
    *names*, the scope it is read in, has it (``from numpy import bool_ as
    flag``); an attribute ``bool``, ``bool_`` or ``bool8`` of whatever owner
    (``np``, ``numpy``, an array namespace ``xp``); a ``dtype`` call on any
    of them, positional or ``dtype=``, and that call's ``.type``; and the
    strings ``"bool"``, ``"bool_"``, ``"bool8"``, ``"?"`` and ``"b1"``, with
    or without a byte-order mark. A name assigned ``bool`` (``kind = bool``)
    is not followed.
    """
    if isinstance(node, ast.Attribute) and node.attr == "type":
        return _is_dtype_call(node.value) and _is_bool_dtype(node.value, names)
    if _is_dtype_call(node):
        given = [*node.args[:1], *(k.value for k in node.keywords if k.arg == "dtype")]
        return any(_is_bool_dtype(dtype, names) for dtype in given)
    if isinstance(node, ast.Name):
        return node.id == "bool" or (names is not None and names.may_hold(node, "bool"))
    if isinstance(node, ast.Attribute):
        return node.attr in _BOOL_DTYPE_NAMES
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.lstrip(_BYTE_ORDER_MARKS) in _BOOL_DTYPE_NAMES
    )


def _is_bool_cast(node: ast.Call, names: _ScopeNames | None = None) -> bool:
    """Whether *node* is an ``astype`` to ``bool``, in a spelling the scan recognises.

    The call as ``x.astype(bool)``, ``np.astype(x, bool)`` or
    ``np.ndarray.astype(x, bool)``: the dtype is read from the first two
    arguments, where the method form's second is its order string, never a
    dtype, and from ``dtype=``, in the spellings :func:`_is_bool_dtype`
    lists. A float cast to ``bool`` is ``x != 0.0`` under another name. The
    source cannot say which arrays are floats, so the cast is refused
    whatever it is applied to: a boolean array needs none, an integer one
    says ``!= 0``.
    """
    if not (isinstance(node.func, ast.Attribute) and node.func.attr == "astype"):
        return False
    dtypes = [*node.args[:2], *(k.value for k in node.keywords if k.arg == "dtype")]
    return any(_is_bool_dtype(dtype, names) for dtype in dtypes)


def _float_equalities(tree: ast.Module) -> list[str]:
    """Each equality with a float constant, or cast to ``bool``, of *tree*, as ``line source``.

    An ``==`` or ``!=`` with a float constant on one side, in the spellings
    :func:`_is_float_constant` recognises, and every ``astype`` to ``bool``
    that :func:`_is_bool_cast` recognises, which on a float array is the same
    test against zero, in the order of the lines. A name is read in the
    scope and at the point where Python reads it (:func:`_alias_scopes`).
    """
    found: list[tuple[int, str]] = []
    for own, names in _alias_scopes(tree):
        for node in own:
            if isinstance(node, ast.Call) and _is_bool_cast(node, names):
                found.append((node.lineno, ast.unparse(node)))
                continue
            if not isinstance(node, ast.Compare):
                continue
            left = node.left
            for operator, right in zip(node.ops, node.comparators, strict=True):
                if isinstance(operator, (ast.Eq, ast.NotEq)) and (
                    _is_float_constant(left, names) or _is_float_constant(right, names)
                ):
                    found.append((node.lineno, ast.unparse(node)))
                left = right
    return [f"{line} {source}" for line, source in sorted(found, key=lambda f: f[0])]


def test_the_float_equality_check_sees_every_spelling_of_a_float_constant() -> None:
    """A literal, a signed one, one named by numpy or math, ``float("inf")``, and a cast to bool.

    The cast in each spelling the scan recognises, of the call (the method,
    ``np.astype`` and ``np.ndarray.astype``) and of the dtype
    (``np.dtype(bool)``, positional or by keyword, and its ``.type``, a
    string with a byte-order mark, an array namespace's ``bool``, a name
    imported from numpy); a name assigned ``bool`` and an array built with
    a boolean dtype are left to review.
    """
    source = "\n".join(
        [
            "a = x == 0.0",
            "b = x != -1.5",
            "c = x == np.inf",
            "d = -math.inf == x",
            "e = x == float('nan')",
            "f = y < x == numpy.pi",
            "g = x == 0",
            "h = x <= np.inf",
            "i = np.isposinf(x)",
            "j = x == other",
            "k = x.astype(bool)",
            "l = x.astype(np.bool_)",
            "m = np.diff(x).astype(dtype='?')",
            "n = x.astype(numpy.bool)",
            "o = x.astype(float)",
            "p = np.asarray(x > 0.5, dtype=bool)",
            "q = np.astype(x, bool)",
            "r = np.ndarray.astype(x, 'b1')",
            "s = x.astype(np.dtype(bool))",
            "t = x.astype(dtype=numpy.dtype('?'))",
            "u = x.astype('|b1')",
            "v = x.astype('=?')",
            "w = x.astype(xp.bool)",
            "from numpy import bool_ as flag, float64",
            "y = x.astype(flag)",
            "z = x.astype(np.float64, 'K')",
            "aa = np.astype(x, float64)",
            "x = y.astype(np.dtype(bool).type)",
            "ab = x.astype(numpy.dtype(dtype='?'))",
            "ac = x.astype(np.dtype(float).type)",
            "ad = x.astype(y.dtype.type)",
        ]
    )
    assert [line.split()[0] for line in _float_equalities(ast.parse(source))] == [
        "1", "2", "3", "4", "5", "6", "11", "12", "13", "14", "17", "18", "19",
        "20", "21", "22", "23", "25", "28", "29",
    ]  # fmt: skip


def test_the_float_equality_check_reads_a_numpy_bool_alias_in_its_own_scope() -> None:
    """A name imported as numpy's boolean is one only where Python resolves it there.

    An import at the top of a module reaches every function that does not bind
    the name itself, and one that declares it ``global`` even where the
    function around it binds the name; one inside a function reaches that
    function and the functions and comprehensions nested in it, and not a
    function nested there that declares the name ``global``. None reaches a
    class body's methods and comprehensions (the comprehension's first
    iterable runs in the class body), another function, a comprehension that
    loops over the name, or a generic function or class that takes it as a
    type parameter, where the same name may hold any dtype; a ``:=`` in a
    comprehension binds the name in the function around it.
    """
    source = "\n".join(
        [
            "from numpy import bool_ as flag",
            "def uses_the_module_import(x):",
            "    return x.astype(flag)",
            "def binds_the_name_itself(x, flag):",
            "    return x.astype(flag)",
            "def assigns_the_name(x):",
            "    flag = np.float64",
            "    return x.astype(flag)",
            "def imports_its_own(x):",
            "    from numpy import bool_ as mask",
            "    def inner(y):",
            "        return y.astype(mask)",
            "    return x.astype(mask)",
            "def another(x, mask):",
            "    return x.astype(mask)",
            "class Holder:",
            "    from numpy import bool_ as kept",
            "    ones = np.ones(2).astype(kept)",
            "    cast = staticmethod(lambda x: x.astype(kept))",
            "    def method(self, x, kept=np.float64):",
            "        return x.astype(kept)",
            "def global_name(x):",
            "    global flag",
            "    return x.astype(flag)",
            "def comprehension(x, y):",
            "    kinds = [str(flag) for flag in y]",
            "    return x.astype(flag)",
            "def outer(x):",
            "    flag = np.float64",
            "    def inner(y):",
            "        global flag",
            "        return y.astype(flag)",
            "    return inner(x)",
            "def imports_then_declares_global(x):",
            "    from numpy import bool_ as mask",
            "    def inner(y):",
            "        global mask",
            "        return y.astype(mask)",
            "    return inner(x)",
            "def comprehension_variable(xs):",
            "    return [x.astype(flag) for flag in (np.float32, np.float64)]",
            "class Casts:",
            "    from numpy import bool_ as kept",
            "    each = [x.astype(kept) for x in xs]",
            "    first = [y for y in xs.astype(kept)]",
            "def walrus(xs, x):",
            "    kinds = [(flag := k) for k in xs]",
            "    return x.astype(flag)",
            "def generic[flag](x):",
            "    return x.astype(flag)",
            "class Box[flag]:",
            "    def method(self, x):",
            "        return x.astype(flag)",
            "def comprehension_sees_its_function(xs):",
            "    from numpy import bool_ as mask",
            "    return {x: x.astype(mask) for x in xs}",
        ]
    )
    assert [line.split()[0] for line in _float_equalities(ast.parse(source))] == [
        "3", "12", "13", "18", "24", "27", "32", "45", "56",
    ]  # fmt: skip


def test_the_float_equality_check_reads_a_constant_imported_by_name() -> None:
    """A constant imported from numpy or ``math`` by name, or read through the module renamed.

    ``from math import pi`` makes ``x == pi`` the comparison ``x == math.pi``
    is, and ``import math as m`` makes ``m.pi`` the constant; each is read in
    the scope where Python resolves the name, so a parameter called ``pi``
    is a variable, and a name another function imported is not this one's.
    """
    source = "\n".join(
        [
            "from math import pi, inf as INF",
            "from numpy import nan",
            "import math as m",
            "import numpy as n",
            "a = x == pi",
            "b = INF != x",
            "c = x == nan",
            "d = x == m.e",
            "e = x == n.inf",
            "def takes_pi(x, pi):",
            "    return x == pi",
            "def imports_tau(x):",
            "    from math import tau",
            "    return x == tau",
            "def another(x):",
            "    return x == tau",
            "f = x == e",
        ]
    )
    assert [line.split()[0] for line in _float_equalities(ast.parse(source))] == [
        "5", "6", "7", "8", "9", "14",
    ]  # fmt: skip


def test_the_float_equality_check_reads_the_binding_a_name_holds_where_it_is_read() -> (
    None
):
    """Of two bindings of one name in one scope, a read takes the one Python gives it there.

    The later of two imports in a row, whichever ran of two in the branches
    of an ``if``, an import on an earlier turn of a loop, and an assignment
    after an import, which the name then holds instead. A function reads its
    module's name as it stands once the module has run; a class body and a
    comprehension run where they are written, so they read it there.
    """
    source = "\n".join(
        [
            "from math import pi as flag",
            "from numpy import bool_ as flag",
            "a = x.astype(flag)",
            "b = x == flag",
            "from math import pi as flag",
            "c = x == flag",
            "d = x.astype(flag)",
            "def reads_the_module(x):",
            "    return x == flag",
            "def imports_twice(x):",
            "    from numpy import bool_ as mask",
            "    y = x.astype(mask)",
            "    from math import tau as mask",
            "    z = x.astype(mask)",
            "    return x == mask",
            "def rebinds(x):",
            "    from numpy import bool_ as mask",
            "    mask = np.float64",
            "    return x.astype(mask)",
            "def either(x, wide):",
            "    if wide:",
            "        from numpy import bool_ as mask",
            "    else:",
            "        from numpy import float64 as mask",
            "    return x.astype(mask)",
            "def on_a_later_turn(xs):",
            "    for x in xs:",
            "        y = x.astype(mask)",
            "        from numpy import bool_ as mask",
            "g = [v.astype(flag) for v in xs]",
            "from numpy import bool_ as kept",
            "class Early:",
            "    h = x.astype(kept)",
            "    i = [v.astype(kept) for v in xs]",
            "import math as kept",
            "class Late:",
            "    j = x.astype(kept)",
            "    k = x == kept.pi",
        ]
    )
    assert [line.split()[0] for line in _float_equalities(ast.parse(source))] == [
        "3", "6", "9", "12", "15", "25", "28", "33", "34", "38",
    ]  # fmt: skip


def test_the_float_equality_check_reads_a_module_name_a_function_binds() -> None:
    """An import under ``global`` binds the module's name, one under ``nonlocal`` the function's.

    ``from numpy import bool_ as flag`` in a function that declares ``flag``
    global makes the module's ``flag`` numpy's boolean once the function has
    run, for every function that reads the module's name and for the module
    itself, wherever the function is written; the same for a float constant
    and for the module ``math`` imported that way, and for a function nested
    in another that declares the name ``nonlocal``. A function that binds the
    name itself still holds its own.
    """
    source = "\n".join(
        [
            "def reads_before_the_import(x):",
            "    return x.astype(flag)",
            "def binds_the_module_name():",
            "    global flag",
            "    from numpy import bool_ as flag",
            "def binds_a_constant():",
            "    global limit",
            "    from math import inf as limit",
            "def compares(x):",
            "    return x == limit",
            "def binds_the_module():",
            "    global m",
            "    import math as m",
            "def compares_through_it(x):",
            "    return x == m.pi",
            "class Holder:",
            "    def method(self):",
            "        global kept",
            "        from numpy import bool_ as kept",
            "def sibling(x):",
            "    return x.astype(kept)",
            "def outer(x):",
            "    mask = np.float64",
            "    def inner():",
            "        nonlocal mask",
            "        from numpy import bool_ as mask",
            "    inner()",
            "    return x.astype(mask)",
            "def binds_its_own(x, flag):",
            "    return x.astype(flag)",
            "a = x.astype(flag)",
        ]
    )
    assert [line.split()[0] for line in _float_equalities(ast.parse(source))] == [
        "2", "10", "15", "21", "28", "31",
    ]  # fmt: skip


def test_no_source_compares_a_float_for_equality() -> None:
    """Floating point does not answer `==`, and the tree had stopped asking.

    `array_directivity_index` reintroduced the one case: its sine-integral
    footprint guarded a removable singularity with ``x == 0.0``, which an
    endfire steer reaches exactly and nothing near it does. Writing the term as
    ``x sinc(x)^2`` removes both the singularity and the comparison. Nothing in
    the repository could see the regression; SonarCloud reported it after the
    branch was already pushed, so the class is closed here instead.

    A cast to ``bool`` is the same test spelt otherwise: on a float array,
    ``x.astype(bool)`` is ``x != 0.0``, and the literal check let eleven of
    them through (the pinned exponential's two exactness tests, the weighting
    design's zeros at the origin, and eight exact tests of the ray and
    underwater solvers). The exponential's now read the bits, the zeros at the
    origin are counted from the prototype, and an exact test that is meant
    names itself through ``exactly_nonzero``. The cast is refused whatever it
    is applied to, since the source does not say which arrays are floats.
    """
    import pathlib

    equalities: list[str] = []
    for path in sorted(pathlib.Path("src/phonometry").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        equalities.extend(
            f"{path.relative_to('src')}:{line}" for line in _float_equalities(tree)
        )

    assert not equalities, "source comparing a float for equality:\n  " + "\n  ".join(
        equalities
    )


def _overload_sets(tree: ast.Module) -> list[list[ast.FunctionDef]]:
    """Every set of ``@overload`` definitions of one name in one scope."""
    found: list[list[ast.FunctionDef]] = []
    for scope in ast.walk(tree):
        body = getattr(scope, "body", None)
        if not isinstance(body, list):
            continue
        by_name: dict[str, list[ast.FunctionDef]] = {}
        for node in body:
            if isinstance(node, ast.FunctionDef) and any(
                (isinstance(d, ast.Name) and d.id == "overload")
                or (isinstance(d, ast.Attribute) and d.attr == "overload")
                for d in node.decorator_list
            ):
                by_name.setdefault(node.name, []).append(node)
        found.extend(by_name.values())
    return found


def _is_bool_literal(annotation: ast.expr | None) -> bool:
    """Whether an annotation is ``Literal[True]`` or ``Literal[False]``."""
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        annotation = ast.parse(annotation.value, mode="eval").body
    if not isinstance(annotation, ast.Subscript):
        return False
    head = annotation.value
    name = head.id if isinstance(head, ast.Name) else getattr(head, "attr", None)
    if name != "Literal":
        return False
    items = (
        annotation.slice.elts
        if isinstance(annotation.slice, ast.Tuple)
        else [annotation.slice]
    )
    return any(
        isinstance(item, ast.Constant) and isinstance(item.value, bool)
        for item in items
    )


def test_an_overload_on_a_true_or_false_literal_also_takes_a_bool() -> None:
    """A flag held in a variable is a ``bool``, and mypy has to accept it.

    A function whose return type follows a flag states it with one overload
    for ``Literal[True]`` and one for ``Literal[False]``. mypy does not split
    a ``bool`` argument into those two literals to try each overload, so with
    only the two, a caller whose flag comes from a setting or a parameter of
    its own gets "No overload variant matches" for a call that runs.
    ``estimate_reverberation_index(weighted=)`` and
    ``metrology.sensitivity(narrowband=)`` had only the two, while
    ``weighted_impact_improvement`` and ``impact_improvement_adaptation_term``
    came with a third from the start. An overload that types the flag as
    ``bool`` returns the union of the two forms, and ``tests/static_typing``
    calls each of them with a variable, in every place the call can take
    the other arguments, since this test sees only the flag's type.

    The overloads are read through the parser, so an overload set is the
    run of ``@overload`` definitions of one name in one scope, whatever their
    layout over lines.
    """
    missing: list[str] = []
    keyed_sets = 0
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for overloads in _overload_sets(tree):
            keyed: set[str] = set()
            plain: set[str] = set()
            for definition in overloads:
                arguments = definition.args
                for parameter in (
                    *arguments.posonlyargs,
                    *arguments.args,
                    *arguments.kwonlyargs,
                ):
                    if _is_bool_literal(parameter.annotation):
                        keyed.add(parameter.arg)
                    elif (
                        parameter.annotation is not None
                        and ast.unparse(parameter.annotation) == "bool"
                    ):
                        plain.add(parameter.arg)
            keyed_sets += bool(keyed)
            missing.extend(
                f"{path.relative_to(SRC.parent)}:{overloads[0].lineno} "
                f"{overloads[0].name}({name}=)"
                for name in sorted(keyed - plain)
            )

    assert keyed_sets >= 4, f"only {keyed_sets} overload sets keyed on a flag"
    assert not missing, (
        "overloads typed for Literal[True] and Literal[False] with none for a "
        "bool:\n  " + "\n  ".join(missing)
    )


def test_no_suppression_comment_hides_its_reason_from_the_parser() -> None:
    """A `# noqa` directive ends at its codes, and the reason goes above it.

    Ruff documents the directive as ``# noqa: CODE``, and reads codes until it
    meets something that is not one. Prose after a code is undefined ground:
    ruff has tolerated it, the static analyser reports it as a malformed
    suppression, and a directive that silently stops applying is worse than
    the lint it was hiding. Thirteen of these had accumulated in three shapes,
    a dash, a double dash and a second hash, and SonarCloud only saw the
    fourteenth because it was new code in a pull request. The reason belongs on
    the line above, where nothing has to parse it.

    The scripts and the tests are read too: fifty-two directives there carried
    their reason after the codes, in the same three shapes and a parenthesis.
    Only comments are read, so a docstring that quotes the directive is not one.
    """
    import pathlib
    import re
    import tokenize

    directive = re.compile(r"#\s*noqa:\s*(?P<tail>.*)$")
    codes = re.compile(r"^[A-Z]+[0-9]+(?:\s*,\s*[A-Z]+[0-9]+)*\s*$")
    trailing: list[str] = []
    files = [
        path
        for folder in ("src/phonometry", "scripts", "tests")
        for path in sorted(pathlib.Path(folder).rglob("*.py"))
    ]
    for path in files:
        with path.open("rb") as handle:
            comments = [
                token
                for token in tokenize.tokenize(handle.readline)
                if token.type == tokenize.COMMENT
            ]
        for token in comments:
            match = directive.search(token.string)
            if match and not codes.match(match.group("tail")):
                trailing.append(f"{path}:{token.start[0]} {token.line.strip()}")

    assert not trailing, (
        "suppression comments carrying prose after their codes:\n  "
        + "\n  ".join(trailing)
    )


def test_no_error_message_carries_a_comma_decimal() -> None:
    """Error messages are English prose, and English prose takes a point.

    The library writes its own numbers into refusals: a temperature floor at
    absolute zero, the thermodynamic bound on a Poisson ratio. Seven of them
    had drifted to a comma, four of them the same -273,15, while eleven
    comparable messages used a point and one of the two spellings of the same
    0.5 sat in each camp.

    Nothing could see it. The figure gate that does police decimal commas
    reads drawn labels, not exceptions, because its subject is the Spanish
    edition of a figure and a comma inside ``$...$`` sets with the wrong
    spacing. An error message is neither drawn nor translated.

    This reads the ``msg`` assignments a module raises from, and reads them
    through the parser rather than line by line: nearly every refusal here is
    a parenthesised string spanning several lines, and a scan that saw only
    the ``msg = (`` line saw none of the text.

    A comma between digits is a decimal only when a letter does not precede
    it. Subscript pairs are written the same way and are notation rather than
    numbers, so ``k2,1`` and ``F2,b`` stay as they are while ``31,5 Hz``
    does not.
    """
    offenders: list[str] = []
    for path in sorted(Path("src/phonometry").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            text = _message_text(node)
            if text is None:
                continue
            found = re.search(r"(?<![A-Za-z])\d,\d", text)
            if found:
                offenders.append(f"{path}:{node.lineno}  ...{found.group(0)}...")
    assert not offenders, "comma decimal in an English message:\n" + "\n".join(
        offenders
    )


def test_clause_poles_are_not_migrated_to_the_physical_bound() -> None:
    """Two different guards wear the same clothes, and only one of them shares.

    ``require_above_absolute_zero`` bounds a temperature at -273,15 degC,
    because below that it is not a temperature. Three clauses guard something
    else: their own formula is printed as ``sqrt(273 + theta)`` or
    ``1245/(273 + t)``, with the 273 the standard prints, so what breaks there
    sits 0,15 degC higher. Migrating those onto the shared helper would leave a
    band of a sixth of a degree that clears the check and then overflows.

    The three are pinned by name, so a later harmonising sweep has to read this
    before it reaches them.
    """
    clause_poles = {
        "emission/_shared.py": "273",
        "emission/_sound_power_anechoic.py": "273",
        "building/measurement/intensity_insulation.py": "273",
    }
    for relative, printed in clause_poles.items():
        text = (SRC / relative).read_text(encoding="utf-8")
        assert "require_above_absolute_zero" not in text, (
            f"{relative} guards the pole of its own clause, printed with "
            f"{printed}, not absolute zero"
        )


def test_the_grid_flag_is_named_the_way_matplotlib_names_it() -> None:
    """The 295 ``ax.grid(visible=...)`` sites rest on one matplotlib name.

    A boolean is written by name, at the definition and at the call, and for
    the plot corpus the call almost always means ``ax.grid``. matplotlib
    declares that parameter ``visible``; every site was rewritten to say so
    rather than to pass it by position. If a matplotlib release renames it,
    those sites become a ``TypeError`` at the first figure, and the failure
    would arrive as a wall of unrelated red. This pins the assumption instead,
    so the upgrade that breaks it says which name moved.
    """
    import inspect

    from matplotlib.axes import Axes

    names = [n for n in inspect.signature(Axes.grid).parameters if n != "self"]
    first = names[0]
    assert first == "visible", (
        f"matplotlib now calls the first grid parameter {first!r}; the plot "
        "corpus passes it as 'visible'"
    )


def test_a_judgement_summary_does_not_open_with_another_family_verb() -> None:
    """The three judgement verbs mean three different things, and say so.

    `verify_` judges an instrument against the requirements a standard sets for
    it, `assess_` judges a measured situation against limits or categories, and
    `check_` judges the arrangement a method needs before its numbers mean
    anything (docs/contributing/naming.md#n9). A summary may
    open however it reads best, as a question or with any other verb, but one
    that opens with a *different* family's verb tells a reader the prefix was
    picked at random: `check_base_plate_scattering` used to begin "Verify", and
    six of the ten `verify_` functions began "Check".
    """
    import importlib
    import inspect
    import pkgutil

    import phonometry as ph

    families = {"verify_": "verify", "assess_": "assess", "check_": "check"}
    mismatched: list[str] = []
    seen: set[str] = set()
    for module in pkgutil.walk_packages(ph.__path__, "phonometry."):
        if "._" in module.name:
            continue
        try:
            imported = importlib.import_module(module.name)
        # A module that will not import is another test's finding, not this one's
        except Exception:
            continue
        for name in getattr(imported, "__all__", []):
            obj = getattr(imported, name, None)
            if not inspect.isfunction(obj) or name in seen:
                continue
            family = next((v for p, v in families.items() if name.startswith(p)), None)
            if family is None:
                continue
            seen.add(name)
            words = (inspect.getdoc(obj) or "").split()
            opening = words[0].rstrip(".,:").lower() if words else ""
            if opening in set(families.values()) - {family}:
                mismatched.append(f"{name} ({family}) opens with {opening!r}")
    assert not mismatched, mismatched
    assert len(seen) >= 26, f"only {len(seen)} judgement functions found"


def _published_classes() -> dict[str, type]:
    """Every class a domain package (or the root) publishes, by its name."""
    import inspect

    import phonometry

    owners = [phonometry] + [
        getattr(phonometry, name)
        for name in sorted(dir(phonometry))
        if not name.startswith("_") and inspect.ismodule(getattr(phonometry, name))
    ]
    return {
        name: obj
        for owner in owners
        for name in getattr(owner, "__all__", ())
        if inspect.isclass(obj := getattr(owner, name))
    }


def test_every_published_warning_is_a_phonometry_warning() -> None:
    """One ``filterwarnings`` rule reaches every warning the library emits.

    The root promises it: "every warning the library emits derives from
    PhonometryWarning". ``RoadDeviceWarning`` derived from ``UserWarning``
    alone, so ``warnings.simplefilter("error", PhonometryWarning)`` let the
    EN 1793 ratio cap through while it escalated every other advisory. The
    walk reads what each domain's ``__all__`` publishes, which reaches the
    classes defined in private modules (``fluids._state``, the io privates)
    that a walk of the public modules skips.
    """
    from phonometry import PhonometryWarning

    outside = sorted(
        f"{name} derives from {[base.__name__ for base in obj.__mro__[1:]]}"
        for name, obj in _published_classes().items()
        if issubclass(obj, Warning)
        and obj is not PhonometryWarning
        and not issubclass(obj, PhonometryWarning)
    )
    assert not outside, (
        "published warnings outside the PhonometryWarning hierarchy:\n  "
        + "\n  ".join(outside)
    )


def test_every_published_exception_is_named_an_error() -> None:
    """An exception reads as one: ``<Topic>Error``, as PEP 8 asks.

    ``FluidPropertyUnavailable`` was the one published exception without the
    suffix, beside ``CatalogueError``; a reader who met it in an ``except``
    clause could not tell it from a value.
    """
    unnamed = sorted(
        name
        for name, obj in _published_classes().items()
        if issubclass(obj, BaseException)
        and not issubclass(obj, Warning)
        and not name.endswith("Error")
    )
    assert not unnamed, f"published exceptions not named <Topic>Error: {unnamed}"


def _resolve_category(
    module: object,
    function: ast.FunctionDef | ast.AsyncFunctionDef | None,
    expression: ast.expr,
) -> object:
    """The object a ``warnings.warn`` category expression names, or ``None``.

    A name is looked up in the module first and then in the imports of the
    function around the call (the underwater solvers import their warning
    lazily); a parameter of that function is answered with its annotation, as
    the string ``type[...]`` it is written as.
    """
    import importlib

    if isinstance(expression, ast.Name):
        if function is not None:
            arguments = function.args
            for arg in arguments.posonlyargs + arguments.args + arguments.kwonlyargs:
                if arg.arg == expression.id:
                    return ast.unparse(arg.annotation) if arg.annotation else None
            for node in ast.walk(function):
                if isinstance(node, ast.ImportFrom) and any(
                    (alias.asname or alias.name) == expression.id
                    for alias in node.names
                ):
                    package = getattr(module, "__package__", None) or ""
                    imported = importlib.import_module(
                        "." * node.level + (node.module or ""), package
                    )
                    return getattr(imported, expression.id, None)
        return getattr(module, expression.id, None)
    if isinstance(expression, ast.Attribute):
        owner = _resolve_category(module, function, expression.value)
        return getattr(owner, expression.attr, None)
    return None


def _warning_calls(
    tree: ast.AST,
) -> list[tuple[ast.FunctionDef | ast.AsyncFunctionDef | None, ast.Call]]:
    """Every ``warnings.warn(...)`` call, with the function it is written in."""
    calls: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef | None, ast.Call]] = []

    def visit(
        node: ast.AST, function: ast.FunctionDef | ast.AsyncFunctionDef | None
    ) -> None:
        for child in ast.iter_child_nodes(node):
            inner = (
                child
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                else function
            )
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "warn"
                and isinstance(child.func.value, ast.Name)
                and child.func.value.id == "warnings"
            ):
                calls.append((function, child))
            visit(child, inner)

    visit(tree, None)
    return calls


#: Functions that raise again, here, a warning another process raised, with
#: the class it was raised with: its topic is the other process's, so it is
#: a variable here, not a published class written at the call.
WARNING_RELAYS: dict[str, str] = {
    "simulation/_remote/client.py:_relay": "raises again, at the caller's line, a warning the node raised, with its own class",
}


def warnings_without_a_topic(path: Path) -> list[str]:
    """Each ``warnings.warn`` in *path* whose category is not a published topic.

    The category has to be explicit and has to resolve to a published, strict
    subclass of ``PhonometryWarning``: never missing (a bare ``UserWarning``),
    never the root itself, which leaves a caller who wants to silence one
    advisory only the rule that silences every other. A helper that warns on
    behalf of several topics takes the category as a parameter typed
    ``type[PhonometryWarning]``. A relay of :data:`WARNING_RELAYS` is left
    out: the class it warns with is the other process's.
    """
    import importlib

    from phonometry import PhonometryWarning

    rel = path.relative_to(SRC.parent).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    module = importlib.import_module(".".join(parts))
    published = set(_published_classes().values())
    found: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for function, call in _warning_calls(tree):
        relayed = (
            function is not None
            and f"{path.relative_to(SRC).as_posix()}:{function.name}" in WARNING_RELAYS
        )
        if relayed:
            continue
        expression = next(
            (keyword.value for keyword in call.keywords if keyword.arg == "category"),
            call.args[1] if len(call.args) > 1 else None,
        )
        where = f"{path.relative_to(SRC).as_posix()}:{call.lineno}"
        if expression is None:
            found.append(f"{where} names no category")
            continue
        category = _resolve_category(module, function, expression)
        if isinstance(category, str):
            if category.replace(" ", "") != "type[PhonometryWarning]":
                found.append(f"{where} takes its category as {category!r}")
            continue
        if (
            not isinstance(category, type)
            or not issubclass(category, PhonometryWarning)
            or category is PhonometryWarning
            or category not in published
        ):
            found.append(f"{where} warns with {ast.unparse(expression)}")
    return found


def test_every_warning_names_a_published_topic() -> None:
    """A warning is filtered by its topic, so each one is emitted as one.

    Seven calls warned as a plain ``UserWarning`` (two of them naming no
    category at all), and five as the bare ``PhonometryWarning``: the low
    sampling rate of the filter bank beside its own ``FilterBankWarning``, the
    tone burst, and three underwater solvers. None of them could be silenced
    or escalated without silencing or escalating every other advisory too.
    """
    found = [
        offence
        for path in sorted(SRC.rglob("*.py"))
        if "warnings.warn" in path.read_text(encoding="utf-8")
        for offence in warnings_without_a_topic(path)
    ]
    assert not found, "warnings emitted without a published topic:\n  " + (
        "\n  ".join(found)
    )


def test_every_warning_relay_still_relays() -> None:
    for key in WARNING_RELAYS:
        file, _, name = key.partition(":")
        tree = ast.parse((SRC / file).read_text(encoding="utf-8"))
        relays = [
            function.name
            for function, _ in _warning_calls(tree)
            if function is not None
        ]
        assert name in relays, (
            f"{key} no longer raises a warning; drop it from WARNING_RELAYS"
        )


def broad_warning_filters(path: Path) -> list[str]:
    """Each warning filter in *path* that names no topic.

    A ``warnings.simplefilter`` or ``warnings.filterwarnings`` call inside the
    library has to name the class it means: a filter on ``UserWarning``,
    ``Warning`` or the root ``PhonometryWarning`` (or on no category at all)
    also swallows every other advisory raised inside its block, including one
    the caller asked to see.
    """
    import builtins
    import importlib

    from phonometry import PhonometryWarning

    rel = path.relative_to(SRC.parent).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    module = importlib.import_module(".".join(parts))
    broad = {Warning, UserWarning, PhonometryWarning}
    found: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    for call in ast.walk(tree):
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr in {"simplefilter", "filterwarnings"}
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "warnings"
        ):
            continue
        position = 1 if call.func.attr == "simplefilter" else 2
        expression = next(
            (keyword.value for keyword in call.keywords if keyword.arg == "category"),
            call.args[position] if len(call.args) > position else None,
        )
        where = f"{path.relative_to(SRC).as_posix()}:{call.lineno}"
        if expression is None:
            found.append(f"{where} filters every warning")
            continue
        function = next(
            (
                node
                for node in functions
                if node.lineno <= call.lineno <= (node.end_lineno or node.lineno)
            ),
            None,
        )
        category = _resolve_category(module, function, expression)
        if category is None and isinstance(expression, ast.Name):
            category = getattr(builtins, expression.id, None)
        if category in broad:
            found.append(f"{where} filters {ast.unparse(expression)}")
    return found


def test_a_warning_filter_in_the_library_names_its_topic() -> None:
    """The library silences the one advisory it means, never a whole family.

    The railway passage bank silenced ``UserWarning`` around the filter bank
    it builds, to drop the band the rate cannot carry; inside that block every
    advisory the bank raised for any other reason went unseen as well. It now
    silences ``FilterBankWarning``, the topic the bank warns with.
    """
    found = [
        offence
        for path in sorted(SRC.rglob("*.py"))
        if "filterwarnings(" in (text := path.read_text(encoding="utf-8"))
        or "simplefilter(" in text
        for offence in broad_warning_filters(path)
    ]
    assert not found, "warning filters that name no topic:\n  " + "\n  ".join(found)


def test_a_docstring_lists_a_warning_under_warns() -> None:
    """A warning is emitted, not raised, so its docstring field is ``:warns``.

    ``:raises UserWarning:`` put ``HumanVibrationWarning`` in the exceptions
    table of the API reference under the name of its base class, where a
    reader looking for what to filter found a class that filters every
    advisory; ``:warns <Topic>Warning:`` gives it its own table, by name.
    """
    import re

    field = re.compile(r":raises\s+[\w.~`:]*Warning\b")
    found = [
        f"{path.relative_to(SRC).as_posix()}:{number}"
        for path in sorted(SRC.rglob("*.py"))
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if field.search(line)
    ]
    assert not found, "warnings documented as raised:\n  " + "\n  ".join(found)


#: The start of a field of a docstring's field list: its kind and its name. A
#: role that opens a line (``:class:`X```) is no field.
_FIELD = re.compile(r"^:(?P<kind>\w+)(?:\s+(?P<name>[^:`]+))?:(?!`)")


#: A warning's class, by the name every warning of the package ends with.
_WARNING_CLASS = re.compile(r"\b(\w+Warning)\b")

#: The verb or the noun that says a warning is emitted, its class unnamed.
_WARNING_WORD = re.compile(r"\b(warn(?:s|ed|ings?)?)\b", re.IGNORECASE)


def _raises_findings(doc: str, first_line: int, where: str) -> list[str]:
    """Each line of a ``:raises`` field of *doc* that names a warning or says one.

    A field runs from its ``:kind ...:`` line over every line indented
    deeper than it, a line that opens with a role such as ``:class:`` and
    a further paragraph after a blank line among them. It ends at a line
    no deeper than its own that opens another field or none, as the prose
    after the field list does.

    :param doc: A docstring, as written, its indentation kept.
    :param first_line: The line of the module the docstring opens on.
    :param where: How a finding names the module.
    :return: ``<where>:<line> <exception> names <Warning>`` for a warning's
        class, ``<where>:<line> <exception> says <word>`` for the word.
    """
    found: list[str] = []
    kind = name = ""
    indent = 0
    for offset, line in enumerate(doc.splitlines()):
        text = line.strip()
        if not text:
            continue
        depth = len(line) - len(line.lstrip())
        field = _FIELD.match(text)
        if field and (not kind or depth <= indent):
            kind, name = field["kind"], (field["name"] or "").strip()
            indent = depth
            text = text[field.end() :]
        elif depth <= indent:
            kind = ""
        if kind != "raises":
            continue
        at = f"{where}:{first_line + offset} {name}"
        found.extend(f"{at} names {cls}" for cls in _WARNING_CLASS.findall(text))
        found.extend(f"{at} says {word}" for word in _WARNING_WORD.findall(text))
    return found


def raises_fields_naming_a_warning(source: str, where: str) -> list[str]:
    """Each ``:raises`` field of *source*'s docstrings whose text names or says a warning.

    The field's text is read as :func:`_raises_findings` bounds it; a
    warning's class or the word ``warn``, ``warns``, ``warned``, ``warning``
    or ``warnings`` anywhere in it is a finding.

    :param source: The text of a Python module.
    :param where: How a finding names the module.
    :return: One line per finding, as :func:`_raises_findings` words it.
    """
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
            continue
        doc = ast.get_docstring(node, clean=False)
        if doc and node.body:
            found.extend(_raises_findings(doc, node.body[0].lineno, where))
    return found


def test_a_raises_field_never_names_a_warning() -> None:
    """A warning a call may emit has its own ``:warns`` field, never a clause of a ``:raises`` one.

    The FDTD engines, the simulation functions, the video writers and the
    backend loader said under ``:raises ComputeDeviceError:`` that with
    ``fallback=True`` the run warns with ``ComputeFallbackWarning``; the API
    reference then listed the warning in no table of warnings, where a
    reader looking for what to filter looks.
    """
    found = [
        finding
        for path in sorted(SRC.rglob("*.py"))
        if "warn" in (text := path.read_text(encoding="utf-8")).lower()
        for finding in raises_fields_naming_a_warning(
            text, path.relative_to(SRC).as_posix()
        )
    ]
    assert not found, "warnings named under :raises:\n  " + "\n  ".join(found)


def test_the_raises_field_reader_ends_a_field_where_the_field_list_does() -> None:
    """A warning named in prose after the field list, or under ``:warns``, is no finding."""
    source = (
        "def f():\n"
        '    """Lead.\n'
        "\n"
        "    :raises ValueError: for a bad level; a quiet one warns with\n"
        "        :class:`LevelWarning` instead.\n"
        "    :warns OtherWarning: when it is late.\n"
        "\n"
        "    Outside its range it runs, and a :class:`RangeWarning` says so.\n"
        '    """\n'
    )
    assert raises_fields_naming_a_warning(source, "m.py") == [
        "m.py:4 ValueError says warns",
        "m.py:5 ValueError names LevelWarning",
    ]


def test_the_raises_field_reader_reads_every_paragraph_of_a_field() -> None:
    """A warning named in a later paragraph of a ``:raises`` field is a finding.

    The reader ended a field at its first blank line, so a field written in
    two paragraphs, as the package writes some, hid a warning in its second.
    """
    source = (
        "def f():\n"
        '    """Lead.\n'
        "\n"
        "    :raises ValueError: for a bad level.\n"
        "\n"
        "        A quiet one is let through with a :class:`LevelWarning`.\n"
        "    :returns: The level.\n"
        '    """\n'
    )
    assert raises_fields_naming_a_warning(source, "m.py") == [
        "m.py:6 ValueError names LevelWarning"
    ]


def test_the_raises_field_reader_finds_a_warning_its_class_unnamed() -> None:
    """A ``:raises`` field that says a call warns, naming no class, is a finding.

    The reader looked only for a name ending in ``Warning``, so a field
    that said the run warns and goes on, without the class, passed.
    """
    source = (
        "def f():\n"
        '    """Lead.\n'
        "\n"
        "    :raises ValueError: for a bad level, unless ``quiet``, when the\n"
        "        call only warns.\n"
        '    """\n'
    )
    assert raises_fields_naming_a_warning(source, "m.py") == [
        "m.py:5 ValueError says warns"
    ]


def test_the_raises_field_reader_reads_the_plural_of_the_word() -> None:
    """A ``:raises`` field that says a call emits warnings is a finding too.

    The word was read as ``warn``, ``warns``, ``warned`` and ``warning``, so
    a field that said the run goes on with its warnings, in the plural and
    with no class, passed; and a module was read only when it held the
    capitalised ``Warning`` somewhere, so a module that wrote the word in
    lower case alone was not read at all.
    """
    source = (
        "def f():\n"
        '    """Lead.\n'
        "\n"
        "    :raises ValueError: for a bad level; a quiet one passes with two\n"
        "        warnings.\n"
        '    """\n'
    )
    assert raises_fields_naming_a_warning(source, "m.py") == [
        "m.py:5 ValueError says warnings"
    ]


#: Logger calls louder than INFO: an advisory is a warning (A52), and a
#: logger at WARNING or above prints to standard error by default.
_LOUD = frozenset({"warning", "warn", "error", "critical", "exception", "fatal", "log"})
#: Calls that configure logging, which is the caller's business.
_CONFIGURING = frozenset(
    {
        "basicConfig",
        "addHandler",
        "removeHandler",
        "addFilter",
        "removeFilter",
        "setLevel",
        "dictConfig",
        "fileConfig",
    }
)


def _logging_imports(tree: ast.AST) -> dict[str, str]:
    """Each name *tree* binds to ``logging`` or to a member of it.

    The value is the dotted name the bound name stands for.
    """
    names = {"logging": "logging"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(
                (alias.asname, alias.name) if alias.asname else ("logging", "logging")
                for alias in node.names
                if alias.name.split(".")[0] == "logging"
            )
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and (node.module or "").split(".")[0] == "logging"
        ):
            names.update(
                (alias.asname or alias.name, f"{node.module}.{alias.name}")
                for alias in node.names
            )
    return names


def _package_imports(tree: ast.AST) -> dict[str, str]:
    """Each name *tree* binds by importing from the package, with its name there.

    A relative import is one from the package. ``import phonometry.x`` binds
    ``phonometry``, and ``import phonometry.x as y`` binds ``y`` to ``x``.
    """
    names: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (
            node.level > 0 or (node.module or "").split(".")[0] == "phonometry"
        ):
            names.update(
                (alias.asname or alias.name, alias.name) for alias in node.names
            )
        elif isinstance(node, ast.Import):
            names.update(
                (alias.asname, alias.name.rpartition(".")[2])
                if alias.asname
                else ("phonometry", "phonometry")
                for alias in node.names
                if alias.name.split(".")[0] == "phonometry"
            )
    return names


def _dotted(expression: ast.expr, names: dict[str, str]) -> str | None:
    """The dotted name *expression* spells, its first name read through *names*.

    ``None`` when *expression* is not a dotted name.
    """
    if isinstance(expression, ast.Name):
        return names.get(expression.id, expression.id)
    if isinstance(expression, ast.Attribute):
        owner = _dotted(expression.value, names)
        return None if owner is None else f"{owner}.{expression.attr}"
    return None


def _first_name(expression: ast.expr) -> str | None:
    """The name a chain of attributes *expression* starts from, or ``None``."""
    while isinstance(expression, ast.Attribute):
        expression = expression.value
    return expression.id if isinstance(expression, ast.Name) else None


def _takes_a_logger(node: ast.AST | None, names: dict[str, str]) -> TypeGuard[ast.Call]:
    """Whether *node* calls ``logging.getLogger``, however the module spells it."""
    return (
        isinstance(node, ast.Call) and _dotted(node.func, names) == "logging.getLogger"
    )


def _names_a_library_logger(call: ast.Call) -> bool:
    """Whether a ``getLogger`` *call* names ``phonometry`` or a logger under it."""
    name = next(
        (keyword.value for keyword in call.keywords if keyword.arg == "name"),
        call.args[0] if call.args else None,
    )
    return (
        isinstance(name, ast.Constant)
        and isinstance(name.value, str)
        and name.value.split(".")[0] == "phonometry"
    )


@dataclasses.dataclass
class _Loggers:
    """What one module holds as a logger.

    ``names`` are its imports of ``logging``, ``imported`` the names it
    imports from the package (each with its name there), ``shared`` the names
    the package's modules bind to a logger, and ``held`` the expressions that
    hold a logger in this module.
    """

    names: dict[str, str]
    imported: dict[str, str]
    shared: frozenset[str]
    held: set[str] = dataclasses.field(default_factory=set)

    def holds(self, expression: ast.expr) -> bool:
        """Whether *expression* is a logger.

        It is when this module holds it, when it takes one from
        ``getLogger``, when it is the ``getChild`` of one, or when it is a
        logger another module binds, read through the module it was imported
        with (``client._LOG``).
        """
        if ast.unparse(expression) in self.held or _takes_a_logger(
            expression, self.names
        ):
            return True
        if isinstance(expression, ast.Call):
            return (
                isinstance(expression.func, ast.Attribute)
                and expression.func.attr == "getChild"
                and self.holds(expression.func.value)
            )
        return (
            isinstance(expression, ast.Attribute)
            and expression.attr in self.shared
            and _first_name(expression.value) in self.imported
        )

    def reaches_into(self, expression: ast.expr) -> bool:
        """Whether *expression* is a part of a logger or of ``logging``.

        A part is reached through an attribute or an index: ``_LOG.handlers``,
        ``_LOG.handlers[:]``, ``logging.raiseExceptions``.
        """
        while isinstance(expression, (ast.Attribute, ast.Subscript)):
            expression = expression.value
            if self.holds(expression) or _dotted(expression, self.names) == "logging":
                return True
        return False


def _read_loggers(tree: ast.AST, shared: frozenset[str]) -> _Loggers:
    """Every logger *tree* holds, followed through its assignments.

    A name imported from the package is a logger when the package binds it to
    one. An assignment whose value is a logger binds its targets to one, until
    no assignment adds one more (an alias of an alias, a child of a child). A
    logger bound in a class body is held as ``self.<name>``, ``cls.<name>``
    and ``<Class>.<name>`` too.
    """
    imported = _package_imports(tree)
    loggers = _Loggers(_logging_imports(tree), imported, shared)
    loggers.held.update(name for name, there in imported.items() if there in shared)
    classes = {
        id(statement): node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        for statement in node.body
    }
    assignments = [
        (node.targets if isinstance(node, ast.Assign) else [node.target], node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    grown = True
    while grown:
        bound = {
            f"{owner}{ast.unparse(target)}"
            for targets, node in assignments
            if node.value is not None and loggers.holds(node.value)
            for target in targets
            for owner in (
                ("", "self.", "cls.", f"{classes[id(node)]}.")
                if id(node) in classes
                else ("",)
            )
        }
        grown = not bound <= loggers.held
        loggers.held |= bound
    return loggers


def _logging_set_by(statement: ast.stmt, loggers: _Loggers) -> str | None:
    """The part of a logger or of ``logging`` *statement* sets or deletes.

    ``None`` when it changes neither.
    """
    if isinstance(statement, ast.Delete):
        verb, targets = "deletes", statement.targets
    elif isinstance(statement, ast.Assign):
        verb, targets = "sets", statement.targets
    elif isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
        verb, targets = "sets", [statement.target]
    else:
        return None
    return next(
        (
            f"{verb} {ast.unparse(target)}"
            for target in targets
            if loggers.reaches_into(target)
        ),
        None,
    )


def _logging_misuse_at(node: ast.AST, loggers: _Loggers) -> str | None:
    """What *node* does that the logging rule refuses, or ``None``."""
    if isinstance(node, ast.stmt):
        return _logging_set_by(node, loggers)
    if not isinstance(node, ast.Call):
        return None
    function = _dotted(node.func, loggers.names)
    if function is not None and function.startswith("logging."):
        return None if function == "logging.getLogger" else f"calls {function}"
    if not isinstance(node.func, ast.Attribute):
        return None
    owner, attribute = node.func.value, node.func.attr
    if loggers.holds(owner):
        loud = attribute in _LOUD | _CONFIGURING
        return f"calls {ast.unparse(node.func)}" if loud else None
    if loggers.reaches_into(owner):
        return f"calls {ast.unparse(node.func)}"
    if attribute in _CONFIGURING:
        return f"configures logging with {attribute}"
    return None


def logging_misuse(
    source: str, where: str, *, shared_loggers: frozenset[str] = frozenset()
) -> list[str]:
    """Each place in *source* that logs louder than INFO, configures logging, or uses a logger not the library's.

    The source is read through its imports: an alias of ``logging``, or a name
    imported from it, is the call it stands for, and a name imported from the
    package that the package binds to a logger (*shared_loggers*, from
    :func:`shared_loggers`) is a logger here too. A logger is followed through
    every assignment (see :func:`_read_loggers`); calling into one, or setting
    or deleting a part of one or of ``logging``, configures logging. The places
    come in the order of the source.
    """
    tree = ast.parse(source)
    loggers = _read_loggers(tree, shared_loggers)
    found = [
        (node.lineno, "takes a logger that is not phonometry's")
        for node in ast.walk(tree)
        if _takes_a_logger(node, loggers.names) and not _names_a_library_logger(node)
    ]
    found.extend(
        (node.lineno, offence)
        for node in ast.walk(tree)
        if isinstance(node, (ast.stmt, ast.expr))
        and (offence := _logging_misuse_at(node, loggers))
    )
    return [f"{where}:{line} {what}" for line, what in sorted(found)]


def _may_hold_a_logger(source: str, shared: frozenset[str]) -> bool:
    """Whether *source* names ``logging`` or a logger the package binds.

    A module that names neither can neither take a logger nor import one.
    """
    return "logging" in source or any(name in source for name in shared)


def shared_loggers(sources: list[str]) -> frozenset[str]:
    """The names the modules in *sources* bind to a logger at their top level.

    A module that imports a logger from another binds it too, under its own
    name, so the names are read again until no module adds one.
    """
    shared: frozenset[str] = frozenset()
    while True:
        bound: set[str] = set()
        for source in sources:
            if not _may_hold_a_logger(source, shared):
                continue
            tree = ast.parse(source)
            held = _read_loggers(tree, shared).held
            bound.update(
                name
                for statement in tree.body
                if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.ImportFrom))
                for name in _top_level_names(statement)
                if name in held
            )
        if bound <= shared:
            return shared
        shared |= bound


def _top_level_names(
    statement: ast.Assign | ast.AnnAssign | ast.ImportFrom,
) -> list[str]:
    """The names a top-level assignment or import *statement* binds."""
    if isinstance(statement, ast.ImportFrom):
        return [alias.asname or alias.name for alias in statement.names]
    targets = (
        statement.targets if isinstance(statement, ast.Assign) else [statement.target]
    )
    return [target.id for target in targets if isinstance(target, ast.Name)]


def test_the_library_logs_quietly_to_loggers_of_its_own() -> None:
    sources = {
        path.relative_to(SRC).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(SRC.rglob("*.py"))
    }
    shared = shared_loggers(list(sources.values()))
    found = [
        offence
        for where, text in sources.items()
        if _may_hold_a_logger(text, shared)
        for offence in logging_misuse(text, where, shared_loggers=shared)
    ]
    assert not found, "logging the library must not do:\n  " + "\n  ".join(found)


def test_the_logging_rule_reads_a_loud_logger() -> None:
    source = (
        "import logging\n"
        "_LOG = logging.getLogger('phonometry.simulation')\n"
        "_OTHER = logging.getLogger(__name__ + 'x')\n"
        "def f():\n"
        "    _LOG.warning('slow')\n"
        "    _LOG.addHandler(None)\n"
        "    logging.basicConfig()\n"
        "    _LOG.info('fine')\n"
    )
    assert logging_misuse(source, "x.py") == [
        "x.py:3 takes a logger that is not phonometry's",
        "x.py:5 calls _LOG.warning",
        "x.py:6 calls _LOG.addHandler",
        "x.py:7 calls logging.basicConfig",
    ]


def test_the_logging_rule_reads_every_spelling_of_a_logger() -> None:
    """A logger is read however the module spells it, and nothing else is.

    An alias of ``logging``, a name imported from it, a logger imported from
    another module (by name or through its module), a logger held by an
    annotated name, an attribute or a class, an alias, a child, a logger used
    where it is taken and a call written over several lines are each read as
    the call they stand for. A call named like a loud one on anything else
    (``np.log``, ``warnings.warn``, the ``error`` of a list of issues) is its
    own business.
    """
    source = (
        "import logging as log\n"
        "import warnings\n"
        "import numpy as np\n"
        "from logging import getLogger, warning as warn_root\n"
        "from . import client\n"
        "from .client import _LOG\n"
        "_OWN: log.Logger = getLogger(name='phonometry.io')\n"
        "_ROOT = log.getLogger()\n"
        "class Run:\n"
        "    _log = _OWN.getChild('run')\n"
        "    def __init__(self, issues):\n"
        "        self.issues = issues\n"
        "        self.held = log.getLogger('phonometry.simulation')\n"
        "        self.held.error(\n"
        "            'slow'\n"
        "        )\n"
        "        getLogger('phonometry.io').critical('lost')\n"
        "        warn_root('lost')\n"
        "        _LOG.warning('slow')\n"
        "        client._LOG.error('lost')\n"
        "        self._log.exception('lost')\n"
        "        alias = _OWN\n"
        "        alias.fatal('lost')\n"
        "        _OWN.debug('fine')\n"
        "        self.held.info('fine')\n"
        "        getLogger('phonometry.io').info('fine')\n"
        "        np.log(2.0)\n"
        "        warnings.warn('x', RuntimeWarning, stacklevel=1)\n"
        "        self.issues.error('row 3', 'fine')\n"
        "    @classmethod\n"
        "    def make(cls):\n"
        "        cls._log.warning('slow')\n"
    )
    assert logging_misuse(source, "x.py", shared_loggers=frozenset({"_LOG"})) == [
        "x.py:8 takes a logger that is not phonometry's",
        "x.py:14 calls self.held.error",
        "x.py:17 calls getLogger('phonometry.io').critical",
        "x.py:18 calls logging.warning",
        "x.py:19 calls _LOG.warning",
        "x.py:20 calls client._LOG.error",
        "x.py:21 calls self._log.exception",
        "x.py:23 calls alias.fatal",
        "x.py:32 calls cls._log.warning",
    ]


def test_the_logging_rule_reads_every_way_of_configuring() -> None:
    source = (
        "import logging\n"
        "import logging.config\n"
        "_LOG = logging.getLogger('phonometry.simulation')\n"
        "def configure(handler):\n"
        "    _LOG.propagate = False\n"
        "    _LOG.handlers.clear()\n"
        "    _LOG.handlers[:] = []\n"
        "    del _LOG.filters[:]\n"
        "    _LOG.removeHandler(handler)\n"
        "    _LOG.level += 10\n"
        "    logging.raiseExceptions = False\n"
        "    logging.lastResort = None\n"
        "    logging.root.handlers = []\n"
        "    logging.config.dictConfig({})\n"
        "    handler.setLevel(logging.DEBUG)\n"
    )
    assert logging_misuse(source, "x.py") == [
        "x.py:5 sets _LOG.propagate",
        "x.py:6 calls _LOG.handlers.clear",
        "x.py:7 sets _LOG.handlers[:]",
        "x.py:8 deletes _LOG.filters[:]",
        "x.py:9 calls _LOG.removeHandler",
        "x.py:10 sets _LOG.level",
        "x.py:11 sets logging.raiseExceptions",
        "x.py:12 sets logging.lastResort",
        "x.py:13 sets logging.root.handlers",
        "x.py:14 calls logging.config.dictConfig",
        "x.py:15 configures logging with setLevel",
    ]


def test_the_logging_rule_follows_a_logger_from_module_to_module() -> None:
    """A logger imported, renamed and imported again is still the library's.

    A name no module binds to a logger stays its own business.
    """
    sources = [
        "import logging\n_LOG = logging.getLogger('phonometry.simulation')\n",
        (
            "from .client import _LOG as remote_log\n"
            "node_log = remote_log.getChild('node')\n"
        ),
        "from .node import node_log\ndef f():\n    node_log.error('lost')\n",
        "from .reader import log\nlog.error('a reader of its own')\n",
    ]
    shared = shared_loggers(sources)
    assert shared == {"_LOG", "remote_log", "node_log"}
    assert logging_misuse(sources[2], "x.py", shared_loggers=shared) == [
        "x.py:3 calls node_log.error"
    ]
    assert logging_misuse(sources[3], "y.py", shared_loggers=shared) == []


# --------------------------------------------------------------------------- #
# Records: what their fields are typed, and that they travel
# --------------------------------------------------------------------------- #
#: Published record fields typed ``Any`` on purpose, keyed by record and
#: field, each with the reason.
ANY_FIELD_EXEMPT: dict[tuple[str, str], str] = {}

#: What ``Any`` is, as the reader of the annotations resolves it.
_ANY = frozenset({"typing.Any", "typing_extensions.Any"})

#: What a ``dict`` is, written bare, generic or through ``typing``.
_DICT = frozenset({"builtins.dict", "typing.Dict"})


def _published_records() -> dict[str, type]:
    return {
        name: cls
        for name, cls in _published_classes().items()
        if dataclasses.is_dataclass(cls)
    }


@functools.cache
def _record_reader() -> tuple[return_overloads.Package, cpa.Annotations]:
    """The package's annotations, as ``scripts/check_parameter_annotations.py`` reads them."""
    package = return_overloads.Package(python_files([], SRC), SRC)
    return package, cpa.Annotations(package)


def _fields_naming(wanted: frozenset[str]) -> dict[tuple[str, str], list[str]]:
    """The published record fields whose annotation names one of *wanted*.

    Read from the source through the annotations reader, which spells out an
    alias at every level (``Untyped = Any``, ``Table = Dict[str, float]``)
    and reads past the type parameter of a NumPy generic. A published record
    the reader cannot find fails, rather than being read past.
    """
    package, annotations = _record_reader()
    found: dict[tuple[str, str], list[str]] = {}
    for name, cls in _published_records().items():
        dotted = f"{cls.__module__}.{cls.__qualname__}"
        assert dotted in annotations.classes, f"{name}: not read from the source"
        for field in cpa.record_fields(package, annotations, dotted).values():
            named = annotations.named_within(field.module, field.annotation, wanted)
            if named:
                found[(name, field.name)] = named
    return found


def test_no_published_field_is_typed_any() -> None:
    """A field typed ``Any`` tells a reader, and a type checker, nothing (rule A31).

    The type parameter of a numpy generic (``np.integer[Any]``,
    ``NDArray[Any]``) is not the field's type, and is read past; an alias
    of ``Any`` is ``Any``.
    """
    found = set(_fields_naming(_ANY))
    assert found - set(ANY_FIELD_EXEMPT) == set()
    assert set(ANY_FIELD_EXEMPT) - found == set(), "stale ANY_FIELD_EXEMPT entries"


def test_no_published_field_is_typed_dict() -> None:
    """A ``dict`` field is invariant and editable: ``Mapping`` says what it holds.

    A frozen record holds the mapping it was built with read-only, so the
    field is annotated with the read-only supertype, and a typed caller's
    ``dict`` of a narrower key or value type is taken. Bare ``dict``,
    ``dict[...]``, ``typing.Dict`` and an alias of any of them are read
    alike.
    """
    assert _fields_naming(_DICT) == {}


def test_the_field_reader_spells_out_aliases(tmp_path: Path) -> None:
    """An alias of ``Any`` or of ``Dict`` is read as what it stands for."""
    root = tmp_path / "pkg"
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    (root / "api.py").write_text(
        "from dataclasses import dataclass\n"
        "from typing import Any, Dict, Literal\n"
        "import numpy as np\n"
        "from numpy.typing import NDArray\n"
        "Untyped = Any\n"
        "Table = Dict[str, float]\n"
        "@dataclass(frozen=True)\n"
        "class Record:\n"
        "    a: Untyped\n"
        "    b: Table | None\n"
        "    c: tuple[dict, ...]\n"
        "    d: NDArray[Any]\n"
        "    e: Literal['dict', 'Any']\n"
        "    f: np.integer[Any] | None\n",
        encoding="utf-8",
    )
    package = return_overloads.Package(sorted(root.rglob("*.py")), root)
    annotations = cpa.Annotations(package)
    fields = cpa.record_fields(package, annotations, "pkg.api.Record")
    anything = {
        name: annotations.named_within(field.module, field.annotation, _ANY)
        for name, field in fields.items()
    }
    dicts = {
        name: annotations.named_within(field.module, field.annotation, _DICT)
        for name, field in fields.items()
    }
    assert {name for name, named in anything.items() if named} == {"a"}
    assert {name for name, named in dicts.items() if named} == {"b", "c"}


#: The calls of the package that build a read-only mapping.
_PROXY_MAKERS = frozenset({"MappingProxyType", "frozen_rows", "frozen_row"})


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for call in ast.walk(node):
        if isinstance(call, ast.Call):
            func = call.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def _proxy_makers(tree: ast.Module) -> set[str]:
    """The functions of a module that hand back a read-only mapping, transitively."""
    makers = set(_PROXY_MAKERS)
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    grown = True
    while grown:
        grown = False
        for name, function in functions.items():
            if name in makers:
                continue
            returned = [
                value
                for node in ast.walk(function)
                if isinstance(node, ast.Return) and (value := node.value) is not None
            ]
            if any(_called_names(value) & makers for value in returned):
                makers.add(name)
                grown = True
    return makers


def _stores_a_read_only_mapping(cls: type) -> bool:
    """Whether a record's ``__post_init__``, or a method it calls, builds one.

    Read from the source of each class of the package in its hierarchy: a
    call to ``MappingProxyType``, to ``frozen_rows``/``frozen_row``, or to a
    function of the class's module that hands one back.
    """
    import inspect
    import textwrap

    for base in cls.__mro__:
        module = sys.modules.get(base.__module__)
        if module is None or not base.__module__.startswith("phonometry"):
            continue
        if base.__module__ == "phonometry._internal.frozen":
            continue
        try:
            source = textwrap.dedent(inspect.getsource(base))
            module_tree = ast.parse(inspect.getsource(module))
        except (OSError, TypeError):
            continue
        makers = _proxy_makers(module_tree)
        tree = ast.parse(source)
        node = tree.body[0]
        if not isinstance(node, ast.ClassDef):
            continue
        methods = {
            child.name: child
            for child in node.body
            if isinstance(child, ast.FunctionDef)
        }
        todo, seen = ["__post_init__"], set()
        while todo:
            name = todo.pop()
            if name in seen or name not in methods:
                continue
            seen.add(name)
            called = _called_names(methods[name])
            if called & makers:
                return True
            todo.extend(called & set(methods))
    return False


def test_a_record_holding_a_read_only_mapping_travels() -> None:
    """A record that wraps a mapping read-only says how to pickle and copy itself.

    ``MappingProxyType`` can be neither pickled nor deep-copied, so a record
    holding one fails ``pickle.dumps`` (a process pool, a cache) and
    ``copy.deepcopy`` unless it travels as plain dictionaries and wraps them
    again on arrival: ``__reduce__`` returning
    ``phonometry._internal.frozen.reduce_with_plain_rows(self)``. This reads
    the source of the record's own module; a proxy a function of another
    module builds and hands to the record is what
    ``tests/test_record_conversions.py`` catches, by building every
    published record that holds a mapping and sending it both ways.
    """
    missing = sorted(
        name
        for name, cls in _published_records().items()
        if _stores_a_read_only_mapping(cls)
        and not any(
            "__reduce__" in vars(base) for base in cls.__mro__ if base is not object
        )
    )
    assert missing == []


def _is_protocol(node: ast.AST) -> bool:
    return isinstance(node, ast.ClassDef) and any(
        (isinstance(base, ast.Name) and base.id == "Protocol")
        or (isinstance(base, ast.Attribute) and base.attr == "Protocol")
        for base in node.bases
    )


def _protocols() -> list[tuple[str, ast.ClassDef]]:
    found: list[tuple[str, ast.ClassDef]] = []
    for path in _iter_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        found.extend(
            (path.relative_to(SRC).as_posix(), node)
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and _is_protocol(node)
        )
    return found


def test_a_protocol_declares_its_data_members_as_properties() -> None:
    """A frozen record satisfies a protocol whose members it can only be read for.

    A plain annotated attribute in a protocol is settable, and a frozen
    dataclass's field is not, so a type checker refuses every frozen result
    the protocol was written to accept (``enclosure_insertion_loss`` taking a
    ``SoundReductionResult``). A read-only member is a ``@property``.
    """
    offenders = sorted(
        f"{path}:{node.name}.{child.target.id}"
        for path, node in _protocols()
        for child in node.body
        if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name)
    )
    assert offenders == []


def _is_type_checking(test: ast.expr) -> bool:
    return (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
        isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
    )


def _module_getattrs(tree: ast.Module) -> list[tuple[ast.FunctionDef, bool]]:
    """Each module-level ``__getattr__``, with whether the type checker is kept from it."""
    found: list[tuple[ast.FunctionDef, bool]] = []
    for statement in tree.body:
        if isinstance(statement, ast.FunctionDef) and statement.name == "__getattr__":
            found.append((statement, False))
        elif isinstance(statement, ast.If):
            hidden = (
                isinstance(statement.test, ast.UnaryOp)
                and isinstance(statement.test.op, ast.Not)
                and _is_type_checking(statement.test.operand)
            )
            found.extend(
                (inner, hidden)
                for inner in statement.body
                if isinstance(inner, ast.FunctionDef) and inner.name == "__getattr__"
            )
    return found


def test_a_module_getattr_is_hidden_from_the_type_checker() -> None:
    """A module ``__getattr__`` sits under ``if not TYPE_CHECKING:``.

    A type checker that sees a module ``__getattr__`` reads every name the
    module lacks through it, so ``phonometry.stpia`` types as ``object`` and
    a misspelling stops being an error. Defined for the running interpreter
    only, it imports lazily as before, and the type checker reads the
    imports the module declares for it.
    """
    offenders = []
    seen = 0
    for path in _iter_modules() + [SRC / "__init__.py"]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node, hidden in _module_getattrs(tree):
            seen += 1
            if not hidden:
                offenders.append(f"{path.relative_to(SRC)}:{node.lineno}")
    assert offenders == []
    assert seen, "the root package's lazy __getattr__ is not read any more"


def test_the_getattr_rule_reads_a_visible_one() -> None:
    visible = ast.parse("def __getattr__(name):\n    raise AttributeError(name)\n")
    hidden = ast.parse(
        "from typing import TYPE_CHECKING\n"
        "if not TYPE_CHECKING:\n"
        "    def __getattr__(name):\n"
        "        raise AttributeError(name)\n"
    )
    assert [flag for _, flag in _module_getattrs(visible)] == [False]
    assert [flag for _, flag in _module_getattrs(hidden)] == [True]


#: The cases mypy checks call by call: each holds an annotation to the forms
#: a caller writes.
STATIC_CASES = SRC.parent.parent / "tests" / "static_typing"

#: The NumPy scalar types a dtype written by position names (``np.int64``).
_SCALAR_TYPE = re.compile(
    r"(u?int\d*|u?intp|float\d*|complex\d*|bool_?|half|c?single|c?double"
    r"|c?longdouble|u?byte|u?short|u?intc|u?long|u?longlong)"
)


def _an_array_of_a_written_dtype(node: ast.expr) -> bool:
    """Whether *node* builds an array whose dtype it writes in place.

    ``np.zeros(4000, dtype=np.int64)``, ``np.array(2, np.int32)`` and
    ``values.astype(np.int64)`` all qualify.
    """
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr == "astype":
        return True
    if any(keyword.arg == "dtype" for keyword in node.keywords):
        return True
    return (
        isinstance(node.func.value, ast.Name)
        and node.func.value.id == "np"
        and any(
            isinstance(argument, ast.Attribute)
            and isinstance(argument.value, ast.Name)
            and argument.value.id == "np"
            and _SCALAR_TYPE.fullmatch(argument.attr) is not None
            for argument in node.args[1:]
        )
    )


def _arrays_of_a_written_dtype_handed_on(tree: ast.AST) -> list[int]:
    """The lines where a call takes such an array as written, not by a name."""
    lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for value in [*node.args, *(keyword.value for keyword in node.keywords)]:
            argument = value.value if isinstance(value, ast.Starred) else value
            if _an_array_of_a_written_dtype(argument):
                lines.append(argument.lineno)
    return sorted(lines)


def test_a_static_case_names_an_array_of_a_given_dtype_before_the_call() -> None:
    """A static case hands on an integer array by a name typed with its dtype.

    Written in the call, ``np.zeros(4000, dtype=np.int64)`` takes its type
    from the parameter it is handed to: against a floating array mypy picks
    the overload that returns ``NDArray[Any]``, so the case passed however
    narrow the parameter was, and could not catch the narrowing it was
    written for. Named first (``integers: NDArray[np.int64] = ...``), the
    array keeps its dtype and the case fails when the parameter refuses it.
    """
    offenders = [
        f"{path.relative_to(STATIC_CASES)}:{line}"
        for path in sorted(STATIC_CASES.glob("*.py"))
        for line in _arrays_of_a_written_dtype_handed_on(
            ast.parse(path.read_text(encoding="utf-8"))
        )
    ]
    assert offenders == []


def test_the_static_case_rule_reads_an_array_written_in_the_call() -> None:
    written = ast.parse(
        "f(np.zeros(4, dtype=np.int64))\n"
        "f(x, scale=np.array(2, np.int32))\n"
        "f(*values.astype(np.int64))\n"
    )
    named = ast.parse(
        "integers: NDArray[np.int64] = np.zeros(4, dtype=np.int64)\n"
        "f(integers)\n"
        "f(np.zeros(4), np.full(3, 1.0))\n"
    )
    assert _arrays_of_a_written_dtype_handed_on(written) == [1, 2, 3]
    assert _arrays_of_a_written_dtype_handed_on(named) == []


#: The NumPy numbers an annotation takes on their own, as the annotations
#: reader resolves them.
_NUMPY_NUMBER_KINDS = frozenset({"numpy.integer", "numpy.floating"})

#: The Python numbers a sequence of numbers is written with.
_PYTHON_NUMBERS = frozenset({"builtins.int", "builtins.float"})

#: The containers a caller writes, each with the annotations that take it:
#: a list is taken by a ``list`` or a ``Sequence`` and not by a ``tuple``, so
#: the items of a ``tuple`` branch do not make a list of them a valid
#: argument, nor those of a ``set`` branch.
_TAKEN_BY: dict[str, frozenset[str]] = {
    "list": frozenset(
        {
            "builtins.list",
            "typing.List",
            "typing.Sequence",
            "typing.MutableSequence",
            "typing.Iterable",
            "typing.Collection",
            "collections.abc.Sequence",
            "collections.abc.MutableSequence",
            "collections.abc.Iterable",
            "collections.abc.Collection",
        }
    ),
    "tuple": frozenset(
        {
            "builtins.tuple",
            "typing.Tuple",
            "typing.Sequence",
            "typing.Iterable",
            "typing.Collection",
            "collections.abc.Sequence",
            "collections.abc.Iterable",
            "collections.abc.Collection",
        }
    ),
    "set": frozenset(
        {
            "builtins.set",
            "builtins.frozenset",
            "typing.Set",
            "typing.FrozenSet",
            "typing.AbstractSet",
            "typing.Iterable",
            "typing.Collection",
            "collections.abc.Set",
            "collections.abc.Iterable",
            "collections.abc.Collection",
        }
    ),
}


def test_every_container_is_a_list_a_tuple_or_a_set_to_a_caller() -> None:
    """Each container the annotations reader knows takes a list, a tuple or a set."""
    assert set().union(*_TAKEN_BY.values()) == cpa._CONTAINERS


def _numbers_left_out_of_sequences(
    annotations: cpa.Annotations,
    module: str,
    node: ast.expr | None,
    taken: frozenset[str | None] = frozenset(),
) -> list[str]:
    """The sequences of an annotation that refuse a NumPy number it takes alone.

    ``int | np.integer[Any] | Sequence[int]`` takes one ``np.int64`` and
    refuses a list of them, to a type checker, where a body that reads each
    item as a number takes both. The sequences of one union are read
    together (``Sequence[float] | Sequence[np.floating[Any]]`` holds the
    NumPy float), as far as they take the same container a caller writes
    (a ``tuple[np.integer[Any], ...]`` beside ``Sequence[int]`` takes a
    tuple of NumPy integers and not a list of them, :data:`_TAKEN_BY`), a
    nested sequence holds what the sequence around it takes alone (*taken*),
    and a mapping's values are read as an annotation of their own.
    """
    members = annotations.members(module, node)
    alone = taken | (
        {annotations.resolve(where, member) for where, member in members}
        & _NUMPY_NUMBER_KINDS
    )
    found: list[str] = []
    items: list[tuple[str, ast.expr]] = []
    written: list[str] = []
    kinds_of: dict[str, set[str | None]] = {}
    for where, member in members:
        dotted = annotations.resolve(where, member)
        held = [item for item in cpa._items(member) if not cpa._is_ellipsis(item)]
        if dotted in cpa._MAPPINGS and held:
            found += _numbers_left_out_of_sequences(annotations, where, held[-1])
        elif dotted in cpa._CONTAINERS:
            items += [(where, item) for item in held]
            written.append(ast.unparse(member))
            kinds = {
                annotations.resolve(inner, number)
                for item in held
                for inner, number in annotations.members(where, item)
            }
            for container, takers in _TAKEN_BY.items():
                if dotted in takers:
                    kinds_of.setdefault(container, set()).update(kinds)
    if any(kinds & _PYTHON_NUMBERS and alone - kinds for kinds in kinds_of.values()):
        found.append(" | ".join(written))
    for where, item in items:
        found += _numbers_left_out_of_sequences(annotations, where, item, alone)
    return found


def _annotations_leaving_numbers_out(
    package: return_overloads.Package, annotations: cpa.Annotations
) -> list[str]:
    """Every parameter and annotated name of *package* whose sequences refuse a NumPy number it takes alone."""
    found: list[str] = []
    for module, tree in sorted(package.trees.items()):
        for node in ast.walk(tree):
            if isinstance(node, ast.arg):
                name, annotation = node.arg, node.annotation
            elif isinstance(node, ast.AnnAssign):
                name, annotation = ast.unparse(node.target), node.annotation
            else:
                continue
            found += [
                f"{module}:{node.lineno}: {name}: {sequence}"
                for sequence in _numbers_left_out_of_sequences(
                    annotations, module, annotation
                )
            ]
    return found


def test_a_numpy_number_taken_alone_is_taken_in_a_sequence_too() -> None:
    """An annotation that takes ``np.int64`` alone takes a list of them beside it.

    ``Signal.pick(channels: int | np.integer[Any] | Sequence[int])`` took one
    NumPy channel index and, for mypy, refused a list of them, and the
    impedance profile of ``FDTDBoundaries`` took a NumPy float alone and a
    ``Sequence[float]`` beside it, while each call ran. A NumPy number a
    caller may pass alone is one a caller collects in a list.
    """
    package, annotations = _record_reader()
    assert _annotations_leaving_numbers_out(package, annotations) == []


def test_the_sequence_rule_reads_a_union_whole(tmp_path: Path) -> None:
    """Aliases are spelt out, sibling sequences read together, mapping values read too."""
    root = tmp_path / "pkg"
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    (root / "api.py").write_text(
        "from collections.abc import Mapping, Sequence\n"
        "from typing import Any\n"
        "import numpy as np\n"
        "from numpy.typing import NDArray\n"
        "Index = int | np.integer[Any]\n"
        "Values = Sequence[float] | Sequence[np.floating[Any]] | NDArray[Any]\n"
        "def pick(channels: Index | Sequence[int]) -> None: ...\n"
        "def profile(sides: Mapping[str, float | np.floating[Any] | list[float]]) -> None: ...\n"
        "def nested(rows: np.integer[Any] | Sequence[Sequence[int]]) -> None: ...\n"
        "def kept(channels: Index | Sequence[int | np.integer[Any]]) -> None: ...\n"
        "def siblings(values: float | np.floating[Any] | Values) -> None: ...\n"
        "def plain(values: float | Sequence[float]) -> None: ...\n"
        "def tupled(channels: Index | tuple[np.integer[Any], ...] | Sequence[int]) -> None: ...\n"
        "def fixed(pair: np.floating[Any] | tuple[float, float]) -> None: ...\n"
        "def listed(channels: Index | list[np.integer[Any]] | Sequence[int]) -> None: ...\n",
        encoding="utf-8",
    )
    package = return_overloads.Package(sorted(root.rglob("*.py")), root)
    annotations = cpa.Annotations(package)
    assert _annotations_leaving_numbers_out(package, annotations) == [
        "pkg.api:7: channels: Sequence[int]",
        "pkg.api:8: sides: list[float]",
        "pkg.api:9: rows: Sequence[int]",
        "pkg.api:13: channels: tuple[np.integer[Any], ...] | Sequence[int]",
        "pkg.api:14: pair: tuple[float, float]",
        "pkg.api:15: channels: list[np.integer[Any]] | Sequence[int]",
    ]
