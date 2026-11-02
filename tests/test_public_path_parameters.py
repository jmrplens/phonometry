#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The path parameters of io and of the ANP loader take any ``os.PathLike``, and say so.

``io.write``, ``io.convert`` and ``io.write_sidecar`` were annotated
``str | Path`` where the video writers took ``str | os.PathLike[str]``. Each
one turns what it is given into a ``Path``, so it took any path-like object
all along, but a type checker refused one that is not a ``pathlib.Path``
(an ``os.DirEntry``, a path class of another library). The census below
refuses a public parameter whose annotation names ``Path`` and leaves
``os.PathLike`` out; a path annotated ``str`` alone names neither, and is
outside it.
"""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import os
import pkgutil
import re
import sys
from typing import TYPE_CHECKING, Literal

import numpy as np
import pytest

import phonometry
from phonometry import aircraft, io
from phonometry.io import _flac, _write

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from phonometry.io._write import Subtype

#: The word ``Path`` in an annotation's text, not a part of a longer name.
_PATH = re.compile(r"\bPath\b")
#: FLAC goes through python-soundfile, the ``[audio]`` extra.
_needs_soundfile = pytest.mark.skipif(
    importlib.util.find_spec("soundfile") is None, reason="needs the [audio] extra"
)


def _public_modules() -> Iterator[object]:
    """Every public module of the package, the root included."""
    yield phonometry
    for found in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if not any(part.startswith("_") for part in found.name.split(".")[1:]):
            yield importlib.import_module(found.name)


def _callables(module: object) -> Iterator[tuple[str, Callable[..., object]]]:
    """The functions a module publishes, and the methods and constructors of its classes."""
    for name in getattr(module, "__all__", ()):
        value = getattr(module, name)
        if inspect.isclass(value):
            for member_name, member in vars(value).items():
                function = getattr(member, "__func__", member)
                if inspect.isfunction(function) and (
                    member_name == "__init__" or not member_name.startswith("_")
                ):
                    yield f"{name}.{member_name}", function
        elif inspect.isfunction(value):
            yield name, value


def _narrow_paths() -> set[str]:
    """Each public parameter annotated with ``Path`` and not with ``os.PathLike``.

    ``Path`` is matched as a word: a record of the library whose name holds
    it (``BandPath``, ``PathTarget``) is no file path.
    """
    narrow = set()
    for module in _public_modules():
        for label, function in _callables(module):
            for parameter, annotation in inspect.get_annotations(function).items():
                text = str(annotation)
                if (
                    parameter != "return"
                    and _PATH.search(text)
                    and "PathLike" not in text
                ):
                    narrow.add(f"{label}({parameter}: {text})")
    return narrow


def test_no_public_annotation_names_path_without_os_pathlike() -> None:
    assert _narrow_paths() == set()


def _text_only_paths() -> set[str]:
    """Each public parameter named ``path`` annotated ``str`` alone.

    A record's field is left out: its ``__init__`` is written by
    ``dataclasses``, and a record such as ``io.AudioFileInfo`` keeps the
    path it read as the text it is.
    """
    return {
        f"{label}(path)"
        for module in _public_modules()
        for label, function in _callables(module)
        if str(inspect.get_annotations(function).get("path")) == "str"
        and function.__code__.co_filename != "<string>"
    }


def test_no_public_path_is_annotated_as_a_text_alone() -> None:
    """A public ``path`` names ``os.PathLike`` beside ``str``.

    The ``.report()`` of every result took ``path: str`` and handed it to
    ReportLab as it got it, so a ``pathlib.Path`` built the whole fiche and
    then failed; each reads the path through ``os.fspath`` now and says so.
    """
    assert _text_only_paths() == set()


class _Elsewhere:
    """A path of another library: an ``os.PathLike`` that is not a ``pathlib.Path``."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def __fspath__(self) -> str:
        return str(self._path)


@pytest.mark.parametrize(
    ("name", "subtype", "bext"),
    [
        ("double.wav", "DOUBLE", None),
        ("pcm16.wav", "PCM_16", None),
        ("pcm24.wav", "PCM_24", None),
        ("bext.wav", "PCM_16", "loudness"),
        pytest.param("archive.flac", None, None, marks=_needs_soundfile),
    ],
)
def test_a_path_of_another_library_is_written_where_it_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    subtype: Subtype | None,
    bext: Literal["loudness"] | None,
) -> None:
    # The writers handed str(path) to SciPy and python-soundfile, which is
    # the object's repr for a path that is not a str or a pathlib.Path: the
    # file went to "<... object at 0x...>" in the working directory.
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(tmp_path)
    samples = np.linspace(-0.5, 0.5, 480)
    io.write(
        _Elsewhere(elsewhere / name),
        io.Signal(samples, 48000),
        subtype=subtype,
        bext=bext,
    )
    assert sorted(p.name for p in tmp_path.iterdir()) == ["elsewhere"]
    assert [p.name for p in elsewhere.iterdir()] == [name]
    back = io.read(_Elsewhere(elsewhere / name))
    assert np.allclose(back.data, samples, atol=1e-4)
    assert io.info(_Elsewhere(elsewhere / name)).path == str(elsewhere / name)


