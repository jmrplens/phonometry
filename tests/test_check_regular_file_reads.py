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


def test_what_an_if_type_checking_block_imports_is_no_callee(
    tmp_path: pathlib.Path,
) -> None:
    """An import under ``if TYPE_CHECKING:`` never runs, so ``open`` is still
    the builtin. It was read as what the name stands for, at the top of a
    module and under ``global`` in a function, so a whole read passed for a
    call of ``pathlib.Path``.
    """
    assert _found(
        tmp_path,
        """
        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            from pathlib import Path as open

        def at_the_top(path):
            with open(path) as handle:
                return handle.read()
        """,
    ) == [("at_the_top", _OWN)]
    assert _found(
        tmp_path,
        """
        from typing import TYPE_CHECKING

        def swap():
            global open
            if TYPE_CHECKING:
                from pathlib import Path as open

        def under_global(path):
            with open(path) as handle:
                return handle.read()
        """,
    ) == [("under_global", _OWN)]


@pytest.mark.parametrize(
    ("call", "found"),
    [
        pytest.param(
            "(lambda open=open: open(path))()", [("read", _OWN)], id="default"
        ),
        pytest.param("(lambda open=open: open(path))(print)", [], id="positional"),
        pytest.param("(lambda open=open: open(path))(open=print)", [], id="keyword"),
        pytest.param(
            "(lambda opener=print: opener(path))(open)",
            [("read", _OWN)],
            id="open-handed",
        ),
        pytest.param("(lambda open=open: open(path))(*handlers)", [], id="starred"),
        pytest.param(
            "(lambda open=open, /, **kwargs: open(path))(open=print)",
            [("read", _OWN)],
            id="keyword-of-a-positional-only-name",
        ),
        pytest.param(
            "(lambda open=open, /, **kwargs: open(path))(**{})",
            [("read", _OWN)],
            id="mapping-beside-a-positional-only-one",
        ),
        pytest.param(
            "(lambda open=open, /, **kwargs: open(path))(print, **{})",
            [],
            id="positional-only-handed-in-its-place",
        ),
    ],
)
def test_a_lambda_called_where_it_is_written_reads_what_the_call_hands(
    tmp_path: pathlib.Path, call: str, found: list[tuple[str, str]]
) -> None:
    """A lambda called where it is written holds in each parameter what the
    call hands it, and its default only where the call hands nothing; a
    ``*`` argument may hand it anything.

    The parameter was read as its default whatever the call handed, so
    ``print`` handed in for ``open`` read as a read of ``open``, and ``open``
    handed in for a parameter whose default is ``print`` passed. A keyword,
    or a ``**`` mapping, fills no positional-only parameter: what it hands
    goes to ``**kwargs``, and the default stands.
    """
    source = f"def read(path, handlers=()):\n    return {call}\n"
    assert _found(tmp_path, source) == found


