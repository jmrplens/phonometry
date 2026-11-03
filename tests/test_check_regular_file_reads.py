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
own name or another, or bound to another by an assignment, a copy of
``shutil``, which reads its source by its name, and a call that only shares a
check's name (``np.info`` beside the library's ``info``), which the gate took
for the check, and an import in one function, which the gate let rename a
reader in every other. A check is known by the module that defines it, and
reached through a relative import, a module, a package that imports it,
``self`` or a function around the call; a name stands for what its own scope
binds it to.
"""

from __future__ import annotations

import pathlib
import sys
import textwrap

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_regular_file_reads as crf
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
        from check import require_regular
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
        from check import require_regular
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


def test_a_name_stands_for_what_its_own_scope_binds_it_to(
    tmp_path: pathlib.Path,
) -> None:
    """An import or a parameter binds a name in its own scope, as Python reads it.

    A function that imports another module under ``np`` or ``snd`` leaves the
    name of every other function as it was; a class body's import is not seen
    by the class's methods; a parameter hides the module's name; a function
    nested in another sees what the other binds; and a check imported in one
    function counts in that function only.
    """
    assert _found(
        tmp_path,
        """
        import math as sf
        import numpy as np

        def unrelated():
            import math as np
            return np.pi

        def loaded(path):
            return np.load(path)

        class Holder:
            import math as np

            def load(self, path):
                return np.load(path)

        class Table:
            import soundfile as snd

            DATA = snd.read("table.wav")

        def given(sf, path):
            return sf.info(str(path))

        def outer(path):
            import soundfile as snd

            def inner():
                return snd.info(str(path))

            return inner

        def checked(sf, path):
            from check import require_regular

            require_regular(path)
            return sf.read(str(path))

        def unchecked(sf, path):
            require_regular(path)
            return sf.read(str(path))

        def first(path):
            import soundfile as snd
            return snd.read(str(path))

        def second(path):
            import pickle as snd
            return snd.load(path)
        """,
    ) == [
        ("loaded", _FOREIGN),
        ("Holder.load", _FOREIGN),
        ("Table", _FOREIGN),
        ("given", _FOREIGN),
        ("outer.inner", _FOREIGN),
        ("unchecked", _FOREIGN),
        ("first", _FOREIGN),
    ]


def test_a_copy_reads_its_source_by_its_name(tmp_path: pathlib.Path) -> None:
    """shutil opens the source itself: a pipe there keeps the copy waiting."""
    assert _found(
        tmp_path,
        """
        import shutil
        from shutil import copy2 as keep

        from check import require_regular

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
        from check import not_a_check, sniff

        def read(sf, path):
            sniff(path)
            return sf.read(str(path))

        def unchecked(sf, path, other):
            not_a_check(path, other)
            return sf.read(str(path))
        """,
        helpers=helpers,
    ) == [("unchecked", _FOREIGN)]


#: A module of checks with the short names of the library's own: ``info``
#: asks what the name holds, as ``io.info`` does, and ``described`` hands its
#: name to NumPy's ``info``, which asks nothing.
_NAMESAKES = """
import numpy as np
from phonometry._internal.json_input import not_regular_at

def info(path):
    if not_regular_at(Path(path)) is not None:
        raise ValueError(path)

def require_regular(path):
    info(path)

def described(path):
    return np.info(path)
