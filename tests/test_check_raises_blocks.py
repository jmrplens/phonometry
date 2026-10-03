#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate on exception and warning tests that more than one call could satisfy.

``scripts/check_raises_blocks.py`` refuses a ``pytest.raises``,
``pytest.warns`` or ``pytest.deprecated_call`` block holding more than one
call that could raise, or more than one statement, which is what SonarCloud
reports as python:S5778 and S9088. The two defects it was written against are
here verbatim in shape: the catalogue writer built its catalogue inside the
block of the write it checked, and six warning tests built their case inside
the block of the model they checked. So are the calls Sonar does not count,
because a gate that refuses ``float("nan")`` as an argument would be switched
off within a week.
"""

from __future__ import annotations

import pathlib
import sys
import textwrap

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_raises_blocks as crb


def _findings(tmp_path: pathlib.Path, source: str) -> list[crb.Finding]:
    """The findings of one test module written from ``source``."""
    path = tmp_path / "test_case.py"
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return crb.findings(path)


def test_the_catalogue_writer_defect_is_refused(tmp_path: pathlib.Path) -> None:
    """The input built inside the block of the call under test (#887)."""
    found = _findings(
        tmp_path,
        """
        import pytest
        from phonometry import io

        def test_kept(path):
            with pytest.raises(FileExistsError, match="kept"):
                io.write_catalogue(_mine(), path)
        """,
    )
    assert [(f.test, f.calls) for f in found] == [
        ("test_kept", ("phonometry.io.write_catalogue", "_mine"))
    ]


def test_the_fix_the_writer_tests_took_passes(tmp_path: pathlib.Path) -> None:
    """The same test with the catalogue built first."""
    found = _findings(
        tmp_path,
        """
        import pytest
        from phonometry import io

        def test_kept(path):
            mine = _mine()
            with pytest.raises(FileExistsError, match="kept"):
                io.write_catalogue(mine, path)
        """,
    )
    assert found == []


def test_a_warning_test_is_held_to_the_same_rule(tmp_path: pathlib.Path) -> None:
    """The case built inside a ``pytest.warns`` block (#809)."""
    found = _findings(
        tmp_path,
        """
        import pytest
        from phonometry import metrology

        def test_unstable_tone_warns():
            with pytest.warns(metrology.CalibrationWarning, match="unstable"):
                metrology.sensitivity(_cal_tone(), fs=48_000)
        """,
    )
    assert [(f.waiter, f.calls) for f in found] == [
        ("pytest.warns", ("phonometry.metrology.sensitivity", "_cal_tone"))
    ]


def test_a_deprecation_test_is_held_to_the_same_rule(tmp_path: pathlib.Path) -> None:
    """``pytest.deprecated_call`` waits for one call to warn, as ``warns`` does."""
    found = _findings(
        tmp_path,
        """
        import pytest

        def test_old_name_warns():
            with pytest.deprecated_call():
                old_name(build())
        """,
    )
    assert [(f.waiter, f.calls) for f in found] == [
        ("pytest.deprecated_call", ("old_name", "build"))
    ]


def test_a_chained_call_is_two_calls(tmp_path: pathlib.Path) -> None:
    """Sonar's own example: either half of the chain could raise."""
    found = _findings(
        tmp_path,
        """
        import pytest

        def test_normalize():
            with pytest.raises(ValueError, match="amount"):
                parse_payment(payload).normalize()
        """,
    )
    assert [f.calls for f in found] == [("(...).normalize", "parse_payment")]


def test_several_statements_are_refused_even_with_one_call(
    tmp_path: pathlib.Path,
) -> None:
    """Which statement raised is the same question, and Ruff's noqa does not hide it."""
    found = _findings(
        tmp_path,
        """
        import pytest

        def test_frozen():
            with pytest.raises(AttributeError, match="value"):  # noqa: PT012
                result = make()
                result.value = 3
        """,
    )
    assert [(f.statements, f.calls) for f in found] == [(2, ("make",))]


def test_the_calls_sonar_holds_safe_do_not_count(tmp_path: pathlib.Path) -> None:
    """Conversions, containers, paths and NumPy around the one call under test."""
    found = _findings(
        tmp_path,
        """
        import pathlib
        import numpy as np
        import pytest
        from phonometry import speech

        def test_safe():
            with pytest.raises(ValueError, match="finite"):
                speech.stipa(
                    np.sin(2 * np.pi * np.arange(4)),
                    int(float("nan")),
                    list(range(len([1, 2]))),
                    pathlib.Path("x"),
                    set(),
                )
        """,
    )
    assert found == []


def test_a_set_built_from_something_counts(tmp_path: pathlib.Path) -> None:
    """``set()`` cannot raise; ``set(values)`` iterates and can."""
    found = _findings(
        tmp_path,
        """
        import pytest

        def test_bands():
            with pytest.raises(ValueError, match="bands"):
                check(set(values))
        """,
    )
    assert [f.calls for f in found] == [("check", "set")]


def test_a_builtin_name_the_file_rebinds_is_not_the_builtin(
    tmp_path: pathlib.Path,
) -> None:
    """A module's own ``format`` is a call under test like any other."""
    found = _findings(
        tmp_path,
        """
        import pytest

        def format(value):
            return value

        def test_rebound():
            with pytest.raises(ValueError, match="x"):
                check(format(1))
        """,
    )
    assert [f.calls for f in found] == [("check", "format")]


def test_a_deferred_call_does_not_count(tmp_path: pathlib.Path) -> None:
    """A lambda or a nested function inside the block is defined, not called."""
    found = _findings(
        tmp_path,
        """
        import pytest

        def test_deferred():
            with pytest.raises(ValueError, match="key"):
                apply(key=lambda row: row.name.lower())
        """,
    )
    assert found == []


def test_a_class_defined_in_the_block_runs_its_bases_and_body(
    tmp_path: pathlib.Path,
) -> None:
    """Unlike a function, a class statement runs its bases and its body at once."""
    found = _findings(
        tmp_path,
        """
        import pytest

        def test_sealed():
            with pytest.raises(TypeError, match="sealed"):
                class Bad(make_base()):
                    value = compute()
        """,
    )
    assert [f.calls for f in found] == [("make_base", "compute")]


def test_the_lambda_form_is_the_block(tmp_path: pathlib.Path) -> None:
    """``pytest.raises(Error, lambda: ...)`` runs the lambda inside the check."""
    found = _findings(
        tmp_path,
        """
        import pytest

        def test_lambda():
            pytest.raises(ValueError, lambda: check(build()))
        """,
    )
    assert [f.calls for f in found] == [("check", "build")]


def test_an_imported_alias_of_raises_is_recognised(tmp_path: pathlib.Path) -> None:
    """The gate reads what the name resolves to, not how it is spelt."""
    found = _findings(
        tmp_path,
        """
        from pytest import raises as expect

        def test_alias():
            with expect(KeyError, match="x"):
                lookup(key())
        """,
    )
    assert [f.waiter for f in found] == ["pytest.raises"]


def test_two_waiters_in_one_with_wait_on_their_body(tmp_path: pathlib.Path) -> None:
    """A warning and an error from the same call is still one call."""
    found = _findings(
        tmp_path,
        """
        import pytest

        def test_both():
            with (
                pytest.warns(UserWarning, match="range"),
                pytest.raises(ValueError, match="finite"),
            ):
                nipts(l_ex=85.0, years=float("nan"))
        """,
    )
    assert found == []


def test_an_exemption_silences_one_test_and_goes_stale(
    tmp_path: pathlib.Path,
) -> None:
    """The hatch, keyed by file and test, reports itself once it covers nothing."""
    path = tmp_path / "test_case.py"
    path.write_text(
        "import pytest\n"
        "def test_kept():\n"
        "    with pytest.raises(ValueError, match='x'):\n"
        "        check(build())\n",
        encoding="utf-8",
    )
    key = (crb.relative(path), "test_kept")
    found, stale, read = crb.check([path], {key: "why it stays"})
    assert (found, stale, read) == ([], [], 1)
    path.write_text(
        "import pytest\n"
        "def test_kept():\n"
        "    built = build()\n"
        "    with pytest.raises(ValueError, match='x'):\n"
        "        check(built)\n",
        encoding="utf-8",
    )
    found, stale, _ = crb.check([path], {key: "why it stays"})
    assert (found, stale) == ([], [key])


def test_the_suite_holds_no_such_block() -> None:
    """The tree itself: every exception and warning test waits on one call."""
    assert crb.main([]) == 0