@pytest.mark.parametrize(
    ("source", "found"),
    [
        pytest.param(
            """
            import io
            open = io.open

            def read(path, opener=open):
                with opener(path) as fh:
                    return fh.read()

            open = print
            """,
            [("read", _OWN)],
            id="rebound-after-the-def",
        ),
        pytest.param(
            """
            import io
            open = print

            def read(path, opener=open):
                with opener(path) as fh:
                    return fh.read()

            open = io.open
            """,
            [],
            id="rebound-before-the-def",
        ),
        pytest.param(
            """
            import io

            def outer(path):
                source = io.open
                def read(path, opener=source):
                    with opener(path) as fh:
                        return fh.read()
                source = print
                return read(path)
            """,
            [("outer.read", _OWN)],
            id="in-a-function",
        ),
        pytest.param(
            """
            import io
            open = io.open

            class R:
                def read(self, path, opener=open):
                    with opener(path) as fh:
                        return fh.read()

            open = print
            """,
            [("R.read", _OWN)],
            id="a-method-rebound-after-the-class",
        ),
        pytest.param(
            """
            import io
            open = print

            class R:
                def read(self, path, opener=open):
                    with opener(path) as fh:
                        return fh.read()

            open = io.open
            """,
            [],
            id="a-method-rebound-before-the-class",
        ),
        pytest.param(
            """
            import io

            def outer(path):
                source = io.open

                class R:
                    def read(self, path, opener=source):
                        with opener(path) as fh:
                            return fh.read()

                source = print
                return R().read(path)
            """,
            [("outer.R.read", _OWN)],
            id="a-method-of-a-class-in-a-function",
        ),
        pytest.param(
            """
            import io
            open = io.open

            class R:
                reader = lambda path, opener=open: opener(path).read()

            open = print
            """,
            [("R", _OWN)],
            id="a-lambda-in-a-class-body",
        ),
    ],
)
def test_a_default_is_what_its_name_holds_where_the_def_runs(
    tmp_path: pathlib.Path, source: str, found: list[tuple[str, str]]
) -> None:
    """A parameter's default runs once, where the ``def`` does, so it is what
    the name holds there, not what the scope binds it to by its end.

    The default was read through the scope's last binding of the name, so an
    ``open`` rebound to ``print`` after the ``def`` hid the read the default
    makes, and one rebound to ``io.open`` after it made a read of ``print``.
    """
    assert _found(tmp_path, source) == found


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            """
            import io

            def open(path):
                return None

            def read(path, opener=open):
                with opener(path) as fh:
                    return fh.read()

            open = io.open
            """,
            id="a-later-alias",
        ),
        pytest.param(
            """
            def open(path):
                return None

            def read(path, opener=open):
                with opener(path) as fh:
                    return fh.read()
            """,
            id="spelt-like-the-builtin",
        ),
        pytest.param(
            """
            class open:
                def __init__(self, path):
                    self.path = path

            def read(path, opener=open):
                with opener(path) as fh:
                    return fh.read()
            """,
            id="a-class",
        ),
    ],
)
def test_a_default_that_names_a_definition_of_the_module_reads_no_file(
    tmp_path: pathlib.Path, source: str
) -> None:
    """A default that names a ``def`` or a ``class`` of the module holds that
    function or class, which opens no file the guard can name.

    The name was read through the module's table of names and its spelling,
    so a later ``open = io.open``, or the spelling of the builtin itself,
    made the default stand for an ``open``, and a call of it was refused as
    a read.
    """
    assert _found(tmp_path, source) == []


@pytest.mark.parametrize(
    ("binding", "found"),
    [
        pytest.param("opener = io.open\n", [("read", _OWN)], id="standing-alias"),
        pytest.param("opener = io.open\nopener = lambda path: None\n", [], id="lambda"),
        pytest.param("opener = io.open\nopener = make()\n", [], id="call"),
        pytest.param(
            "from io import open as opener\nopener = lambda path: None\n",
            [],
            id="import-then-lambda",
        ),
        pytest.param(
            "opener = print\nfrom io import open as opener\n",
            [("read", _OWN)],
            id="alias-then-import",
        ),
    ],
)
def test_a_later_binding_of_another_kind_ends_an_alias(
    tmp_path: pathlib.Path, binding: str, found: list[tuple[str, str]]
) -> None:
    """A lambda or a call's result bound to a name after an import or an
    alias of it leaves the name standing for nothing the guard can name, and
    an import after an alias stands over it.

    A scope's table of names took its imports and then its assignments of a
    dotted name, whatever their order, and nothing else, so ``io.open`` stood
    past the lambda and a call of it was refused as a read, and an alias
    stood over the import after it.
    """
    source = (
        f"import io\n{binding}\n"
        "def read(path):\n    with opener(path) as fh:\n        return fh.read()\n"
    )
    assert _found(tmp_path, source) == found


