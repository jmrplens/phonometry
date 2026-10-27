#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The documentation clips have one road to a GPU, the public one.

They used to step a replica of the acoustic engine, sent to the GPU host by
scripts of their own and configured by ``PHONO_GPU_*`` settings in ``.env``.
The clips now step ``phonometry.simulation`` on the device the registry
records, and a node is named in the hosts file. This holds the old road
closed: none of the replica's scripts is back, no module imports one of
them, and no tracked file names a ``PHONO_GPU_`` setting, whatever the
setting is called and wherever the file sits. The changelog is the one
exception: its released entries keep the names they shipped with.
"""

from __future__ import annotations

import ast
import functools
import pathlib
import re
import unicodedata
from typing import TYPE_CHECKING

import child_process
import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_THIS = pathlib.Path(__file__).resolve().relative_to(_ROOT).as_posix()

_GONE_MODULES = frozenset(
    {"fdtd2d", "fdtd_dispatch", "fdtd_gpu", "fdtd_gpu_remote", "job_runner"}
)
#: Where the replica and its transport lived.
_GONE_SCRIPTS = tuple(f"scripts/{name}.py" for name in sorted(_GONE_MODULES))

#: Every setting of the old road began with this prefix, and so does a read
#: of one, whether it spells the whole name or completes it at run time
#: (``f"PHONO_GPU_{key}"``), so the prefix is what is searched for, not a
#: list of names. A brace belongs to the name only as a whole replacement
#: field: the one that closes a shell's ``${PHONO_GPU_HOST}`` does not.
_SETTING = re.compile(r"PHONO_GPU_(?:\w|\{[^{}\s]*\})*")
_SETTING_BYTES = b"PHONO_GPU_"

#: The tracked files that may name one: this guard, which names them to
#: refuse them, and the changelog, the record of what was released with them.
_MAY_NAME = frozenset({_THIS, "CHANGELOG.md"})


def _imported(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def replica_imports(files: Iterable[tuple[str, str]]) -> list[str]:
    """``path: [modules]`` for each file that imports a module of the replica.

    *files* are ``(path, source)`` pairs. An import names the module, so a
    file whose text never does is not parsed. The text is looked at as
    Python reads an identifier, its compatibility characters folded (NFKC):
    ``import`` of a name in fullwidth letters imports the ASCII module.
    """
    found = []
    for name, text in files:
        folded = unicodedata.normalize("NFKC", text)
        if not any(module in folded for module in _GONE_MODULES):
            continue
        hit = _imported(ast.parse(text)) & _GONE_MODULES
        if hit:
            found.append(f"{name}: {sorted(hit)}")
    return found


def _python_sources() -> Iterator[tuple[str, str]]:
    """Each module under src/, scripts/ and tests/, as its path and its source."""
    for folder in ("src", "scripts", "tests"):
        for path in (_ROOT / folder).rglob("*.py"):
            yield path.relative_to(_ROOT).as_posix(), path.read_text(encoding="utf-8")


def replica_scripts(paths: Iterable[str]) -> list[str]:
    """The *paths* under ``scripts/`` that carry the name of a replica module.

    The five it lived at, and the same names in a folder below them:
    ``scripts/figures/fdtd2d.py`` would be imported as ``figures.fdtd2d``,
    which the import scan reads as ``figures``.
    """
    return sorted(
        path
        for path in paths
        if path.startswith("scripts/")
        and pathlib.PurePosixPath(path).suffix == ".py"
        and pathlib.PurePosixPath(path).stem in _GONE_MODULES
    )


@functools.cache
def _tracked_names() -> tuple[str, ...]:
    """Every file git tracks in the repository this guard sits in."""
    # Fixed argv, run on the repository this file belongs to
    listed = child_process.run(
        ["git", "-C", str(_ROOT), "ls-files", "-z"],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    ).stdout
    return tuple(name for name in listed.split("\0") if name)


def _tracked_texts() -> Iterator[tuple[str, str]]:
    """Each tracked text file that holds the prefix, as its path and its text.

    A file holding a NUL byte is binary and left out. The rest are decoded
    with any undecodable byte replaced, so a file in another encoding is
    still read for an ASCII name. A tracked path that is not a file here, a
    submodule or a file deleted in the working tree, has nothing to read.
    """
    for name in _tracked_names():
        path = _ROOT / name
        if not path.is_file():
            continue
        data = path.read_bytes()
        if _SETTING_BYTES in data and b"\0" not in data:
            yield name, data.decode("utf-8", errors="replace")


def old_settings_named(files: Iterable[tuple[str, str]]) -> list[str]:
    """``path: setting`` for each ``PHONO_GPU_`` setting a file names.

    *files* are ``(path in the repository, text)`` pairs; the files of
    :data:`_MAY_NAME` are passed over.
    """
    return [
        f"{name}: {setting}"
        for name, text in files
        if name not in _MAY_NAME
        for setting in sorted(set(_SETTING.findall(text)))
    ]


def test_none_of_the_replicas_scripts_is_back() -> None:
    present = (
        path.relative_to(_ROOT).as_posix() for path in (_ROOT / "scripts").rglob("*.py")
    )
    back = replica_scripts(present)
    assert not back, "\n".join(back)


def test_no_module_imports_the_replica_or_its_transport() -> None:
    found = replica_imports(_python_sources())
    assert not found, "\n".join(found)


def _fullwidth(text: str) -> str:
    """*text* in the fullwidth forms of its ASCII characters, which Python reads as the ASCII ones."""
    return "".join(chr(ord(char) + 0xFEE0) for char in text)


@pytest.mark.parametrize(
    ("source", "module"),
    [
        (f"import {_fullwidth('fdtd2d')}\n", "fdtd2d"),
        (f"from {_fullwidth('fdtd_gpu')} import run\n", "fdtd_gpu"),
        (f"import {_fullwidth('job')}_runner as runner\n", "job_runner"),
    ],
    ids=["import", "from", "in part"],
)
def test_an_import_spelled_in_compatibility_characters_is_seen(
    source: str, module: str
) -> None:
    """Python folds an identifier's compatibility characters (NFKC) before it imports the module."""
    found = replica_imports([("scripts/example.py", source)])
    assert found == [f"scripts/example.py: ['{module}']"]


