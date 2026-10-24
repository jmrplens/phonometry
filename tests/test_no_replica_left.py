#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The documentation clips have one road to a GPU, the public one.

They used to step a replica of the acoustic engine, sent to the GPU host by
scripts of their own and configured by ``PHONO_GPU_*`` settings in ``.env``.
The clips now step ``phonometry.simulation`` on the device the registry
records, and a node is named in the hosts file. This holds the old road
closed: no module imports the replica or its transport, and no file a
developer reads or runs names one of its settings.
"""

from __future__ import annotations

import ast
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[1]

_GONE_MODULES = frozenset(
    {"fdtd2d", "fdtd_dispatch", "fdtd_gpu", "fdtd_gpu_remote", "job_runner"}
)
_GONE_SETTINGS = (
    "PHONO_GPU_HOST",
    "PHONO_GPU_USER",
    "PHONO_GPU_NAME",
    "PHONO_GPU_DOCKER_IMAGE",
    "PHONO_GPU_WORKDIR",
    "PHONO_GPU_ENCODE",
    "PHONO_GPU_FFMPEG_IMAGE",
)


def _imported(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_no_module_imports_the_replica_or_its_transport() -> None:
    found = []
    for folder in ("src", "scripts", "tests"):
        for path in (_ROOT / folder).rglob("*.py"):
            hit = _imported(ast.parse(path.read_text(encoding="utf-8"))) & _GONE_MODULES
            if hit:
                found.append(f"{path.relative_to(_ROOT)}: {sorted(hit)}")
    assert not found, "\n".join(found)


def test_no_file_a_developer_reads_names_an_old_gpu_setting() -> None:
    paths = [
        _ROOT / "Makefile",
        _ROOT / ".env.example",
        _ROOT / "CONTRIBUTING.md",
        *(_ROOT / ".github" / "workflows").glob("*.yml"),
        *(_ROOT / "scripts").rglob("*.py"),
        *(_ROOT / "docs").rglob("*.md"),
        *(_ROOT / "site" / "src" / "content").rglob("*.md*"),
    ]
    found = [
        f"{path.relative_to(_ROOT)}: {name}"
        for path in paths
        if "superpowers" not in path.parts
        for name in _GONE_SETTINGS
        if name in path.read_text(encoding="utf-8")
    ]
    assert not found, "\n".join(found)