"""


def test_a_call_that_shares_a_check_s_name_is_no_check(
    tmp_path: pathlib.Path,
) -> None:
    """A check is known by the module that defines it, not by the last part of its name.

    ``np.info(path)`` before ``np.load(path)`` asks nothing of the name,
    though the library's ``info`` is a check; nor does a method of another
    object called ``read_at_most``, nor a function of the reader's own module
    that is called ``require_regular`` and checks nothing.
    """
    assert _found(
        tmp_path,
        """
        import numpy as np

        def numpy_info(path):
            np.info(path)
            return np.load(path)

        def a_method(handle, sf, path):
            handle.read_at_most(path)
            return sf.read(str(path))

        def require_regular(path):
            return None

        def own_namesake(sf, path):
            require_regular(path)
            return sf.info(str(path))
        """,
        helpers=_NAMESAKES,
    ) == [
        ("numpy_info", _FOREIGN),
        ("a_method", _FOREIGN),
        ("own_namesake", _FOREIGN),
    ]


def test_a_helper_that_hands_its_name_to_a_namesake_of_a_check_is_no_check(
    tmp_path: pathlib.Path,
) -> None:
    """``described`` hands its name to ``np.info``, which is not the library's ``info``."""
    assert _found(
        tmp_path,
        """
        from check import described, require_regular

        def unchecked(sf, path):
            described(path)
            return sf.read(str(path))

        def checked(sf, path):
            require_regular(path)
            return sf.read(str(path))
        """,
        helpers=_NAMESAKES,
    ) == [("unchecked", _FOREIGN)]


def test_a_check_is_found_however_the_module_reaches_it(tmp_path: pathlib.Path) -> None:
    """Through a relative import, a module, a package that imports it, ``self``, a nested function."""
    package = tmp_path / "phonometry" / "io"
    package.mkdir(parents=True)
    sources = {
        "__init__.py": "from ._audio_file import require_regular_audio\n",
        "_audio_file.py": """
            from .._internal.json_input import not_regular_at

            def require_regular_audio(path):
                if not_regular_at(Path(path)) is not None:
                    raise ValueError(path)
            """,
        "_backends.py": """
            from . import _audio_file
            from ._audio_file import require_regular_audio
            from phonometry import io
            from phonometry._internal import json_input
            from phonometry.io import require_regular_audio as exported

            def relative(sf, path):
                require_regular_audio(path)
                return sf.read(str(path))

            def through_the_module(sf, path):
                _audio_file.require_regular_audio(path)
                return sf.info(str(path))

            def through_the_package(sf, path):
                exported(path)
                io.require_regular_audio(path)
                return sf.blocks(str(path))

            def shared(sf, path):
                json_input.not_regular_at(Path(path))
                return sf.read(str(path))

            def nested(sf, path):
                def ask(name):
                    require_regular_audio(name)

                ask(path)
                return sf.read(str(path))

            class Reader:
                def _ask(self, path):
                    require_regular_audio(path)

                def read(self, sf, path):
                    self._ask(path)
                    return sf.read(str(path))
            """,
    }
    for name, source in sources.items():
        (package / name).write_text(textwrap.dedent(source), encoding="utf-8")
    findings, _stale = crf.check(sorted(package.iterdir()))
    assert [finding.describe() for finding in findings] == []


def test_a_function_defined_inside_a_block_is_read(tmp_path: pathlib.Path) -> None:
    """A reader written for one version of Python, or as a fallback, is read too.

    The walk of the functions went from a module, a class or a function only
    to the definitions directly in it, and the walk of a function's own code
    stops at the definitions in it, so a function written inside an ``if``,
    a ``try`` or a ``with`` was read by neither: its open passed unseen, and
    a check written that way counted for no reader.
    """
    assert _found(
        tmp_path,
        """
        import sys

        import numpy as np

        from phonometry._internal.json_input import not_regular_at

        if sys.version_info >= (3, 13):
            def _sniff(path):
                return open(path, "rb").read(12)
        else:
            def _sniff(path):
                with Path(path).open("rb") as fh:
                    return fh.read(12)

        try:
            import soundfile as sf
        except ImportError:
            sf = None
        else:
            def _probe(path):
                return sf.info(str(path))

        class Reader:
            if sys.platform == "win32":
                def load(self, path):
                    return np.load(path)

        def opener(path):
            with Path(path).parent as folder:
                def inner(name):
                    return (folder / name).read_bytes()
            return inner

        if sys.version_info >= (3, 12):
            def require(path):
                if not_regular_at(Path(path)) is not None:
                    raise ValueError(path)

        def checked(path):
            require(path)
            return np.load(path)
        """,
    ) == [
        ("_sniff", _OWN),
        ("_sniff", _OWN),
        ("_probe", _FOREIGN),
        ("Reader.load", _FOREIGN),
        ("opener.inner", _OWN),
    ]


