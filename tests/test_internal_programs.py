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

if TYPE_CHECKING:
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