def test_no_tracked_file_names_an_old_gpu_setting() -> None:
    found = old_settings_named(_tracked_texts())
    assert not found, "\n".join(found)


@pytest.mark.parametrize("path", _GONE_SCRIPTS)
def test_a_replica_script_added_again_is_seen(path: str) -> None:
    assert replica_scripts([path]) == [path]


def test_a_replica_module_under_another_folder_of_scripts_is_seen() -> None:
    assert replica_scripts(["scripts/figures/fdtd2d.py"]) == [
        "scripts/figures/fdtd2d.py"
    ]


def test_the_scripts_that_stay_are_not_taken_for_the_replica() -> None:
    assert replica_scripts(["scripts/engine_scenarios.py", "scripts/fdtd2d.txt"]) == []


@pytest.mark.parametrize(
    ("path", "text", "setting"),
    [
        (
            "src/phonometry/simulation/compute.py",
            'host = os.environ.get("PHONO_GPU_HOST")\n',
            "PHONO_GPU_HOST",
        ),
        (
            "tests/conftest.py",
            'host = os.environ.get("PHONO_GPU_HOST")\n',
            "PHONO_GPU_HOST",
        ),
        (
            ".github/actions/clips/action.yml",
            "runs:\n  env:\n    PHONO_GPU_HOST: nas\n",
            "PHONO_GPU_HOST",
        ),
        (
            "scripts/figures/media.py",
            'value = os.environ.get(f"PHONO_GPU_{key}")\n',
            "PHONO_GPU_{key}",
        ),
        (
            "scripts/clip_link.py",
            'port = os.environ.get("PHONO_GPU_PORT")\n',
            "PHONO_GPU_PORT",
        ),
        (
            ".github/scripts/comment_pr.py",
            'name = os.environ["PHONO_GPU_NAME"]\n',
            "PHONO_GPU_NAME",
        ),
        (
            "docker/node/provision.sh",
            'ssh "$PHONO_GPU_USER@nas"\n',
            "PHONO_GPU_USER",
        ),
        (
            "scripts/clips.sh",
            'ssh "${PHONO_GPU_HOST}" true\n',
            "PHONO_GPU_HOST",
        ),
        (
            "scripts/figures/media.py",
            'value = os.environ[f"PHONO_GPU_{key.upper()}_S"]\n',
            "PHONO_GPU_{key.upper()}_S",
        ),
    ],
    ids=[
        "library",
        "conftest",
        "action",
        "built from parts",
        "a name never listed",
        "github script",
        "docker",
        "shell braces",
        "built from a call",
    ],
)
def test_a_setting_of_the_old_road_is_seen_wherever_it_is_named(
    path: str, text: str, setting: str
) -> None:
    assert old_settings_named([(path, text)]) == [f"{path}: {setting}"]


def test_the_changelog_and_this_guard_may_name_one() -> None:
    text = "PHONO_GPU_HOST\n"
    assert old_settings_named([("CHANGELOG.md", text), (_THIS, text)]) == []


def test_the_reading_step_reads_the_tracked_files_that_name_one() -> None:
    """A scan that read no file would find no setting: the files known to name one are read.

    This guard names the prefix to refuse it, so it is always among them;
    the changelog is while an entry of it still names a setting.
    """
    read = {name for name, _ in _tracked_texts()}
    assert _THIS in read
    if _SETTING_BYTES in (_ROOT / "CHANGELOG.md").read_bytes():
        assert "CHANGELOG.md" in read


def test_the_scan_reaches_the_folders_a_setting_could_hide_in() -> None:
    tracked = _tracked_names()
    for folder in (
        "src/",
        "scripts/",
        "tests/",
        "docs/",
        "site/",
        "docker/",
        ".github/workflows/",
        ".github/scripts/",
    ):
        assert any(name.startswith(folder) for name in tracked), folder
    assert {"Makefile", ".env.example", "CONTRIBUTING.md"} <= set(tracked)