#: A module whose own check is called ``info``, and readers in which that name
#: is bound to something else before the call.
_SHADOWED = """
import numpy as np

from phonometry._internal.json_input import not_regular_at

def info(path):
    if not_regular_at(Path(path)) is not None:
        raise ValueError(path)

def checked(path):
    info(path)
    return np.load(path)

def by_an_import(path):
    from numpy import info
    info(path)
    return np.load(path)

def by_a_parameter(info, path):
    info(path)
    return np.load(path)

def by_an_assignment(path):
    info = make_describer()
    info(path)
    return np.load(path)

def by_a_loop(path, describers):
    for info in describers:
        info(path)
    return np.load(path)

def outer(path):
    from numpy import info

    def inner():
        info(path)
        return np.load(path)

    return inner
"""


def test_a_name_bound_in_the_reader_s_own_scope_hides_the_module_s_check(
    tmp_path: pathlib.Path,
) -> None:
    """Python looks a name up in the function first, then around it, then the module.

    The module's own functions were looked at before the reader's imports,
    parameters and assignments, so ``info(path)`` counted as the module's
    check ``info`` even where the reader had bound ``info`` to ``numpy.info``,
    to a parameter or to anything else, and the ``np.load`` after it passed.
    """
    assert _found(tmp_path, _SHADOWED) == [
        ("by_an_import", _FOREIGN),
        ("by_a_parameter", _FOREIGN),
        ("by_an_assignment", _FOREIGN),
        ("by_a_loop", _FOREIGN),
        ("outer.inner", _FOREIGN),
    ]


#: A module whose own check is called ``info``, and readers in which a scope
#: inside the reader binds that name for itself, or the reader declares it
#: ``global``, or binds it twice.
_SCOPED = """
import numpy as np

from phonometry._internal.json_input import not_regular_at

def info(path):
    if not_regular_at(Path(path)) is not None:
        raise ValueError(path)

def beside_a_comprehension(path, describers):
    info(path)
    names = [info.name for info in describers]
    return np.load(path), names

def beside_a_nested_store(path):
    info(path)

    def describe():
        info = make_describer()
        return info

    return np.load(path), describe

def beside_a_lambda(path):
    info(path)
    show = lambda: (info := make_describer())
    return np.load(path), show

def outer(path):
    def info(name):
        return name

    def inner():
        global info
        info(path)
        return np.load(path)

    return inner

def defined_then_rebound(path):
    def info(name):
        if not_regular_at(Path(name)) is not None:
            raise ValueError(name)

    info = make_describer()
    info(path)
    return np.load(path)
"""


def test_a_name_is_looked_up_in_the_scope_the_call_runs_in(
    tmp_path: pathlib.Path,
) -> None:
    """Only the scopes a call runs in, and what each binds of its own, say what a name is.

    A comprehension's loop target, a name a nested function or a lambda
    stores in, hid the module's check ``info`` in the reader around them,
    and a name the reader declares ``global`` was looked up in the function
    around it, which defines a namesake that checks nothing: the check
    before ``np.load`` was not seen and the read was refused. A name a
    scope both defines and rebinds was read as the definition, which the
    rebinding replaced before the call, and the unchecked read passed.
    """
    assert _found(tmp_path, _SCOPED) == [("defined_then_rebound", _FOREIGN)]