@pytest.mark.parametrize(
    ("binding", "found"),
    [
        pytest.param("io = make()\nopener = io.open\n", [], id="head-rebound-before"),
        pytest.param(
            "opener = io.open\nio = make()\n",
            [("read", _OWN)],
            id="head-rebound-after",
        ),
        pytest.param(
            "from io import open as held\nheld = lambda path: None\nopener = held\n",
            [],
            id="name-rebound-before",
        ),
        pytest.param(
            "held = print\nopener = held\nfrom io import open as held\n",
            [],
            id="name-imported-after",
        ),
    ],
)
@pytest.mark.parametrize("where", ["at-the-top", "in-the-function"])
def test_an_alias_reads_its_value_where_the_assignment_runs(
    tmp_path: pathlib.Path, binding: str, found: list[tuple[str, str]], where: str
) -> None:
    """``opener = io.open`` holds what ``io`` stands for where the assignment
    runs: a call's result or a lambda bound to the name before the alias
    leaves the alias holding what the guard cannot name, and a binding after
    it changes nothing, at the top of the module and in the function.

    A scope's table of names took its imports and its aliases in the order
    of the source and nothing else, so the alias read ``io`` as the import
    before a call's result replaced it, and the read through it was refused;
    and an import after an alias of ``print`` made the alias a read.
    """
    call = "    with opener(path) as fh:\n        return fh.read()\n"
    if where == "at-the-top":
        source = f"import io\n{binding}\ndef read(path):\n{call}"
    else:
        inner = textwrap.indent(f"import io\n{binding}", "    ")
        source = f"def read(path):\n{inner}{call}"
    assert _found(tmp_path, source) == found


@pytest.mark.parametrize(
    "loop",
    [
        pytest.param("for opener in ():\n    pass\n", id="no-turn"),
        pytest.param("for opener in items:\n    break\n", id="left-at-once"),
        pytest.param("for opener in [print]:\n    pass\n", id="a-turn"),
    ],
)
@pytest.mark.parametrize("where", ["at-the-top", "in-the-function"])
def test_a_loop_s_target_leaves_what_the_name_held_standing(
    tmp_path: pathlib.Path, loop: str, where: str
) -> None:
    """A loop binds its target only on a turn it runs, and it may run none,
    so after it the name may still hold the alias before it, as after the
    branches of an ``if``.

    The target was read as bound on every way past the loop, so it ended
    ``opener = io.open`` and the read through it passed.
    """
    alias = "opener = io.open\n" + loop
    call = "    with opener(path) as fh:\n        return fh.read()\n"
    if where == "at-the-top":
        source = f"import io\n{alias}\ndef read(path):\n{call}"
    else:
        inner = textwrap.indent(alias, "    ")
        source = f"import io\n\ndef read(path, items):\n{inner}{call}"
    assert _found(tmp_path, source) == [("read", _OWN)]


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            """
            import io

            def read(path):
                if (opener := io.open) is not None:
                    pass
                with opener(path) as fh:
                    return fh.read()
            """,
            id="in-the-function",
        ),
        pytest.param(
            """
            import io

            if (open := io.open) is not None:
                pass

            def read(path, opener=open):
                with opener(path) as fh:
                    return fh.read()
            """,
            id="at-the-top-read-by-a-default",
        ),
    ],
)
def test_a_name_a_walrus_binds_is_read_as_an_assignment_would_be(
    tmp_path: pathlib.Path, source: str
) -> None:
    """``(opener := io.open)`` binds the name to what the value names, as
    ``opener = io.open`` does.

    Only an assignment statement was read as one, so a read through a name
    bound by ``:=`` passed as a call of nothing the guard could name.
    """
    assert _found(tmp_path, source) == [("read", _OWN)]


