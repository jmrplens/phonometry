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


def _longest_name(directory: Path) -> int:
    """The longest name *directory* takes, 255 where it cannot say."""
    try:
        return os.pathconf(directory, "PC_NAME_MAX")
    except (AttributeError, OSError, ValueError):
        return 255


#: How a recording is written to a name as long as its directory takes: SciPy's
#: WAV, the in-house packer, and python-soundfile's FLAC with a ``bext``,
#: which is copied once more beside the file to put the chunk in.
_LONG_NAME_WRITES: dict[str, tuple[str, Callable[[Path], None], bool]] = {
    "WAV": (".wav", lambda path: write(path, SAMPLES, FS), False),
    "PCM_24": (".wav", lambda path: write(path, SAMPLES, FS, subtype="PCM_24"), False),
    "FLAC with a bext": (
        ".flac",
        lambda path: write(path, SAMPLES, FS, bext=fresh_metadata()),
        True,
    ),
}


@pytest.mark.parametrize("kind", sorted(_LONG_NAME_WRITES))
def test_a_name_as_long_as_the_directory_takes_is_written(
    kind: str, tmp_path: Path
) -> None:
    """The hidden name beside the target is cut to what the directory takes.

    It was the whole name with a dot, a token of sixteen digits and
    ``.partial`` added, 26 characters more, and a FLAC with a ``bext`` added
    ``.phonometry-tmp`` to that, so a name of 232 characters or more on a
    file system of 255 was refused as too long before anything was written.
    """
    suffix, write_to, needs_soundfile = _LONG_NAME_WRITES[kind]
    if needs_soundfile and not HAVE_SOUNDFILE:
        pytest.skip("the [audio] extra (soundfile) is not installed")
    path = tmp_path / ("m" * (_longest_name(tmp_path) - len(suffix)) + suffix)
    write_to(path)
    assert read(path).data.shape[-1] == SAMPLES.size
    assert [entry.name for entry in tmp_path.iterdir()] == [path.name]


def test_the_name_beside_a_target_fits_its_directory_and_is_new(
    tmp_path: Path,
) -> None:
    longest = _longest_name(tmp_path)
    # Two bytes a character, so a cut through the middle of one is possible.
    target = tmp_path / ("é" * longest)
    first = json_input.beside_name(target, ".partial")
    second = json_input.beside_name(target, ".partial")
    for beside in (first, second):
        assert beside.parent == tmp_path
        assert beside.name.startswith(".é")
        assert beside.name.endswith(".partial")
        assert len(os.fsencode(beside.name)) <= longest
    assert first != second
    short = json_input.beside_name(tmp_path / "meas.wav", ".tmp")
    assert short.name.startswith(".meas.wav.")


@pytest.fixture
def usual_umask() -> Iterator[None]:
    """The umask most systems start a user with: new files readable by everyone."""
    kept = os.umask(0o022)
    try:
        yield
    finally:
        os.umask(kept)


def _hidden_modes(directory: Path) -> dict[str, int]:
    """The permission bits of each hidden file in *directory*, by name."""
    return {
        entry.name: stat.S_IMODE(entry.stat().st_mode)
        for entry in directory.iterdir()
        if entry.name.startswith(".")
    }


@_POSIX
@pytest.mark.usefixtures("usual_umask")
@pytest.mark.parametrize(
    ("before", "after"), [(0o600, 0o600), (0o640, 0o640), (None, 0o644)]
)
def test_the_file_beside_a_private_one_is_private_while_it_is_written(
    before: int | None, after: int, tmp_path: Path
) -> None:
    """The writer made the file beside the target with the umask's bits, 0644.

    The old file's bits were given to it only once the writer was done, so a
    recording kept private could be read by anyone, in its new file, while it
    was written. The file is now made before the writer opens it, readable and
    writable by its owner alone where it replaces a file, and with the umask's
    bits where nothing is replaced, as the new file keeps them.
    """
    path = tmp_path / "meas.wav"
    if before is not None:
        path.write_bytes(OLD_BYTES)
        path.chmod(before)
    with json_input.writing_beside(path) as file:
        with file.open("wb") as handle:
            handle.write(b"the new recording")
        while_written = stat.S_IMODE(file.stat().st_mode)
    assert while_written == (0o600 if before is not None else 0o644)
    assert stat.S_IMODE(path.stat().st_mode) == after
    assert path.read_bytes() == b"the new recording"
    assert [entry.name for entry in tmp_path.iterdir()] == ["meas.wav"]


def _write_double(path: Path) -> None:
    write(path, SAMPLES, FS, subtype="DOUBLE")


def _write_pcm24_whole(path: Path) -> None:
    write(path, SAMPLES, FS, subtype="PCM_24")


