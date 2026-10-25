#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Which file runs for a program named by a bare name: never one only the working directory holds, on Windows."""

from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import windows_lookup

from phonometry._internal.programs import past_the_working_directory
from phonometry.io import _video_encoders as ve
from phonometry.simulation._remote import command

if TYPE_CHECKING:
    from collections.abc import Callable

#: Where Windows' lookup writes a program it found in the working directory.
_HERE = f"{os.curdir}{os.sep}tool.exe"


@pytest.fixture
def windows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Windows lookup from *tmp_path*, which holds a planted ``tool.exe``, with nothing on ``PATH``."""
    (tmp_path / "tool.exe").write_bytes(b"")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "elsewhere"))
    monkeypatch.setattr(shutil, "which", windows_lookup.which)
    monkeypatch.setattr(sys, "platform", "win32")
    return tmp_path


def _plant(directory: Path) -> Path:
    """A ``tool.exe`` in *directory*, made with its parents."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "tool.exe").write_bytes(b"")
    return directory / "tool.exe"


def _only_in_the_working_directory(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[str, str | None]:
    return "tool", None


def _on_path_past_the_working_directory(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[str, str | None]:
    return "tool", str(_plant(root / "elsewhere"))


def _in_the_first_path_entry_that_holds_it(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[str, str | None]:
    first = _plant(root / "first")
    _plant(root / "second")
    # An empty entry is skipped, not read as the working directory.
    path = ["", str(root / "first"), str(root / "second")]
    monkeypatch.setenv("PATH", os.pathsep.join(path))
    return "tool", str(first)


def _in_a_working_directory_path_lists(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[str, str | None]:
    monkeypatch.setenv("PATH", os.pathsep.join([str(root / "elsewhere"), str(root)]))
    return "tool", _HERE


def _named_with_a_directory(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[str, str | None]:
    # The working directory's own, named so, is the user's choice too.
    return f"{os.curdir}{os.sep}tool", _HERE


def _found_outside_the_working_directory(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[str, str | None]:
    (root / "tool.exe").unlink()
    installed = _plant(root / "elsewhere")
    return "tool", f"{installed.parent}{os.sep}{installed.name}"


def _off_windows(root: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str | None]:
    monkeypatch.setattr(sys, "platform", "linux")
    return "tool", _HERE


@pytest.mark.parametrize(
    "case",
    [
        _only_in_the_working_directory,
        _on_path_past_the_working_directory,
        _in_the_first_path_entry_that_holds_it,
        _in_a_working_directory_path_lists,
        _named_with_a_directory,
        _found_outside_the_working_directory,
        _off_windows,
    ],
    ids=lambda case: case.__name__.strip("_"),
)
def test_the_file_to_run(
    windows: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: Callable[[Path, pytest.MonkeyPatch], tuple[str, str | None]],
) -> None:
    """The file to run for what ``shutil.which`` found, or ``None`` for a program found only in the working directory."""
    name, expected = case(windows, monkeypatch)
    found = shutil.which(name)
    assert found is not None
    assert past_the_working_directory(name, found) == expected


def _found_at(name: str) -> str:
    """Where the stand-in for ``shutil.which`` finds *name*."""
    return str(Path("found") / f"{name}.exe")


def _given_for(name: str) -> str:
    """The file the stand-in for the rule gives for *name*."""
    return str(Path("given") / f"{name}.exe")


def test_the_ffmpeg_and_ssh_lookups_run_the_file_it_gives(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Neither lookup holds a copy of the rule: each asks it, runs the file it gives, and logs to a logger of its own."""
    import matplotlib as mpl

    asked: list[tuple[str, str]] = []

    def rule(name: str, found: str) -> str | None:
        asked.append((name, found))
        return _given_for(name)

    monkeypatch.setattr(shutil, "which", _found_at)
    monkeypatch.setitem(mpl.rcParams, "animation.ffmpeg_path", "ffmpeg")
    monkeypatch.setattr(command, "_SSH_PROGRAM", None)
    monkeypatch.setattr(ve, "past_the_working_directory", rule)
    monkeypatch.setattr(command, "past_the_working_directory", rule)
    with caplog.at_level(logging.INFO, logger="phonometry"):
        assert ve.find_ffmpeg() == _given_for("ffmpeg")
        assert command.ssh_program() == (_given_for("ssh"),)
    assert asked == [("ffmpeg", _found_at("ffmpeg")), ("ssh", _found_at("ssh"))]
    assert [(name, level) for name, level, _ in caplog.record_tuples] == [
        ("phonometry.io", logging.INFO),
        ("phonometry.simulation", logging.INFO),
    ]