@pytest.mark.parametrize(
    "prelude",
    [
        "TYPE_CHECKING = True",
        "from settings import TYPE_CHECKING",
        "import os as typing\nTYPE_CHECKING = typing.environ",
    ],
)
def test_a_block_on_a_name_the_module_rebinds_runs(
    tmp_path: pathlib.Path, prelude: str
) -> None:
    """``if TYPE_CHECKING:`` keeps its body from running only where the name
    holds the flag of ``typing``. A module that binds the name to anything
    else runs the body, and a read there is refused: the body was emptied
    for its spelling alone, so the read passed.
    """
    source = (
        prelude
        + "\n\ndef _sniff(path):\n    if TYPE_CHECKING:\n"
        + "        with Path(path).open('rb') as fh:\n"
        + "            return fh.read(12)\n    return None\n"
    )
    assert _found(tmp_path, source) == [("_sniff", _OWN)]


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            """
            def read(path):
                if not TYPE_CHECKING:
                    return 1
                else:
                    return open(path).read()
            """,
            id="the-else-of-a-negated-test",
        ),
        pytest.param(
            """
            def read(path):
                return open(path).read() if TYPE_CHECKING else None
            """,
            id="a-branch-of-an-expression",
        ),
        pytest.param(
            """
            if TYPE_CHECKING:
                held = open("x").read()
            """,
            id="the-block-at-the-top-of-the-module",
        ),
        pytest.param(
            """
            if TYPE_CHECKING:
                def read(path):
                    return open(path).read()
            """,
            id="a-function-in-the-block-at-the-top",
        ),
        pytest.param(
            """
            class Reader:
                if TYPE_CHECKING:
                    def read(self, path):
                        return open(path).read()
            """,
            id="a-method-in-the-block",
        ),
    ],
)
def test_what_a_test_on_type_checking_keeps_from_running_reads_no_file(
    tmp_path: pathlib.Path, source: str
) -> None:
    """A read no run reaches waits on nothing. Each was refused."""
    planted = "from typing import TYPE_CHECKING\n" + textwrap.dedent(source)
    assert _found(tmp_path, planted) == []


@pytest.mark.parametrize(
    ("source", "function"),
    [
        pytest.param(
            """
            def read(path):
                if not TYPE_CHECKING:
                    return open(path).read()
            """,
            "read",
            id="the-body-of-a-negated-test",
        ),
        pytest.param(
            """
            def read(path):
                return None if TYPE_CHECKING else open(path).read()
            """,
            "read",
            id="the-else-of-an-expression",
        ),
        pytest.param(
            """
            if not TYPE_CHECKING:
                def read(path):
                    return open(path).read()
            """,
            "read",
            id="a-function-in-the-body-of-a-negated-test",
        ),
        pytest.param(
            """
            if TYPE_CHECKING:
                pass
            else:
                held = open("x").read()
            """,
            "<module>",
            id="the-else-of-the-block-at-the-top",
        ),
    ],
)
def test_the_branch_of_a_test_on_type_checking_that_runs_is_read(
    tmp_path: pathlib.Path, source: str, function: str
) -> None:
    """The branch that runs is a read like any other."""
    planted = "from typing import TYPE_CHECKING\n" + textwrap.dedent(source)
    assert _found(tmp_path, planted) == [(function, _OWN)]


@pytest.mark.parametrize(
    "source",
    [
        """
        def read(paths, openers):
            return [open(paths).read() for open in openers]
        """,
        """
        def read(path):
            return (lambda open: open(path))(print)
        """,
        """
        def read(path, open):
            return open(path).read()
        """,
        """
        def read(path):
            open = make_opener()
            return open(path).read()
        """,
        """
        def read(path):
            def open(name):
                return name
            return open(path)
        """,
        """
        def open(name):
            return name

        def read(path):
            return open(path)
        """,
        """
        import soundfile as sf

        def read(paths, readers):
            return [sf.read(paths) for sf in readers]
        """,
    ],
)
def test_a_name_bound_nearer_is_not_the_builtin_or_the_import(
    tmp_path: pathlib.Path, source: str
) -> None:
    """``open`` stands for the builtin only where nothing binds it, and a
    comprehension's or a lambda's own name stands for nothing the module
    imports. Each was read as the read of a file its spelling names.
    """
    assert _found(tmp_path, source) == []


