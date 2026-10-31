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
from typing import TypeGuard

import pytest

_SCRIPTS = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_parameter_annotations as cpa
import check_return_overloads as return_overloads
from ast_scan import python_files

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
    from phonometry._internal.types import BandFraction

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


def test_no_source_compares_a_float_for_equality() -> None:
    """Floating point does not answer `==`, and the tree had stopped asking.

    `array_directivity_index` reintroduced the one case: its sine-integral
    footprint guarded a removable singularity with ``x == 0.0``, which an
    endfire steer reaches exactly and nothing near it does. Writing the term as
    ``x sinc(x)^2`` removes both the singularity and the comparison. Nothing in
    the repository could see the regression; SonarCloud reported it after the
    branch was already pushed, so the class is closed here instead.
    """
    import ast
    import pathlib

    equalities: list[str] = []
    for path in sorted(pathlib.Path("src/phonometry").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            for operator, right in zip(node.ops, node.comparators, strict=True):
                if not isinstance(operator, (ast.Eq, ast.NotEq)):
                    continue
                operands = (node.left, right)
                if any(
                    isinstance(side, ast.Constant) and isinstance(side.value, float)
                    for side in operands
                ):
                    equalities.append(
                        f"{path.relative_to('src')}:{node.lineno} {ast.unparse(node)}"
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


#: Protocols of the package that declare a settable member on purpose, keyed by
#: file and protocol, each with the reason.
PROTOCOL_ATTRIBUTE_EXEMPT: dict[tuple[str, str], str] = {
    ("simulation/fdtd.py", "_PressureEngine"): (
        "a private engine contract in a file scripts/gpu_parity.py fingerprints, "
        "whose _backend is assigned by the engine that holds it"
    ),
}


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
        if isinstance(child, ast.AnnAssign)
        and isinstance(child.target, ast.Name)
        and (path, node.name) not in PROTOCOL_ATTRIBUTE_EXEMPT
    )
    assert offenders == []
    protocols = {(path, node.name) for path, node in _protocols()}
    assert set(PROTOCOL_ATTRIBUTE_EXEMPT) <= protocols, "stale exemption"


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
