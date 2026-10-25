#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Which file runs for a program named by a bare name: never one only the working directory holds, on Windows."""

from __future__ import annotations

import os
import shutil
import sys
from typing import TYPE_CHECKING

import pytest
import windows_lookup

from phonometry._internal.programs import past_the_working_directory
from phonometry.io import _video_encoders as ve

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

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


def test_a_program_found_only_in_the_working_directory_is_none(windows: Path) -> None:
    assert shutil.which("tool") == _HERE
    assert past_the_working_directory("tool", _HERE) is None


def test_the_first_directory_of_path_that_holds_it_wins(
    windows: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for directory in ("first", "second"):
        (windows / directory).mkdir()
        (windows / directory / "tool.exe").write_bytes(b"")
    # An empty entry is skipped, not read as the working directory.
    path = ["", str(windows / "first"), str(windows / "second")]
    monkeypatch.setenv("PATH", os.pathsep.join(path))
    assert past_the_working_directory("tool", _HERE) == str(
        windows / "first" / "tool.exe"
    )


def test_a_name_with_a_directory_is_run_as_found(windows: Path) -> None:
    named = str(windows / "tool")
    found = str(windows / "tool.exe")
    assert past_the_working_directory(named, found) == found


def test_a_program_found_outside_the_working_directory_is_run_as_found(
    windows: Path,
) -> None:
    found = str(windows / "elsewhere" / "tool.exe")
    assert past_the_working_directory("tool", found) == found


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
        _off_windows,
    ],
    ids=lambda case: case.__name__.strip("_"),
)
def test_the_ffmpeg_lookup_gives_the_same_answer(
    windows: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: Callable[[Path, pytest.MonkeyPatch], tuple[str, str | None]],
) -> None:
    """io's ffmpeg lookup keeps its own copy of the rule, and gives the same file, or refuses where this gives none."""
    name, expected = case(windows, monkeypatch)
    found = shutil.which(name)
    assert found is not None
    answer: str | None
    try:
        answer = ve._outside_the_working_directory(name, found)
    except ve.FFmpegNotFoundError:
        answer = None
    assert past_the_working_directory(name, found) == answer == expected
