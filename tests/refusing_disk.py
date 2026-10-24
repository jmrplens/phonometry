#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A disk that refuses what a video writer asks of it, for the writers' tests.

The suite may run as root, whom no permission refuses, so a refusal is put in
this process's way instead: a name whose status cannot be read, as inside a
directory without search permission, and a hidden partial file that cannot
be removed, as one a scanner holds open on Windows, or one in a directory
that takes files and lets none go.
"""

from __future__ import annotations

import errno
import os
import pathlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pytest


def refuse_status(monkeypatch: pytest.MonkeyPatch, path: pathlib.Path) -> None:
    """Make reading the status of *path* fail, as inside a directory this process cannot search."""
    real_stat = os.stat
    refused = os.fspath(path)

    def stat(
        target: int | str | bytes | os.PathLike[str] | os.PathLike[bytes],
        *args: Any,
        **kwargs: Any,
    ) -> os.stat_result:
        if not isinstance(target, int) and os.fspath(target) == refused:
            raise PermissionError(errno.EACCES, "Permission denied", refused)
        return real_stat(target, *args, **kwargs)

    monkeypatch.setattr(os, "stat", stat)


def hold_partials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make removing any hidden partial file fail, as while a scanner holds it open."""
    real_unlink = pathlib.Path.unlink

    def unlink(self: pathlib.Path, *, missing_ok: bool = False) -> None:
        if self.name.endswith(".partial"):
            msg = "the file is being used by another process"
            raise PermissionError(errno.EACCES, msg, str(self))
        real_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(pathlib.Path, "unlink", unlink)


def refuse_partials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make creating any hidden partial file fail, as in a directory this process may not write."""
    real_open = pathlib.Path.open

    def opened(self: pathlib.Path, *args: Any, **kwargs: Any) -> object:
        if self.name.endswith(".partial"):
            raise PermissionError(errno.EACCES, "Permission denied", str(self))
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "open", opened)


def partial_sizes(directory: pathlib.Path) -> list[int]:
    """The size of every hidden partial file in *directory*, smallest first."""
    return sorted(p.stat().st_size for p in directory.glob("*.partial"))
