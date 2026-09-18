#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where the rendered clips live, which is no longer this repository.

The animation clips and their poster frames are binary, large and re-encoded
whole whenever the code drawing one changes. Kept here they made a clone of
the code download gigabytes it did not need, so they live in a repository of
their own, ``jmrplens/phonometry-assets``, and this module says where the
local checkout of it is.

The figures are different and stay: an SVG is text, git stores a revision of
one as a few kilobytes of delta, and ``check_figures.py`` regenerates and
compares them on every pull request. So ``make graphs`` still writes to
``.github/images`` and only ``make animations`` and ``make posters`` write to
the directory this module names.

Resolution, in order:

1. ``PHONOMETRY_ASSETS_DIR`` in the environment, or in the repository ``.env``
   next to the GPU settings, naming the ``images`` directory of the checkout.
2. Otherwise ``<repository>/../phonometry-assets/images``, a sibling checkout,
   which is what ``make assets`` creates.

Nothing falls back to ``.github/images``. A clip written there would be
reported by ``check_figures.py`` as a figure nobody committed, and the whole
point of the split is that no clip enters this repository again.
"""

from __future__ import annotations

import os
from pathlib import Path

import fdtd_gpu_remote

_REPO_ROOT = Path(__file__).resolve().parent.parent

#: The environment variable naming the clips directory.
VARIABLE = "PHONOMETRY_ASSETS_DIR"

#: The GitHub repository the clips are published to.
REPOSITORY = "jmrplens/phonometry-assets"

#: Where a clip is served from, for the guides, the READMEs and the site.
RAW_URL = f"https://raw.githubusercontent.com/{REPOSITORY}/main/images"

#: The file in this repository recording which commit of the assets
#: repository the committed code's clips were rendered into.
LOCK = _REPO_ROOT / "assets.lock"


def default_dir() -> Path:
    """The sibling checkout ``make assets`` creates."""
    return _REPO_ROOT.parent / "phonometry-assets" / "images"


def clips_dir() -> Path:
    """The directory the clips are rendered into and published from.

    Reads ``.env`` first, dotenv-style, so a value set there beside the GPU
    host is honoured without exporting anything.
    """
    fdtd_gpu_remote.load_env()
    configured = os.environ.get(VARIABLE, "").strip()
    return Path(configured).expanduser() if configured else default_dir()


def checkout_root(images: Path) -> Path:
    """The git checkout holding *images*, which is its parent."""
    return images.parent


def require_clips_dir() -> Path:
    """:func:`clips_dir`, or a clear error naming what to run.

    Used by the targets that write clips, so a missing checkout stops the run
    before rendering rather than after.
    """
    images = clips_dir()
    if not (checkout_root(images) / ".git").exists():
        msg = (
            f"the clips directory {images} is not inside a git checkout of "
            f"{REPOSITORY}. Run `make assets` to clone it beside this "
            f"repository, or set {VARIABLE} in .env to an existing checkout."
        )
        raise FileNotFoundError(msg)
    images.mkdir(parents=True, exist_ok=True)
    return images


def locked_commit() -> str:
    """The assets commit the committed code was rendered against."""
    return LOCK.read_text(encoding="utf-8").strip()