def test_a_function_of_the_module_another_rebinds_under_global_is_no_check(
    tmp_path: pathlib.Path,
) -> None:
    """A function that declares the module's ``info`` global and binds it may
    run before the reader does, so ``info`` may be what it bound there and
    not the check the module defines: the reader is refused, as it is when
    the module rebinds the name at its top.
    """
    source = """
        import numpy as np

        from phonometry._internal.json_input import not_regular_at

        def info(path):
            if not_regular_at(Path(path)) is not None:
                raise ValueError(path)

        def _swap():
            global info
            info = make_describer()

        def reader(path):
            info(path)
            return np.load(path)
        """
    assert _found(tmp_path, source) == [("reader", _FOREIGN)]


@pytest.mark.parametrize(
    ("rebinding", "found"),
    [
        ("require_regular = make_describer()", [("reader", _FOREIGN)]),
        ("from check import require_regular", []),
    ],
    ids=["another-value", "the-same-import"],
)
def test_an_import_a_function_rebinds_under_global_is_read_as_it_may_stand(
    tmp_path: pathlib.Path, rebinding: str, found: list[tuple[str, str]]
) -> None:
    """The module's import of the check is what ``require_regular`` holds only
    while no function that declares it ``global`` has bound it to something
    else; the module's names were read from its top alone, so the import
    stood for the name after such a function replaced it.
    """
    source = f"""
        import numpy as np

        from check import require_regular

        def _swap():
            global require_regular
            {rebinding}

        def reader(path):
            require_regular(path)
            return np.load(path)
        """
    assert _found(tmp_path, source) == found


#: A module that defines one reader in each branch of an ``if``, and one in
#: each block of a ``try``, where only one of the two binds ``info`` itself.
_TWO_BRANCHES = """
import sys

import numpy as np

from phonometry._internal.json_input import not_regular_at

def info(path):
    if not_regular_at(Path(path)) is not None:
        raise ValueError(path)

if sys.version_info >= (3, 13):
    def by_version(path):
        from numpy import info
        info(path)
        return np.load(path)
else:
    def by_version(path):
        return np.load(path)

try:
    def by_fallback(path):
        from numpy import info
        info(path)
        return np.load(path)
except ImportError:
    def by_fallback(path):
        info(path)
        return np.load(path)
"""


def test_each_definition_of_a_name_binds_its_own_names(
    tmp_path: pathlib.Path,
) -> None:
    """Two readers of one name, one in each branch, are two scopes.

    The names each scope binds were kept by its qualified name, so the
    second definition's stood for both: the ``if`` reader that binds
    ``info`` to ``numpy.info`` was read with the ``else`` reader's names,
    in which ``info`` is the module's check, and its ``np.load`` passed; the
    ``try`` reader passed the same way behind the ``except`` one.
    """
    assert sorted(_found(tmp_path, _TWO_BRANCHES)) == [
        ("by_fallback", _FOREIGN),
        ("by_version", _FOREIGN),
        ("by_version", _FOREIGN),
    ]


def test_a_check_defined_in_two_branches_counts_only_when_both_check(
    tmp_path: pathlib.Path,
) -> None:
    """A name is a check only when every definition of it checks its name.

    A check that asks what the name holds on one version of Python and hands
    the name back untouched on the other leaves the read unchecked on that
    one; the gate counted it as a check because one of its two definitions
    is.
    """
    source = """
        import sys

        import numpy as np

        from check import require_regular
        from phonometry._internal.json_input import not_regular_at

        if sys.version_info >= (3, 13):
            def check(path):
                if not_regular_at(Path(path)) is not None:
                    raise ValueError(path)
        else:
            def check(path):
                return path

        if sys.version_info >= (3, 13):
            def both(path):
                if not_regular_at(Path(path)) is not None:
                    raise ValueError(path)
        else:
            def both(path):
                require_regular(path)

        def reader(path):
            check(path)
            return np.load(path)

        def checked(path):
            both(path)
            return np.load(path)
        """
    assert _found(tmp_path, source, helpers=_CHECK) == [("reader", _FOREIGN)]