@pytest.mark.parametrize(
    ("source", "shape"),
    [
        pytest.param(
            """
            import io

            open = io.open

            def read(path):
                with open(path) as handle:
                    return handle.read()
            """,
            _OWN,
            id="an-alias-at-the-top",
        ),
        pytest.param(
            """
            import io

            def read(path):
                open = io.open
                with open(path) as handle:
                    return handle.read()
            """,
            _OWN,
            id="an-alias-in-the-function",
        ),
        pytest.param(
            """
            import io

            open = io.open

            def read(path):
                def inner():
                    return open(path).read()
                return inner()
            """,
            _OWN,
            id="an-alias-a-nested-function-reads",
        ),
        pytest.param(
            """
            def read(path, open=open):
                with open(path) as handle:
                    return handle.read()
            """,
            _OWN,
            id="a-default-of-the-builtin",
        ),
        pytest.param(
            """
            def read(path, *, open=open):
                with open(path) as handle:
                    return handle.read()
            """,
            _OWN,
            id="a-keyword-only-default-of-the-builtin",
        ),
        pytest.param(
            """
            import io

            def read(path, open=io.open):
                with open(path) as handle:
                    return handle.read()
            """,
            _OWN,
            id="a-default-of-another-spelling",
        ),
        pytest.param(
            """
            def read(path, reader=open):
                return reader(path).read()
            """,
            _OWN,
            id="a-default-under-another-name",
        ),
        pytest.param(
            """
            import soundfile

            def read(path, loader=soundfile.read):
                return loader(path)
            """,
            _FOREIGN,
            id="a-default-of-a-foreign-reader",
        ),
        pytest.param(
            """
            import io

            class Reader:
                open = io.open

                def read(self, path, open=open):
                    return open(path).read()
            """,
            _OWN,
            id="a-default-read-in-the-class-body",
        ),
        pytest.param(
            """
            def read(path):
                return (lambda open=open: open(path))().read()
            """,
            _OWN,
            id="a-lambda-default-of-the-builtin",
        ),
        pytest.param(
            """
            try:
                from gzip import open
            except ImportError:
                open = None

            def read(path):
                return open(path).read()
            """,
            _FOREIGN,
            id="an-import-in-a-try-branch",
        ),
        pytest.param(
            """
            def read(path, soundfile):
                return (lambda sf: sf.read(path))(soundfile)
            """,
            _FOREIGN,
            id="a-lambda-parameter-spelt-as-the-module",
        ),
    ],
)
def test_a_binding_that_holds_a_reader_is_still_read_as_it(
    tmp_path: pathlib.Path, source: str, shape: str
) -> None:
    """A binding hides what the spelling names only when it holds nothing the
    guard knows: an alias, an import in a branch and a parameter's default say
    what the name holds, and a lambda's parameter spelt ``sf`` is the module
    handed in, as a function's is. Each passed a whole read for a name bound
    to something unknown.
    """
    assert [found for _function, found in _found(tmp_path, source)] == [shape]


@pytest.mark.parametrize(
    "source",
    [
        """
        def read(path, open=None):
            return open(path)
        """,
        """
        def read(path, opener=print):
            return opener(path)
        """,
        """
        import math

        def read(path, np=math):
            return np.load(path)
        """,
        """
        from pathlib import Path

        def read(path, open=Path):
            return open(path)
        """,
        """
        from pathlib import Path as open

        def read(path, open=open):
            return open(path)
        """,
        """
        import soundfile

        def read(path):
            return (lambda sf=None: sf)(soundfile)
        """,
        """
        import math

        def read(path):
            return (lambda sf=math: sf.read(path))()
        """,
        """
        def read(path):
            return (lambda: [sf := make_reader(), sf.read(path)])()
        """,
    ],
)
def test_a_default_that_names_no_reader_reads_nothing(
    tmp_path: pathlib.Path, source: str
) -> None:
    """A default of ``None`` leaves a parameter unknown, and a default that
    names something else says it is that: neither is a read of a file.
    """
    assert _found(tmp_path, source) == []