def _write_flac_with_bext(path: Path) -> None:
    write(path, SAMPLES, FS, bext=fresh_metadata())


def _convert_to(path: Path) -> None:
    convert(path.with_name("source.wav"), path)


#: Each writer of a recording at a caller's name: SciPy's WAV, the in-house
#: packer, python-soundfile's FLAC with a bext copied once more beside it to
#: put the chunk in, and a conversion to FLAC, which copies it the same way
#: (from a source the test writes first).
_PRIVATE_WRITES: dict[str, tuple[str, Callable[[Path], None], bool]] = {
    "write WAV": ("meas.wav", _write_double, False),
    "write PCM_24": ("meas.wav", _write_pcm24_whole, False),
    "write FLAC with a bext": ("meas.flac", _write_flac_with_bext, True),
    "convert to FLAC": ("meas.flac", _convert_to, True),
}


@_POSIX
@pytest.mark.usefixtures("usual_umask")
@pytest.mark.parametrize("writer", sorted(_PRIVATE_WRITES))
def test_a_private_recording_is_never_written_where_others_can_read_it(
    writer: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every file the new recording passes through beside the old is private.

    The bits of every hidden file are read when the writer is done, before
    the old file's bits are given to the new one: a FLAC with a bext is
    copied once more beside the first new file to put the chunk in, and that
    copy, made with the umask's bits, took the first one's place.
    """
    name, write_to, needs_soundfile = _PRIVATE_WRITES[writer]
    if needs_soundfile and not HAVE_SOUNDFILE:
        pytest.skip("the [audio] extra (soundfile) is not installed")
    path = tmp_path / name
    path.write_bytes(OLD_BYTES)
    path.chmod(0o600)
    if writer.startswith("convert"):
        write(tmp_path / "source.wav", SAMPLES, FS, subtype="PCM_24")
    seen: list[dict[str, int]] = []
    flushed = json_input._flushed

    def looked_at(written: Path, mode: int | None) -> None:
        seen.append(_hidden_modes(tmp_path))
        flushed(written, mode)

    monkeypatch.setattr(json_input, "_flushed", looked_at)
    write_to(path)
    assert len(seen) == 1
    assert len(seen[0]) == 1
    assert list(seen[0].values()) == [0o600]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert read(path).data.shape[-1] == SAMPLES.size


@_POSIX
@pytest.mark.usefixtures("usual_umask")
@pytest.mark.parametrize(
    ("before", "after"), [(0o600, 0o600), (0o644, 0o644), (None, 0o644)]
)
def test_bytes_put_beside_a_private_file_are_never_readable_by_others(
    before: int | None, after: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """write_beside wrote the bytes into a file made with the umask's bits.

    The old file's bits came after the bytes, so a sidecar or a catalogue
    kept private could be opened by anyone in between, and read through that
    open file once the bytes were there. The bits are read just before the
    old file's are given, once the bytes are written.
    """
    target = tmp_path / "meas.wav.json"
    if before is not None:
        target.write_bytes(OLD_BYTES)
        target.chmod(before)
    seen: list[int] = []
    fchmod = os.fchmod

    def looked_at(descriptor: int, mode: int) -> None:
        seen.append(stat.S_IMODE(os.fstat(descriptor).st_mode))
        fchmod(descriptor, mode)

    monkeypatch.setattr(os, "fchmod", looked_at)
    json_input.write_beside(target, b"the new sidecar")
    monkeypatch.undo()
    assert seen == ([0o600] if before is not None else [])
    assert stat.S_IMODE(target.stat().st_mode) == after
    assert target.read_bytes() == b"the new sidecar"


def test_a_writer_left_at_the_yield_leaves_no_file_beside(tmp_path: Path) -> None:
    """A writer whose generator is closed at the yield removes the new file.

    Neither resumed nor handed an error: the generator is closed as Python
    closes any it drops, and the file made beside the target goes with it.
    """
    path = tmp_path / "meas.wav"
    path.write_bytes(OLD_BYTES)
    manager = json_input.writing_beside(path)
    beside = manager.__enter__()
    beside.write_bytes(b"half a recording")
    manager.gen.close()
    assert [entry.name for entry in tmp_path.iterdir()] == ["meas.wav"]
    assert path.read_bytes() == OLD_BYTES


def test_a_directory_that_cannot_say_its_longest_name_takes_255(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A directory not there yet answers no ``pathconf``, and Windows has no
    ``pathconf`` at all: the name beside a target is cut to 255 bytes then.
    """
    assert json_input._name_max(tmp_path / "not-there-yet") == 255
    monkeypatch.delattr(os, "pathconf", raising=False)
    assert json_input._name_max(tmp_path) == 255
    beside = json_input.beside_name(tmp_path / ("m" * 300), ".partial")
    assert len(os.fsencode(beside.name)) <= 255