def test_a_check_a_later_definition_replaces_counts_as_the_later_one(
    tmp_path: pathlib.Path,
) -> None:
    """A name is the definition it holds once the module has run.

    Every definition of a name counted, so a first ``check`` that hands the
    name back untouched, replaced by a second that asks what the name holds,
    left the read behind it refused, though no call ever runs the first.
    """
    source = """
        import numpy as np

        from check import require_regular

        def check(path):
            return path

        def check(path):
            require_regular(path)

        def reader(path):
            check(path)
            return np.load(path)
        """
    assert _found(tmp_path, source, helpers=_CHECK) == []


def test_a_method_of_a_class_a_later_class_replaces_is_no_definition(
    tmp_path: pathlib.Path,
) -> None:
    """A method is read in the class that holds it, and a class a later one
    of its name replaces holds none the module keeps.

    The methods of two ``Reader`` classes were read against each other, and
    two blocks that share nothing keep both, so the check of the second
    ``Reader`` counted only when the first, which no call reaches, checked
    as well.
    """
    source = """
        import numpy as np

        from check import require_regular

        class Reader:
            def check(path):
                return path

        class Reader:
            def check(path):
                require_regular(path)

        def reader(path):
            Reader.check(path)
            return np.load(path)
        """
    assert _found(tmp_path, source, helpers=_CHECK) == []


def test_a_package_re_exports_what_any_compound_statement_imports(
    tmp_path: pathlib.Path,
) -> None:
    """An import written in a ``with``, a ``match`` or a loop at the top of a
    package's ``__init__`` re-exports the name as one written at the top does.

    The re-exports of a package were read through ``if`` and ``try`` alone,
    so a check the package imports inside a ``with`` was no check for a
    module that reaches it through the package, and the read was refused.
    """
    package = tmp_path / "phonometry" / "io"
    package.mkdir(parents=True)
    sources = {
        "__init__.py": """
            from contextlib import suppress

            with suppress(ImportError):
                from ._audio_file import require_regular_audio
            """,
        "_audio_file.py": """
            from .._internal.json_input import not_regular_at

            def require_regular_audio(path):
                if not_regular_at(Path(path)) is not None:
                    raise ValueError(path)
            """,
        "_backends.py": """
            from phonometry.io import require_regular_audio as exported

            def through_the_package(sf, path):
                exported(path)
                return sf.read(str(path))
            """,
    }
    for name, source in sources.items():
        (package / name).write_text(textwrap.dedent(source), encoding="utf-8")
    findings, _stale = crf.check(sorted(package.iterdir()))
    assert [finding.describe() for finding in findings] == []


def test_a_package_re_exports_the_later_of_two_imports_of_one_name(
    tmp_path: pathlib.Path,
) -> None:
    """Of two imports of one name at the top of a package's ``__init__``, the
    package re-exports the later, which Python leaves in place.

    The re-exports were read from the last statement up, so the earlier
    import, the check, stood for the name, and a module that reaches the
    later one through the package, which checks nothing, read unchecked.
    """
    package = tmp_path / "phonometry" / "io"
    package.mkdir(parents=True)
    sources = {
        "__init__.py": """
            from ._audio_file import require_regular_audio
            from ._loose import check_nothing as require_regular_audio
            """,
        "_audio_file.py": """
            from .._internal.json_input import not_regular_at

            def require_regular_audio(path):
                if not_regular_at(Path(path)) is not None:
                    raise ValueError(path)
            """,
        "_loose.py": """
            def check_nothing(path):
                return path
            """,
        "_backends.py": """
            from phonometry.io import require_regular_audio as exported

            def through_the_package(sf, path):
                exported(path)
                return sf.read(str(path))
            """,
    }
    for name, source in sources.items():
        (package / name).write_text(textwrap.dedent(source), encoding="utf-8")
    findings, _stale = crf.check(sorted(package.iterdir()))
    assert [(finding.function, finding.line) for finding in findings] == [
        ("through_the_package", 6)
    ]