@_needs_soundfile
def test_a_path_of_another_library_is_converted_read_in_blocks_and_calibrated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)  # where a file written to the repr would land
    source, target = _Elsewhere(tmp_path / "a.wav"), _Elsewhere(tmp_path / "b.flac")
    samples = np.linspace(-0.5, 0.5, 480)
    io.write(source, io.Signal(samples, 48000), subtype="PCM_16")
    io.write_sidecar(source, 1.25)
    converted = io.convert(source, target)
    assert converted.path == str(tmp_path / "b.flac")
    assert sum(block.data.shape[-1] for block in io.read_blocks(target, 100)) == 480
    sidecar = io.read_sidecar(target)
    assert sidecar is not None
    assert sidecar.calibration_factor == 1.25
    assert io.sidecar_path(target) == tmp_path / "b.flac.phonometry.json"


def test_a_refusal_names_a_path_of_another_library_by_its_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    # A message printed the object's repr, and convert's left a caller's
    # control characters unescaped.
    io.write(tmp_path / "a.wav", io.Signal(np.zeros(48), 48000))
    source, marked = (
        _Elsewhere(tmp_path / "a.wav"),
        _Elsewhere(tmp_path / "b\x1b[2J.mp3"),
    )
    with pytest.raises(ValueError, match="writing lossy formats") as lossy:
        io.convert(source, marked)
    assert str(lossy.value).startswith(f"{tmp_path}{os.sep}b\\x1b[2J.mp3: ")
    unknown, silence = _Elsewhere(tmp_path / "z.xyz"), io.Signal(np.zeros(48), 48000)
    with pytest.raises(ValueError, match="unsupported target") as suffix:
        io.write(unknown, silence)
    assert str(suffix.value).startswith(f"{tmp_path}{os.sep}z.xyz: ")
    elsewhere = _Elsewhere(tmp_path / "elsewhere")
    with pytest.raises(NotADirectoryError, match="is not a directory") as missing:
        aircraft.load_anp_database(elsewhere)
    assert f"'{tmp_path}{os.sep}elsewhere'" in str(missing.value)
    (tmp_path / "elsewhere").mkdir()
    with pytest.raises(FileNotFoundError, match="no .csv ANP tables") as empty:
        aircraft.load_anp_database(elsewhere)
    assert f"'{tmp_path}{os.sep}elsewhere'" in str(empty.value)


@pytest.mark.parametrize(
    ("refuse", "content", "reason"),
    [
        (_flac.read_flac_bext, b"RIFF\0\0\0\0WAVE", "not a FLAC file"),
        (
            lambda path: _flac.embed_flac_bext(path, bytes(1 << 24)),
            b"fLaC",
            "bext chunk of 16777216 bytes exceeds the 24-bit FLAC metadata block length",
        ),
        (lambda path: _flac.embed_flac_bext(path, b""), b"RIFF", "not a FLAC file"),
        (
            lambda path: _flac.embed_flac_bext(path, b""),
            b"fLaC\0\0",
            "truncated FLAC metadata chain",
        ),
        (
            lambda path: _write.append_riff_chunk(path, b"bext", b""),
            b"fLaC\0\0\0\0",
            "not a RIFF/RF64/BW64 file",
        ),
    ],
    ids=[
        "FLAC bext reader",
        "FLAC bext too long",
        "FLAC bext writer",
        "FLAC chain",
        "RIFF chunk writer",
    ],
)
@pytest.mark.parametrize(
    "name",
    [
        "taken.bin",
        pytest.param(
            "taken\x1b.bin",
            marks=pytest.mark.skipif(
                sys.platform == "win32",
                reason="a Windows file name cannot hold a control character",
            ),
        ),
    ],
    ids=["plain name", "name with ESC"],
)
def test_a_file_unlike_the_one_sniffed_or_written_is_named_by_its_path(
    refuse: Callable[[os.PathLike[str]], object],
    content: bytes,
    reason: str,
    name: str,
    tmp_path: Path,
) -> None:
    # The readers and writers behind io.read, io.info, io.write and io.convert
    # refuse a file that is not the FLAC they sniffed or the FLAC or WAV they
    # have just written, which a caller cannot hand them; the refusal printed
    # a path of another library as the object's repr. A control character in
    # the name is printed as its escape.
    path = tmp_path / name
    path.write_bytes(content)
    elsewhere = _Elsewhere(path)
    with pytest.raises(ValueError, match=reason) as caught:
        refuse(elsewhere)
    escape = ascii(name)[1:-1]
    assert str(caught.value) == f"{tmp_path}{os.sep}{escape}: {reason}"
    assert [entry.name for entry in tmp_path.iterdir()] == [name]


@pytest.mark.parametrize(
    "mark",
    [
        "\x1b[2J",
        "\u202e",
        pytest.param(
            "\udcff",
            marks=pytest.mark.skipif(
                sys.platform == "win32",
                reason="a Windows file name is UTF-16, so no name fails UTF-8",
            ),
        ),
    ],
)
@pytest.mark.parametrize("kind", [str, _Elsewhere])
def test_an_anp_directory_is_named_by_its_escapes_once(
    mark: str, kind: Callable[[Path], str | os.PathLike[str]], tmp_path: Path
) -> None:
    # The name was escaped and then quoted by repr, which doubled the
    # backslash of each escape.
    missing = kind(tmp_path / f"b{mark}")
    with pytest.raises(NotADirectoryError) as caught:
        aircraft.load_anp_database(missing)
    escape = ascii(mark)[1:-1]
    assert str(caught.value) == (
        f"ANP database path '{tmp_path}{os.sep}b{escape}' is not a directory."
    )
