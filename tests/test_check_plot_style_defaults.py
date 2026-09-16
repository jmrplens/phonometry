#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate against a style default that collides with its own alias.

``scripts/check_plot_style_defaults.py`` refuses ``kwargs.setdefault`` for the
seven artist properties matplotlib gives two names. The defect it was written
for is real and was everywhere: 195 calls across 24 renderer modules defaulted
a colour, a line width or a marker size under one spelling, so a caller who
wrote the other got ``TypeError: Got both 'color' and 'c', which are aliases of
one another`` instead of a figure.
"""

from __future__ import annotations

import pathlib
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_plot_style_defaults as gate


def _module(source: str, tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "module.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_the_long_spelling_is_refused(tmp_path: pathlib.Path) -> None:
    source = 'def f(**kwargs):\n    kwargs.setdefault("color", "red")\n'
    assert gate._findings(_module(source, tmp_path)) == [
        (2, "setdefault of the aliased property 'color'")
    ]


def test_the_short_spelling_is_refused_too(tmp_path: pathlib.Path) -> None:
    """A renderer defaulting ``c`` breaks the caller who wrote ``color``."""
    source = 'def f(**kwargs):\n    kwargs.setdefault("c", "red")\n'
    assert gate._findings(_module(source, tmp_path)) == [
        (2, "setdefault of the aliased property 'c'")
    ]


def test_a_property_with_no_alias_is_left_alone(tmp_path: pathlib.Path) -> None:
    """``label`` and ``marker`` have one name each, so they cost nothing."""
    source = (
        "def f(**kwargs):\n"
        '    kwargs.setdefault("label", "x")\n'
        '    kwargs.setdefault("marker", "o")\n'
        '    kwargs.setdefault("zorder", 3)\n'
    )
    assert gate._findings(_module(source, tmp_path)) == []


def test_a_read_back_of_the_long_spelling_is_refused(tmp_path: pathlib.Path) -> None:
    """The second artist reads ``kwargs["color"]`` and the caller wrote ``c``."""
    source = 'def f(**kwargs):\n    return kwargs["color"]\n'
    assert gate._findings(_module(source, tmp_path)) == [
        (2, "read-back of the aliased property 'color'")
    ]


def test_a_pop_of_one_spelling_is_refused(tmp_path: pathlib.Path) -> None:
    """``pop`` takes one name and leaves the other in the mapping."""
    source = 'def f(**kwargs):\n    return kwargs.pop("color", "blue")\n'
    assert gate._findings(_module(source, tmp_path)) == [
        (2, "pop of the aliased property 'color'")
    ]


def test_a_literal_default_beside_the_spread_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """``{"color": ..., **kwargs}`` is the same default in another shape."""
    source = 'def f(**kwargs):\n    return {"color": "blue", "label": "x", **kwargs}\n'
    assert gate._findings(_module(source, tmp_path)) == [
        (2, "literal default of the aliased property 'color'")
    ]


def test_a_local_mapping_is_left_alone(tmp_path: pathlib.Path) -> None:
    """A dictionary the caller never sees may hold whichever spelling it likes."""
    source = (
        "def f(**kwargs):\n"
        "    detached = dict(kwargs)\n"
        '    detached["ls"] = "none"\n'
        '    return detached["ls"], {"color": "blue", **detached}\n'
    )
    assert gate._findings(_module(source, tmp_path)) == []


def test_the_helper_is_not_flagged(tmp_path: pathlib.Path) -> None:
    """The fix has to pass the gate that asks for it."""
    source = (
        "def f(**kwargs):\n"
        '    style_default(kwargs, "color", "red")\n'
        '    return style_get(kwargs, "color", "red"), styled(kwargs, lw=2)\n'
    )
    assert gate._findings(_module(source, tmp_path)) == []


def test_every_aliased_property_is_covered(tmp_path: pathlib.Path) -> None:
    """All seven pairs, so a later spelling cannot slip through unlisted."""
    names = sorted(gate._ALIASED)
    body = "".join(f'    kwargs.setdefault("{n}", 1)\n' for n in names)
    found = gate._findings(_module(f"def f(**kwargs):\n{body}", tmp_path))
    assert [why.rsplit(" ", 1)[1].strip("'") for _, why in found] == names
    assert len(names) == 14


def test_the_two_alias_tables_are_the_same() -> None:
    """The gate refuses exactly what the helper knows how to default."""
    assert gate._aliases_agree() is None


def test_the_helper_table_is_read_and_not_imported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The gate runs in a step that installs nothing, so it may not import.

    Importing ``phonometry._plot.common`` pulls numpy in behind it, which the
    static step has no reason to hold. Blocking the package here is what tells
    a reading of the source from an import of it.
    """
    monkeypatch.setitem(sys.modules, "phonometry", None)
    assert gate._helper_aliases() == set(gate._ALIASED)
    assert gate._aliases_agree() is None


def test_a_table_that_is_not_a_literal_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A gate that cannot read the helper's table says so instead of passing."""
    root = tmp_path / "phonometry"
    (root / "_plot").mkdir(parents=True)
    (root / "_plot" / "common.py").write_text(
        '_SHORT = "c"\n_STYLE_ALIASES: dict[str, str] = {"color": _SHORT}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(gate, "_ROOT", root)
    assert gate._helper_aliases() is None
    drift = gate._aliases_agree()
    assert drift is not None
    assert "could not be read" in drift


def test_the_package_is_clean() -> None:
    """The corpus itself, which is what the gate protects."""
    assert gate.main() == 0