#: The modules beside a package ``__init__`` whose re-export of the check
#: :func:`_read_through_the_package` varies: the check, a function that
#: checks nothing, and a module that reaches the name through the package.
_BESIDE_THE_PACKAGE = {
    "_audio_file.py": """
        from .._internal.json_input import not_regular_at

        def require_regular_audio(path):
            if not_regular_at(Path(path)) is not None:
                raise ValueError(path)
        """,
    "_loose.py": """
        def check_nothing(path):
            return path
        """,
    "_backends.py": """
        from phonometry.io import require_regular_audio as exported

        def through_the_package(sf, path):
            exported(path)
            return sf.read(str(path))
        """,
}


def _read_through_the_package(
    tmp_path: pathlib.Path, init: str
) -> list[tuple[str, int]]:
    """The findings of a package whose ``__init__`` is *init*, beside
    :data:`_BESIDE_THE_PACKAGE`, as ``(function, line)``.
    """
    package = tmp_path / "phonometry" / "io"
    package.mkdir(parents=True)
    for name, source in {"__init__.py": init, **_BESIDE_THE_PACKAGE}.items():
        (package / name).write_text(textwrap.dedent(source), encoding="utf-8")
    findings, _stale = crf.check(sorted(package.iterdir()))
    return [(finding.function, finding.line) for finding in findings]


@pytest.mark.parametrize(
    "init",
    [
        """
        try:
            from ._loose import check_nothing as require_regular_audio
        except ImportError:
            from ._audio_file import require_regular_audio
        """,
        """
        try:
            from ._audio_file import require_regular_audio
        except ImportError:
            from ._loose import check_nothing as require_regular_audio
        """,
        """
        if FAST:
            from ._loose import check_nothing as require_regular_audio
        else:
            from ._audio_file import require_regular_audio
        """,
        """
        if FAST:
            from ._audio_file import require_regular_audio
        else:
            from ._loose import check_nothing as require_regular_audio
        """,
    ],
    ids=["try-loose", "try-check", "if-loose", "else-loose"],
)
def test_a_re_export_two_branches_disagree_on_reaches_no_check(
    tmp_path: pathlib.Path, init: str
) -> None:
    """Two imports of one name in the branches of a ``try`` or an ``if`` of a
    package's ``__init__`` may each be what the package re-exports, so a name
    they bind to two functions reaches neither, and the read is unchecked.

    The later of the two stood for the name, so a check imported in the
    ``except`` clause or the ``else`` hid the function that checks nothing in
    the ``try`` body or the ``if``, which runs whenever its import works.
    """
    assert _read_through_the_package(tmp_path, init) == [("through_the_package", 6)]


def test_a_re_export_two_branches_agree_on_reaches_the_check(
    tmp_path: pathlib.Path,
) -> None:
    """Two imports of one name in the branches of a ``try`` that bind it to
    the same check reach it, whichever runs.
    """
    init = """
        try:
            from ._audio_file import require_regular_audio
        except ImportError:
            from ._audio_file import require_regular_audio
        """
    assert _read_through_the_package(tmp_path, init) == []


