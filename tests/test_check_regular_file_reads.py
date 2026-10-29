#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate on readers that open a file a caller names without asking what it is.

``scripts/check_regular_file_reads.py`` refuses an open of the library's own
outside the shared check (``open()``, a ``.open()`` that reads, ``read_bytes``
and ``read_text``) and a reader of another library (SciPy, python-soundfile,
NumPy) that no check of the same name comes before. The shapes here are the
ones the readers had before they were moved onto the check: the audio sniffer
opening the name with ``Path(path).open("rb")``, the hosts file read with
``read_bytes()``, the ANP tables with ``read_text()``, and soundfile asked for
a file's description with nothing before it. So are the shapes the gate must
let through: a writer's modes, a method of another object called ``open``, and
a reader of another library that a check of the library comes before, however
many helpers deep the check is. And so are the shapes the gate first missed: a
file object opened by its name with ``io.FileIO``, a reader imported under its
own name or another, or bound to another by an assignment, and a copy of
``shutil``, which reads its source by its name.
"""

from __future__ import annotations

import pathlib
import sys
import textwrap

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from typing import TYPE_CHECKING

import check_regular_file_reads as crf

if TYPE_CHECKING:
    import pytest

#: A module that checks a name the way the audio readers of the library do.
_CHECK = """
from phonometry._internal.json_input import not_regular_at

def require_regular(path):
    if not_regular_at(Path(path)) is not None:
        raise ValueError(path)
"""


def _found(
    tmp_path: pathlib.Path, source: str, *, helpers: str = _CHECK
) -> list[tuple[str, str]]:
    """``(function, first words of the shape)`` for each read the gate refuses."""
    reader = tmp_path / "reader.py"
    reader.write_text(textwrap.dedent(source), encoding="utf-8")
    check = tmp_path / "check.py"
    check.write_text(textwrap.dedent(helpers), encoding="utf-8")
    findings, _stale = crf.check([reader, check])
    return [(f.function, f.shape.split(";")[0]) for f in findings]


_OWN = "an open of its own"
_FOREIGN = "a reader of another library with no check of the name before it"


def test_the_sniffer_opening_the_name_itself_is_refused(tmp_path: pathlib.Path) -> None:
    """The shape every audio reader had: a pipe at the name kept the open waiting."""
    assert _found(
        tmp_path,
        """
        def _sniff(path):
            with Path(path).open("rb") as fh:
                return fh.read(12)
        """,
    ) == [("_sniff", _OWN)]


def test_a_whole_file_read_is_refused(tmp_path: pathlib.Path) -> None:
    """The hosts file and the ANP tables were read so, a pipe there waited forever."""
    assert _found(
        tmp_path,
        """
        def load_host(path):
            return path.read_bytes()

        def _read_tables(files):
            return {f.name: f.read_text(encoding="utf-8-sig") for f in files}
        """,
    ) == [("load_host", _OWN), ("_read_tables", _OWN)]


def test_open_without_a_mode_or_with_a_reading_mode_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    assert _found(
        tmp_path,
        """
        import io
        import os

        def builtin(path):
            return open(path)

        def text(path):
            return open(path, mode="r", encoding="utf-8")

        def through_io(path):
            return io.open(path, "rb")

        def low_level(path):
            return os.open(path, os.O_RDONLY)

        def method(path):
            return path.open()

        def unknown_mode(path, mode):
            return open(path, mode)
        """,
    ) == [
        ("builtin", _OWN),
        ("text", _OWN),
        ("through_io", _OWN),
        ("low_level", _OWN),
        ("method", _OWN),
        ("unknown_mode", _OWN),
    ]


def test_a_writer_and_a_method_of_another_object_are_let_through(
    tmp_path: pathlib.Path,
) -> None:
    """A mode that writes is a writer's, and ``pipe.open(fig)`` opens no file."""
    assert (
        _found(
            tmp_path,
            """
            def writers(path, staging, fig, pipe):
                with open(path, "wb") as out, staging.open("xb") as new:
                    out.write(b"")
                with open(path, "r+b") as patched, path.open(mode="ab") as log:
                    patched.write(b"")
                pipe.open(fig)
            """,
        )
        == []
    )


def test_a_reader_of_another_library_needs_a_check_of_the_same_name_before_it(
    tmp_path: pathlib.Path,
) -> None:
    """soundfile and SciPy open the name themselves, so the check comes first."""
    assert _found(
        tmp_path,
        """
        from scipy.io import wavfile

        def described(sf, path):
            return sf.info(str(path))

        def checked(sf, path):
            require_regular(path)
            return sf.read(str(path))

        def another_name(sf, path, other):
            require_regular(other)
            return sf.blocks(str(path))

        def too_late(path):
            data = wavfile.read(str(path))
            require_regular(path)
            return data

        def numpy_load(np, path):
            return np.load(path)

        def archive(gzip, wave, zipfile, path):
            gzip.open(path)
            wave.open(str(path), "rb")
            zipfile.ZipFile(path)

        def written(gzip, wave, zipfile, path):
            gzip.open(path, "wb")
            wave.open(str(path), mode="wb")
            zipfile.ZipFile(path, "w")
        """,
    ) == [
        ("described", _FOREIGN),
        ("another_name", _FOREIGN),
        ("too_late", _FOREIGN),
        ("numpy_load", _FOREIGN),
        ("archive", _FOREIGN),
        ("archive", _FOREIGN),
        ("archive", _FOREIGN),
    ]


