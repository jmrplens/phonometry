#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The audio readers refuse a name that holds no regular file, before they open it.

A named pipe no one writes to kept :func:`~phonometry.io.read` waiting at the
open of its sniffer for a writer that never came, a link to ``/dev/zero`` was
read as twelve zero bytes and called no audio file, and a directory raised
the ``IsADirectoryError`` of the open. Each reader now names what is at the
name in one :class:`ValueError`, within seconds, before it opens it: the four
entry points, and the readers of the package and of python-soundfile and SciPy
behind them, each of which asks again before its own open.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import numpy as np
import pytest
from special_files import SPECIAL_KINDS, make_special, raised_within

from phonometry._internal import json_input
from phonometry.io import (
    _audio_file,
    _backends,
    _chunks,
    _flac,
    _wav,
    convert,
    info,
    read,
    read_blocks,
    write,
)

if TYPE_CHECKING:
    import os
    from collections.abc import Callable
    from pathlib import Path

FS = 48000

#: Each entry point of the package that reads an audio file a caller names.
_READERS: dict[str, Callable[[Path], object]] = {
    "read": read,
    "info": info,
    "read_blocks": lambda path: read_blocks(path, 4),
    "convert": lambda path: convert(path, path.with_name("converted.wav")),
}


@pytest.mark.parametrize("reader", sorted(_READERS))
@pytest.mark.parametrize("kind", SPECIAL_KINDS)
def test_a_name_that_holds_no_regular_file_is_refused_before_it_is_opened(
    kind: str, reader: str, tmp_path: Path
) -> None:
    """A pipe kept the sniffer's open waiting, and a device and a directory came
    out as something else.
    """
    path = tmp_path / "meas.wav"
    what = make_special(kind, path)
    error = raised_within(
        lambda: _READERS[reader](path), pipe=path if kind == "pipe" else None
    )
    assert isinstance(error, ValueError)
    assert (
        str(error) == f"{path}: is {what}, and audio is read only from a regular file"
    )
    assert not path.with_name("converted.wav").exists()


@pytest.mark.parametrize(
    "inner",
    [
        lambda path: _backends._sniff(path),
        lambda path: _chunks.parse_wav_chunks(path),
        lambda path: _flac.read_flac_bext(path),
        lambda path: _flac.embed_flac_bext(path, b""),
        lambda path: _wav.wav_info(path),
    ],
    ids=["sniff", "chunk walker", "flac bext", "flac bext writer", "wav info"],
)
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX pipes")
def test_every_reader_behind_the_entry_points_asks_again(
    inner: Callable[[Path], object], tmp_path: Path
) -> None:
    """A pipe put at the name after the entry point looked is refused too."""
    path = tmp_path / "meas.wav"
    make_special("pipe", path)
    error = raised_within(lambda: inner(path), pipe=path)
    assert isinstance(error, ValueError)
    assert "is a named pipe (FIFO), and audio is read only from a regular file" in str(
        error
    )


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX pipes")
def test_the_readers_of_other_libraries_are_asked_about_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SciPy and soundfile open the name themselves: the check comes before them."""
    good = tmp_path / "good.wav"
    write(good, np.zeros(16), FS)
    chunks = _chunks.parse_wav_chunks(good)
    pipe = tmp_path / "pipe.wav"
    make_special("pipe", pipe)

    def refuse(*_: object, **__: object) -> object:
        msg = "opened before the check"
        raise AssertionError(msg)

    monkeypatch.setattr(_wav.wavfile, "read", refuse)
    error = raised_within(lambda: _wav.read_wav(pipe, chunks), pipe=pipe)
    assert isinstance(error, ValueError)
    assert "is a named pipe (FIFO)" in str(error)

    class NoSoundfile:
        info = read = blocks = staticmethod(refuse)

    error = raised_within(
        lambda: _backends.soundfile_stamp(NoSoundfile, pipe, "FLAC"), pipe=pipe
    )
    assert isinstance(error, ValueError)
    assert "is a named pipe (FIFO)" in str(error)


@pytest.mark.skipif(sys.platform == "win32", reason="symbolic links")
def test_a_link_to_a_recording_is_read(tmp_path: Path) -> None:
    kept = tmp_path / "kept.wav"
    write(kept, np.arange(8, dtype=np.float64) / 16, FS)
    link = tmp_path / "meas.wav"
    link.symlink_to(kept)
    np.testing.assert_array_equal(read(link).data, read(kept).data)
    assert info(link).n_samples == 8


def test_a_name_with_nothing_at_it_raises_what_the_open_always_raised(
    tmp_path: Path,
) -> None:
    for reader in _READERS.values():
        with pytest.raises(FileNotFoundError):
            reader(tmp_path / "missing.wav")


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX pipes")
def test_a_pipe_put_in_the_place_of_the_file_is_refused_at_the_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Between the look at the name and the open, a pipe may take its place."""
    regular = tmp_path / "regular.wav"
    write(regular, np.zeros(8), FS)
    looked = regular.stat()
    pipe = tmp_path / "swapped.wav"
    make_special("pipe", pipe)
    real_stat = type(pipe).stat

    def stat(self: Path, *, follow_symlinks: bool = True) -> os.stat_result:
        if self == pipe:
            return looked
        return real_stat(self, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(type(pipe), "stat", stat)
    error = raised_within(lambda: json_input.open_regular(pipe), pipe=pipe)
    assert isinstance(error, json_input.NotRegularError)
    assert error.kind == "a named pipe (FIFO)"

    def opened() -> object:
        with _audio_file.open_audio(pipe):
            pass
        return None

    error = raised_within(opened, pipe=pipe)
    assert isinstance(error, ValueError)
    assert "is a named pipe (FIFO)" in str(error)


def test_the_shared_open_hands_back_the_file_at_its_start(tmp_path: Path) -> None:
    path = tmp_path / "bytes.bin"
    path.write_bytes(b"RIFF....WAVE")
    with json_input.open_regular(path) as handle:
        assert handle.read() == b"RIFF....WAVE"
    with pytest.raises(FileNotFoundError):
        json_input.open_regular(tmp_path / "missing.bin")