@pytest.mark.parametrize(
    ("init", "found"),
    [
        (
            """
            from ._audio_file import require_regular_audio
            from ._loose import check_nothing
            require_regular_audio = check_nothing
            """,
            [("through_the_package", 6)],
        ),
        (
            """
            from ._audio_file import require_regular_audio

            def require_regular_audio(path):
                return path
            """,
            [("through_the_package", 6)],
        ),
        (
            """
            from ._audio_file import require_regular_audio
            from .._internal.json_input import not_regular_at

            def require_regular_audio(path):
                if not_regular_at(Path(path)) is not None:
                    raise ValueError(path)
            """,
            [],
        ),
        (
            """
            from ._audio_file import require_regular_audio
            from ._loose import check_nothing

            def _swap():
                global require_regular_audio
                require_regular_audio = check_nothing
            """,
            [("through_the_package", 6)],
        ),
        (
            """
            from ._audio_file import require_regular_audio

            def _reload():
                global require_regular_audio
                from ._audio_file import require_regular_audio
            """,
            [],
        ),
    ],
    ids=[
        "assignment",
        "def-that-checks-nothing",
        "def-that-checks",
        "global-assignment-in-a-function",
        "global-import-of-the-same-check",
    ],
)
def test_a_binding_after_a_re_export_takes_the_name_from_it(
    tmp_path: pathlib.Path, init: str, found: list[tuple[str, int]]
) -> None:
    """An assignment or a ``def`` after an import of one name in a package's
    ``__init__`` is what the package holds under it, so a module that reaches
    the name through the package reaches that, not the import.

    The re-exports were read from the imports alone, so the check imported
    first stood for the name after ``require_regular_audio = check_nothing``
    or a ``def`` that checks nothing replaced it. A function that declares
    the name ``global`` and binds it may run at any time, so what it binds
    may be what the package holds too; the bindings at the top of the
    module were read alone, and the check stood for the name after such a
    function replaced it.
    """
    assert _read_through_the_package(tmp_path, init) == found


def test_an_annotation_after_a_re_export_leaves_the_name_to_it(
    tmp_path: pathlib.Path,
) -> None:
    """An annotation without a value binds nothing, so the package still
    holds the check it imported under the name.

    ``require_regular_audio: Callable[..., None]`` after the import was read
    as a binding that replaced it, and a module that reaches the check
    through the package was reported as reaching no check.
    """
    init = """
        from collections.abc import Callable

        from ._audio_file import require_regular_audio

        require_regular_audio: Callable[..., None]
        """
    assert _read_through_the_package(tmp_path, init) == []


def test_a_check_is_the_import_that_stands_for_its_name_at_the_call(
    tmp_path: pathlib.Path,
) -> None:
    """Of two imports of one name in a scope, the call reaches the one that
    stands for the name where it runs.

    A scope's names were read into one table, one import of a name standing
    for it everywhere, the first one written as the walk went, so a
    ``require_regular`` imported from the check module counted as the check
    though a second import, which checks nothing, replaced it before the
    call.
    """
    replaced = """
        import numpy as np

        def reader(path):
            from check import require_regular
            from other import require_regular

            require_regular(path)
            return np.load(path)
        """
    either = """
        import numpy as np

        def reader(path, fast):
            if fast:
                from check import require_regular
            else:
                from other import require_regular
            require_regular(path)
            return np.load(path)
        """
    assert _found(tmp_path, replaced, helpers=_CHECK) == [("reader", _FOREIGN)]
    assert _found(tmp_path, either, helpers=_CHECK) == [("reader", _FOREIGN)]


def test_a_function_meets_every_import_of_the_module_from_its_def_on(
    tmp_path: pathlib.Path,
) -> None:
    """A call inside a function reads the module's name when the function
    runs, which may be during the import and before a later import of the
    name, so every import that may stand from the ``def`` on is one it may
    reach; one that a later import replaces before the ``def`` is not.

    The function read the module's imports as they stand once it has run, so
    the check imported after it hid the import that checks nothing, which a
    call made at once, ``TABLE = reader(...)``, reaches.
    """
    called_early = """
        import numpy as np
        from other import require_regular

        def reader(path):
            require_regular(path)
            return np.load(path)

        TABLE = reader("table.npy")
        from check import require_regular
        """
    replaced_before = """
        import numpy as np
        from other import require_regular
        from check import require_regular

        def reader(path):
            require_regular(path)
            return np.load(path)
        """
    assert _found(tmp_path, called_early, helpers=_CHECK) == [("reader", _FOREIGN)]
    assert _found(tmp_path, replaced_before, helpers=_CHECK) == []


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
