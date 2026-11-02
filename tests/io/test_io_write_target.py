#  Copyright (c) 2026. Jose Manuel Requena Plens
"""io.write and the target of io.convert take the name only once the new file is whole.

Both wrote straight at the name they were given, so an error or an interrupt
half way left what python-soundfile, SciPy or the in-house packer had begun
there: a recording that was at the name was lost, and a file no reader could
trust took its place. With nothing at the name, or a regular file, the new
file is written beside it and renamed over it at the end, keeping the old
file's permission bits. A link, a pipe, a device or a directory at the name
is opened there as Python opens a name, as it always was: a caller who names
a pipe streams the recording into it on purpose.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest
from special_files import raised_within

from phonometry._internal import json_input
from phonometry.io import _convert, _flac, _write, convert, read, write
from phonometry.io._bext import fresh_metadata

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

#: Whether the [audio] extra, which writes FLAC, is installed.
HAVE_SOUNDFILE = importlib.util.find_spec("soundfile") is not None

_NEEDS_SOUNDFILE = pytest.mark.skipif(
    not HAVE_SOUNDFILE, reason="the [audio] extra (soundfile) is not installed"
)
_POSIX = pytest.mark.skipif(sys.platform == "win32", reason="POSIX pipes and devices")

FS = 48000
SAMPLES = np.linspace(-0.5, 0.5, 4096)
OLD_BYTES = b"the recording that was at the name"


def _interrupt(*_args: object, **_kwargs: object) -> None:
    raise KeyboardInterrupt


def _one_block_then_interrupt(
    real: Callable[..., Iterator[np.ndarray]],
) -> Callable[..., Iterator[np.ndarray]]:
    """The block stream of a conversion, stopped by an interrupt after one block."""

    def blocks(*args: object, **kwargs: object) -> Iterator[np.ndarray]:
        yield next(real(*args, **kwargs))
        raise KeyboardInterrupt

    return blocks


def _write_with_bext(path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_write, "append_riff_chunk", _interrupt)
    write(path, SAMPLES, FS, bext=fresh_metadata())


def _write_pcm24(path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_write, "_encode_frames", _interrupt)
    write(path, SAMPLES, FS, subtype="PCM_24")


def _write_flac(path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_flac, "embed_flac_bext", _interrupt)
    write(path, SAMPLES, FS, bext=fresh_metadata())


def _convert_stopped(path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = path.with_name("source.wav")
    write(source, SAMPLES, FS, subtype="PCM_24")
    monkeypatch.setattr(
        _convert,
        "_quantised_blocks",
        _one_block_then_interrupt(_convert._quantised_blocks),
    )
    convert(source, path, block_size=512)


#: Each writer of a caller's name, stopped half way: after the samples and
#: before the bext SciPy writes none of, inside the samples of the in-house
#: packer, after the FLAC and before its bext, and after one block of a
#: conversion.
_STOPPED: dict[str, tuple[str, Callable[[Path, pytest.MonkeyPatch], None]]] = {
    "write WAV": ("meas.wav", _write_with_bext),
    "write PCM_24": ("meas.wav", _write_pcm24),
    "write FLAC": ("meas.flac", _write_flac),
    "convert to WAV": ("meas.wav", _convert_stopped),
    "convert to FLAC": ("meas.flac", _convert_stopped),
}


def _writers() -> list[object]:
    return [
        pytest.param(name, marks=_NEEDS_SOUNDFILE) if "FLAC" in name else name
        for name in sorted(_STOPPED)
    ]


@pytest.mark.parametrize("writer", _writers())
@pytest.mark.parametrize("before", ["nothing", "a recording"])
def test_a_write_stopped_half_way_leaves_the_name_as_it_was(
    writer: str, before: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An interrupt half way left a file begun at the name, over a recording too."""
    name, stopped = _STOPPED[writer]
    path = tmp_path / name
    if before == "a recording":
        path.write_bytes(OLD_BYTES)
    with pytest.raises(KeyboardInterrupt):
        stopped(path, monkeypatch)
    monkeypatch.undo()
    left = sorted(entry.name for entry in tmp_path.iterdir())
    expected = {"nothing": [], "a recording": [name]}[before]
    if writer.startswith("convert"):
        expected = sorted([*expected, "source.wav"])
    assert left == expected
    if before == "a recording":
        assert path.read_bytes() == OLD_BYTES


