#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Commit and push what a render left in the clips checkout, and record it.

``make animations`` and ``make posters`` write into the local checkout of
``jmrplens/phonometry-assets`` (see :mod:`assets_dir`). This is the step
after: it stages ``images/`` there, commits with a message naming what was
rendered and the commit of this repository it was rendered from, pushes, and
writes the resulting commit into ``assets.lock`` here, so the two repositories
say which version of the clips goes with which version of the code.

It refuses rather than guesses. The checkout has to be on ``main`` and clean
apart from ``images/``, because a stray file or a detached head would be
published or lost under a message about clips. And it does nothing when there
is nothing to commit, so a render that changed no bytes leaves no commit.

Usage::

    python scripts/publish_assets.py              # stage, commit, push, lock
    python scripts/publish_assets.py --dry-run    # say what would happen

The Makefile targets run it after every render. ``--no-publish`` on those
targets skips it, for a render meant only for looking at.
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import assets_dir


def _git(checkout: pathlib.Path, *args: str) -> str:
    """Run git in *checkout* and return its stdout without the final newline.

    Only the final newline: ``status --porcelain`` writes a leading space for
    an unstaged change, and stripping it would shift the path by one column.
    """
    return subprocess.run(  # noqa: S603
        ["git", "-C", str(checkout), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rstrip("\n")


def _head_here() -> str:
    return _git(_SCRIPTS.parent, "rev-parse", "--short", "HEAD")


def refuse_unless_publishable(checkout: pathlib.Path) -> None:
    """Raise with the reason when the checkout is not safe to publish from."""
    branch = _git(checkout, "rev-parse", "--abbrev-ref", "HEAD")
    if branch != "main":
        msg = (
            f"{checkout} is on {branch!r}, not main; the clips are published from main"
        )
        raise RuntimeError(msg)
    dirty = [
        line
        for line in _git(checkout, "status", "--porcelain").splitlines()
        if not line[3:].startswith("images/")
    ]
    if dirty:
        listed = ", ".join(line[3:] for line in dirty[:5])
        msg = (
            f"{checkout} has changes outside images/ ({listed}); publish or "
            "discard them first so they are not committed as clips"
        )
        raise RuntimeError(msg)


def changed_clips(checkout: pathlib.Path) -> list[str]:
    """The clip files a render added, changed or removed, by name."""
    _git(checkout, "add", "--all", "images")
    return [
        line[3:].removeprefix("images/")
        for line in _git(checkout, "status", "--porcelain", "images").splitlines()
    ]


def clip_stems(names: list[str]) -> list[str]:
    """``anim_x`` for every ``anim_x_es_dark.webm``, each once, in order."""
    stems: list[str] = []
    for name in names:
        stem = pathlib.PurePosixPath(name).stem
        for suffix in ("_poster", "_es_dark", "_es", "_dark"):
            stem = stem.removesuffix(suffix)
        if stem not in stems:
            stems.append(stem)
    return stems


def message(names: list[str], source: str) -> str:
    stems = clip_stems(names)
    if len(stems) == 1:
        what = stems[0]
    elif len(stems) <= 4:
        what = ", ".join(stems)
    else:
        what = f"{len(stems)} clips"
    return f"Rendered {what} from phonometry {source}\n\n" + "\n".join(
        f"  {name}" for name in names
    )


def publish(*, dry_run: bool) -> int:
    images = assets_dir.require_clips_dir()
    checkout = assets_dir.checkout_root(images)
    refuse_unless_publishable(checkout)
    names = changed_clips(checkout)
    if not names:
        print(f"nothing to publish: {images} matches its last commit")
        return 0
    text = message(names, _head_here())
    if dry_run:
        print(f"would commit and push {len(names)} file(s) in {checkout}:\n")
        print(text)
        _git(checkout, "reset", "-q", "images")
        return 0
    _git(checkout, "commit", "-q", "-m", text)
    _git(checkout, "push", "-q", "origin", "main")
    commit = _git(checkout, "rev-parse", "HEAD")
    assets_dir.LOCK.write_text(commit + "\n", encoding="utf-8")
    print(f"published {len(names)} file(s) as {assets_dir.REPOSITORY}@{commit[:12]}")
    print(f"recorded in {assets_dir.LOCK.name}; commit it with the fingerprint lock")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--dry-run", action="store_true", help="show the commit without making it"
    )
    arguments = parser.parse_args(argv)
    try:
        return publish(dry_run=arguments.dry_run)
    except (RuntimeError, FileNotFoundError, subprocess.CalledProcessError) as error:
        detail = (
            error.stderr.strip()
            if isinstance(error, subprocess.CalledProcessError)
            else error
        )
        print(f"::error::{detail}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