def test_a_soundfile_opened_to_write_is_no_read(tmp_path: pathlib.Path) -> None:
    assert _found(
        tmp_path,
        """
        def write(sf, target):
            with sf.SoundFile(str(target), "w", samplerate=48000, channels=1):
                pass

        def read(sf, source):
            with sf.SoundFile(str(source)) as handle:
                return handle.read()
        """,
    ) == [("read", _FOREIGN)]


def test_a_file_object_opened_by_its_name_is_an_open_of_its_own(
    tmp_path: pathlib.Path,
) -> None:
    """``io.FileIO`` opens the name as ``open`` does, and a pipe there waits as long."""
    assert _found(
        tmp_path,
        """
        import io
        from io import FileIO

        def through_io(path):
            return io.BufferedReader(io.FileIO(path, "rb"))

        def imported(path):
            return FileIO(path)

        def written(path):
            return io.FileIO(path, "wb")
        """,
    ) == [("through_io", _OWN), ("imported", _OWN)]


def test_a_reader_is_known_by_what_its_module_binds_it_to(
    tmp_path: pathlib.Path,
) -> None:
    """A reader imported by its name, or under another, opens the name all the same."""
    assert _found(
        tmp_path,
        """
        import soundfile
        import soundfile as snd
        from numpy import load
        from scipy.io.wavfile import read as wav_read

        def by_name(path):
            return wav_read(path)

        def by_alias(path):
            return snd.info(str(path))

        def by_assignment(path):
            stream = soundfile
            return stream.read(str(path))

        def bare(path):
            return load(path)

        def checked(path):
            require_regular(path)
            return wav_read(path)
        """,
    ) == [
        ("by_name", _FOREIGN),
        ("by_alias", _FOREIGN),
        ("by_assignment", _FOREIGN),
        ("bare", _FOREIGN),
    ]


def test_a_copy_reads_its_source_by_its_name(tmp_path: pathlib.Path) -> None:
    """shutil opens the source itself: a pipe there keeps the copy waiting."""
    assert _found(
        tmp_path,
        """
        import shutil
        from shutil import copy2 as keep

        def copied(path, target):
            shutil.copyfile(path, target)
            shutil.copy(path, target)

        def kept(path, target):
            keep(path, target)

        def checked(path, target):
            require_regular(path)
            shutil.copyfile(path, target)
        """,
    ) == [("copied", _FOREIGN), ("copied", _FOREIGN), ("kept", _FOREIGN)]


def test_an_open_imported_from_another_module_is_that_module_s(
    tmp_path: pathlib.Path,
) -> None:
    """``open`` bound by an import is that module's reader, not the built-in."""
    assert _found(
        tmp_path,
        """
        from gzip import open as gz_open
        from io import open

        def archive(path):
            return gz_open(path)

        def through_io(path):
            return open(path, "rb")

        def written(path):
            return gz_open(path, "wb")
        """,
    ) == [("archive", _FOREIGN), ("through_io", _OWN)]


def test_a_check_counts_through_helpers_that_hand_it_their_first_parameter(
    tmp_path: pathlib.Path,
) -> None:
    """A reader that checks its own name is a check for its callers."""
    helpers = """
    from phonometry._internal.json_input import open_regular

    def open_audio(path):
        return open_regular(Path(path))

    def sniff(path):
        with open_audio(path) as fh:
            return fh.read(12)

    def not_a_check(path, other):
        return open_regular(other)
    """
    assert _found(
        tmp_path,
        """
        def read(sf, path):
            sniff(path)
            return sf.read(str(path))

        def unchecked(sf, path, other):
            not_a_check(path, other)
            return sf.read(str(path))
        """,
        helpers=helpers,
    ) == [("unchecked", _FOREIGN)]


def test_the_shared_module_is_the_check_and_is_not_read(tmp_path: pathlib.Path) -> None:
    owner = tmp_path / "phonometry" / "_internal" / "json_input.py"
    owner.parent.mkdir(parents=True)
    owner.write_text(
        "def read_at_most(path, limit):\n    return open(path, 'rb').read(limit)\n",
        encoding="utf-8",
    )
    findings, _stale = crf.check([owner])
    assert findings == []


def test_an_exemption_covers_its_function_and_one_that_covers_nothing_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    reader = tmp_path / "reader.py"
    reader.write_text("def own():\n    return VERSION.read_text()\n", encoding="utf-8")
    key = (crf.relative(reader), "own")
    saved = dict(crf.EXEMPT)
    try:
        crf.EXEMPT.clear()
        crf.EXEMPT[key] = "the library's own file"
        crf.EXEMPT[(crf.relative(reader), "gone")] = "a read that was removed"
        findings, stale = crf.check([reader])
    finally:
        crf.EXEMPT.clear()
        crf.EXEMPT.update(saved)
    assert findings == []
    assert stale == [(crf.relative(reader), "gone")]


def test_the_library_reads_every_name_through_the_check() -> None:
    """The gate passes on the library as it stands, and every exemption is used."""
    files = crf.python_files([], crf.SOURCE)
    findings, stale = crf.check(files)
    assert [finding.describe() for finding in findings] == []
    assert stale == []


def test_main_exits_one_on_a_read_and_zero_without(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    reader = tmp_path / "reader.py"
    reader.write_text("def f(path):\n    return path.read_bytes()\n", encoding="utf-8")
    assert crf.main([str(reader)]) == 1
    assert "reader.py:2  f  an open of its own" in capsys.readouterr().out
    reader.write_text("def f(path):\n    return path.name\n", encoding="utf-8")
    assert crf.main([str(reader)]) == 0