def test_a_regular_file_at_the_name_is_replaced_with_its_permission_bits(
    tmp_path: Path,
) -> None:
    path = tmp_path / "meas.wav"
    path.write_bytes(OLD_BYTES)
    path.chmod(0o640)
    write(path, SAMPLES, FS, subtype="DOUBLE")
    assert np.asarray(read(path)).ravel().tolist() == SAMPLES.tolist()
    assert [entry.name for entry in tmp_path.iterdir()] == ["meas.wav"]
    if sys.platform != "win32":
        assert stat.S_IMODE(path.stat().st_mode) == 0o640


def test_a_hard_link_to_the_old_file_keeps_the_old_bytes(tmp_path: Path) -> None:
    """The name is given a new file: written in place, the link changed with it."""
    path = tmp_path / "meas.wav"
    path.write_bytes(OLD_BYTES)
    kept = tmp_path / "kept.wav"
    os.link(path, kept)
    write(path, SAMPLES, FS)
    assert kept.read_bytes() == OLD_BYTES
    assert path.read_bytes() != OLD_BYTES


def test_a_link_at_the_name_stays_and_the_file_it_names_is_written(
    tmp_path: Path,
) -> None:
    named = tmp_path / "named.wav"
    named.write_bytes(OLD_BYTES)
    path = tmp_path / "meas.wav"
    try:
        path.symlink_to(named)
    except OSError as error:  # pragma: no cover - Windows without the privilege
        pytest.skip(f"no symbolic link here: {error}")
    write(path, SAMPLES, FS, subtype="DOUBLE")
    assert path.is_symlink()
    assert np.asarray(read(named)).ravel().tolist() == SAMPLES.tolist()
    assert sorted(entry.name for entry in tmp_path.iterdir()) == [
        "meas.wav",
        "named.wav",
    ]


@_POSIX
def test_a_pipe_at_the_name_takes_the_recording(tmp_path: Path) -> None:
    """A caller who names a pipe streams the recording into it, as Python opens it."""
    path = tmp_path / "meas.wav"
    os.mkfifo(path)
    received: list[bytes] = []

    def drain() -> None:
        with path.open("rb") as pipe:
            received.append(pipe.read())

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    raised = raised_within(
        lambda: write(path, SAMPLES, FS, subtype="PCM_24"), pipe=path
    )
    reader.join(5.0)
    assert raised is None
    assert stat.S_ISFIFO(path.lstat().st_mode)
    assert received[0][:4] == b"RIFF"
    assert len(received[0]) > 3 * SAMPLES.size


@_POSIX
def test_a_device_at_the_name_is_written_where_it_is() -> None:
    device = Path(os.devnull)
    with json_input.writing_beside(device) as file:
        assert file == device
        file.write_bytes(OLD_BYTES)
    assert stat.S_ISCHR(device.stat().st_mode)


@pytest.mark.parametrize("writer", ["write", "convert"])
def test_a_directory_at_the_name_raises_what_the_open_raises(
    writer: str, tmp_path: Path
) -> None:
    path = tmp_path / "meas.wav"
    path.mkdir()
    source = tmp_path / "source.wav"
    write(source, SAMPLES, FS)
    calls: dict[str, Callable[[], object]] = {
        "write": lambda: write(path, SAMPLES, FS),
        "convert": lambda: convert(source, path),
    }
    call = calls[writer]
    with pytest.raises(OSError, match="meas.wav"):
        call()
    assert path.is_dir()
    assert list(path.iterdir()) == []