def test_a_function_of_the_module_named_open_is_read_as_that_function(
    tmp_path: pathlib.Path,
) -> None:
    """A ``def open`` of the module is no builtin, and it is the function a call
    reaches: when it checks its name, it answers for the read after it. A
    lambda's parameter of a check's spelling answers for nothing.
    """
    assert (
        _found(
            tmp_path,
            """
            import numpy as np

            from phonometry._internal.json_input import not_regular_at

            def open(path):
                if not_regular_at(Path(path)) is not None:
                    raise ValueError(path)

            def checked(path):
                open(path)
                return np.fromfile(path)
            """,
        )
        == []
    )
    assert _found(
        tmp_path,
        """
        import numpy as np

        from check import require_regular

        def by_a_lambda(path):
            (lambda require_regular: require_regular(path))(print)
            return np.fromfile(path)
        """,
    ) == [("by_a_lambda", _FOREIGN)]


def test_a_name_a_comprehension_binds_leaves_the_rest_of_the_function_alone(
    tmp_path: pathlib.Path,
) -> None:
    """A comprehension's variable is its own: the function's ``open`` beside it
    is still the builtin, a method called on an item still reads a file, a
    check of that spelling is no check, and a module handed in as ``sf`` is
    still read by its spelling.
    """
    assert _found(
        tmp_path,
        """
        from check import require_regular

        def beside(path, openers):
            names = [open for open in openers]
            with open(path) as handle:
                return handle.read(), names

        def items(files):
            return [f.read_text() for f in files]

        def handed_in(path, sf):
            return sf.read(path)

        def checked_by_nothing(path):
            _ = [require_regular(path) for require_regular in [print]]
            return np.fromfile(path)

        def checked(path):
            require_regular(path)
            return np.fromfile(path)
        """,
        helpers=_CHECK,
    ) == [
        ("beside", _OWN),
        ("items", _OWN),
        ("handed_in", _FOREIGN),
        ("checked_by_nothing", _FOREIGN),
    ]


def test_a_read_in_a_function_s_if_type_checking_block_is_no_read(
    tmp_path: pathlib.Path,
) -> None:
    """The body of an ``if TYPE_CHECKING:`` in a function never runs, so nothing
    it opens is opened; its ``else`` runs.
    """
    assert _found(
        tmp_path,
        """
        def in_the_block(path):
            if TYPE_CHECKING:
                return open(path).read()

        def in_the_else(path):
            if TYPE_CHECKING:
                pass
            else:
                return open(path).read()
        """,
    ) == [("in_the_else", _OWN)]


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


@pytest.mark.parametrize(
    ("annotation", "lazy", "call"),
    [
        ("import soundfile as snd", "import soundfile as snd", "snd.read(path)"),
        ("import numpy as snd", "import soundfile as snd", "snd.read(path)"),
        (
            "from soundfile import read as reader",
            "from soundfile import read as reader",
            "reader(path)",
        ),
        (
            "import numpy as numpy_module",
            "import numpy as numpy_module",
            "numpy_module.fromfile(path)",
        ),
    ],
    ids=["same-module", "another-module", "from-import", "numpy"],
)
def test_an_import_for_the_type_checker_leaves_a_lazy_global_import_its_name(
    tmp_path: pathlib.Path, annotation: str, lazy: str, call: str
) -> None:
    """An annotation's import beside a function that imports the name under
    ``global`` is the ordinary lazy import. The block never runs, so the
    function's import is all the name can hold, and the read through it is
    refused as it is with no block there. The block's import counted as the
    module binding the name, which took the alias away and passed the read.
    """
    source = f"""
        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            {annotation}

        def _load():
            global {lazy.rpartition(" as ")[2]}
            {lazy}

        def f(path):
            return {call}
        """
    assert _found(tmp_path, source) == [("f", _FOREIGN)]


def test_an_import_for_the_type_checker_is_no_second_reading_of_a_running_one(
    tmp_path: pathlib.Path,
) -> None:
    """What runs at the top of the module still disagrees with a function's
    import under ``global``: the name may hold either, and neither is read.
    """
    source = """
        from typing import TYPE_CHECKING

        import numpy as snd

        if TYPE_CHECKING:
            import soundfile as snd

        def _load():
            global snd
            import soundfile as snd

        def f(path):
            return snd.read(path)
        """
    assert _found(tmp_path, source) == []


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
