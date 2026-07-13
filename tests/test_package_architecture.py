#  Copyright (c) 2026. Jose M. Requena-Plens
"""Architecture rules for the phonometry package layout (Phase 1 overhaul).

Static (ast-based) enforcement of the dependency policy between the domain
subpackages, plus a fresh-interpreter smoke import per subpackage. The edge
whitelist is the contract from the modularization plan: keep it tight; adding
an edge is an explicit, reviewed decision.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "phonometry"

#: Cross-package edges allowed IN ADDITION to `pkg -> pkg` (internal),
#: `* -> _internal` and `* -> metrology`. "root" = modules still at the top
#: level of the package (shrinks to the facade set as the migration proceeds).
ALLOWED_EDGES: set[tuple[str, str]] = {
    ("environmental", "materials"),   # air_absorption -> ISO 354 helpers
    ("aircraft", "environmental"),    # atmospheric absorption reuse
    ("vibration", "hearing"),         # multiple-shock SEXES tables
    ("hearing", "metrology"),         # sti filter reuse
    ("psychoacoustics", "metrology"),
    ("room", "metrology"),
}


def _package_of(path: Path) -> str:
    rel = path.relative_to(SRC)
    return rel.parts[0] if len(rel.parts) > 1 else "root"


def _iter_modules() -> list[Path]:
    return [p for p in SRC.rglob("*.py") if p.name != "__init__.py" or p.parent != SRC]


def _edges() -> set[tuple[str, str, str]]:
    """(from_pkg, to_pkg, 'file: import') for every relative import in src."""
    out: set[tuple[str, str, str]] = set()
    for path in _iter_modules():
        pkg = _package_of(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.level == 0:
                continue
            target = node.module or ""
            head = target.split(".")[0] if target else ""
            if node.level == 1 and pkg == "root":
                to_pkg = head if (SRC / head).is_dir() else "root"
            elif node.level == 1:
                to_pkg = pkg  # sibling inside the same subpackage
            else:  # level == 2 from inside a subpackage
                to_pkg = head if (SRC / head).is_dir() else "root"
            out.add((pkg, to_pkg, f"{path.relative_to(SRC)}: {ast.dump(node)[:60]}"))
    return out


def test_internal_imports_no_domain_code() -> None:
    for frm, to, where in _edges():
        if frm == "_internal":
            assert to == "_internal", f"_internal must stay leaf-level: {where}"


def test_cross_package_edges_are_whitelisted() -> None:
    violations = []
    for frm, to, where in _edges():
        if frm == to or to in ("_internal", "root") or frm in ("root", "_plot"):
            # root modules are unrestricted during the migration; the facade
            # (__init__, _compat) legitimately imports everything.
            continue
        if to == "metrology":
            continue
        if to == "_plot":
            # lazy .plot() imports only; enforced structurally by the fact
            # that _plot modules import domain classes under TYPE_CHECKING.
            continue
        if (frm, to) not in ALLOWED_EDGES:
            violations.append(f"{frm} -> {to} ({where})")
    assert not violations, "unlisted cross-package imports:\n" + "\n".join(violations)


def test_plot_modules_only_type_check_domain_imports() -> None:
    plot_dir = SRC / "_plot"
    if not plot_dir.is_dir():
        pytest.skip("_plot not created yet")
    for path in plot_dir.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:  # module level only
            if isinstance(node, ast.ImportFrom) and node.level == 2:
                pytest.fail(f"{path.name}: module-level import of domain code "
                            "(must live under TYPE_CHECKING)")


@pytest.mark.parametrize("pkg", sorted(
    p.name for p in SRC.iterdir() if p.is_dir() and not p.name.startswith("__")
))
def test_subpackage_imports_in_fresh_interpreter(pkg: str) -> None:
    subprocess.run(
        [sys.executable, "-c", f"import phonometry.{pkg}"],
        check=True, capture_output=True, timeout=120,
    )
