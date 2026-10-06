#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The repository ``.env``, read with the standard library alone.

``.env`` holds the machine-specific settings no commit should carry: the GPU
host the FDTD fields and the AV1 encodes run on (``PHONO_GPU_*``) and where
the published clips are checked out (``PHONOMETRY_ASSETS_DIR``). It is
untracked; ``.env.example`` documents every key.

This lives in a module of its own, and imports nothing outside the standard
library, because the readers of ``.env`` are not all renderers. The clip
resolver in ``assets_dir.py`` needs it to find the assets checkout, and that
resolver runs in jobs that install nothing at all: the freshness check of the
published clips (``check_animation_freshness.py``) and ``make assets``, which
is the first thing a fresh clone runs. When the reader lived inside the GPU
runner, asking where the clips are imported NumPy, and those jobs failed on a
module they never use.

Real environment variables take precedence over the file, dotenv-style, and
the parser is self-contained so python-dotenv is not a dependency.
"""

from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def env_file() -> Path:
    """The ``.env`` holding the local settings, from a worktree as well.

    ``.env`` is untracked, so it exists only next to the main checkout. Run
    from a linked worktree, the copy beside this file is absent and every
    setting would read as unset, which downgrades an AV1 render to VP9 without
    saying so. Fall back to the directory holding the common git dir, which is
    the main checkout for every worktree of the repository. The pointer git
    writes is absolute, or relative to the worktree when it was added with
    ``--relative-paths``; both are read against the worktree, never against
    the directory the process happens to run in.
    """
    local = _REPO_ROOT / ".env"
    if local.is_file():
        return local
    git_dir = _REPO_ROOT / ".git"
    if git_dir.is_file():  # a worktree: the file points at the common git dir
        pointer = git_dir.read_text(encoding="utf-8").strip()
        if pointer.startswith("gitdir:"):
            common = (_REPO_ROOT / pointer.split(":", 1)[1].strip()).resolve()
            for parent in common.parents:
                if parent.name == ".git":
                    return parent.parent / ".env"
    return local


#: The file :func:`load_env` reads when it is given none.
ENV_FILE = env_file()


def load_env(path: Path = ENV_FILE) -> dict[str, str]:
    """Read ``KEY=VALUE`` lines from *path* into the process environment.

    Comments (``#``) and blank lines are skipped, surrounding quotes are
    stripped, and variables already present in ``os.environ`` are left
    untouched (real environment wins, as python-dotenv does). Returns the
    mapping that was read (before precedence), for inspection.
    """
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            values[key] = value
            os.environ.setdefault(key, value)
    return values
