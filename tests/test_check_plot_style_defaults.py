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


def test_a_keyword_written_beside_the_spread_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """``ax.bar(x, h, zorder=3, **kwargs)`` cannot take the caller's ``zorder``.

    The caller who passes it gets ``TypeError: got multiple values for keyword
    argument 'zorder'`` and no figure, whatever the property, aliased or not.
    """
    source = (
        "def f(ax, **kwargs):\n"
        "    ax.bar([1], [2], zorder=3, width=0.5, **kwargs)\n"
        "    Rectangle((0, 0), 1, 1, hatch='//', **kwargs)\n"
    )
    assert gate._findings(_module(source, tmp_path)) == [
        (2, "'width' written beside **kwargs in ax.bar(), so a caller cannot pass it"),
        (2, "'zorder' written beside **kwargs in ax.bar(), so a caller cannot pass it"),
        (
            3,
            "'hatch' written beside **kwargs in Rectangle(), so a caller cannot "
            "pass it",
        ),
    ]


def test_a_keyword_that_cannot_reach_the_spread_is_left_alone(
    tmp_path: pathlib.Path,
) -> None:
    """Only a name the caller can put in ``**kwargs`` can collide.

    A parameter of the function itself is bound before ``**kwargs`` is
    filled, a helper of the package takes its own parameters beside the
    caller's properties, the merge through ``styled`` lets the caller win, a
    key the function takes out of the caller's keywords (or of a copy) or
    refuses by name is not there to collide, and a mapping the renderer
    builds without them is its own.
    """
    source = (
        "from .common import draw_rating\n"
        "def _helper(ax, *, title, **kwargs):\n"
        "    return ax\n"
        "def f(ax=None, language='en', **kwargs):\n"
        "    _helper(ax, title='t', **kwargs)\n"
        "    draw_rating(ax, title='t', **kwargs)\n"
        "    ax.plot([1], language=language, **kwargs)\n"
        "    ax.plot([1], **styled(kwargs, zorder=3))\n"
        "    width = kwargs.pop('width', 0.7)\n"
        "    style_pop(kwargs, 'c', None)\n"
        "    refuse_fixed_keywords(kwargs, 'f', 'bottom', reason='r')\n"
        "    options = dict(kwargs)\n"
        "    del options['hatch']\n"
        "    ax.bar([1], [2], width=width, color='r', bottom=0, hatch='/', **options)\n"
        "    own = {'lw': 2}\n"
        "    ax.plot([1], zorder=3, **own)\n"
    )
    assert gate._findings(_module(source, tmp_path)) == []


def test_a_keyword_beside_a_copy_of_the_callers_keywords_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """``options = dict(kwargs)`` carries the caller's keywords as ``kwargs`` does."""
    source = (
        "def f(ax, **kwargs):\n"
        "    options = dict(kwargs)\n"
        "    options.setdefault('label', 'x')\n"
        "    ax.plot([1], zorder=3, **options)\n"
        "    typed: dict[str, object] = dict(kwargs)\n"
        "    ax.plot([1], zorder=3, **typed)\n"
        "    if (walrus := dict(kwargs)):\n"
        "        ax.plot([1], zorder=3, **walrus)\n"
    )
    assert gate._findings(_module(source, tmp_path)) == [
        (
            4,
            "'zorder' written beside **kwargs in ax.plot(), so a caller cannot pass it",
        ),
        (
            6,
            "'zorder' written beside **kwargs in ax.plot(), so a caller cannot pass it",
        ),
        (
            8,
            "'zorder' written beside **kwargs in ax.plot(), so a caller cannot pass it",
        ),
    ]


def test_a_keyword_beside_a_mapping_built_from_the_spread_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """``**{"label": ..., **kwargs}`` and ``**styled(kwargs, ...)`` carry the caller's too."""
    source = (
        "def f(ax, **kwargs):\n"
        "    ax.plot([1], zorder=2, **{'label': 'x', **kwargs})\n"
        "    ax.bar([1], [2], width=0.6, **styled(kwargs, color='r'))\n"
        "    ax.bar([1], [2], **styled(kwargs, width=0.6, color='r'))\n"
    )
    assert gate._findings(_module(source, tmp_path)) == [
        (
            2,
            "'zorder' written beside **kwargs in ax.plot(), so a caller cannot pass it",
        ),
        (3, "'width' written beside **kwargs in ax.bar(), so a caller cannot pass it"),
    ]


def test_a_key_taken_out_counts_only_before_the_call_and_on_its_mapping(
    tmp_path: pathlib.Path,
) -> None:
    """A pop after the call, or from another copy, leaves the collision in place.

    A copy made after the pop inherits it; one made before does not.
    """
    source = (
        "def f(ax, **kwargs):\n"
        "    ax.plot([1], zorder=3, **kwargs)\n"
        "    kwargs.pop('zorder', None)\n"
        "def g(ax, **kwargs):\n"
        "    options = dict(kwargs)\n"
        "    options.pop('zorder', None)\n"
        "    ax.plot([1], zorder=3, **kwargs)\n"
        "def h(ax, **kwargs):\n"
        "    early = dict(kwargs)\n"
        "    kwargs.pop('zorder', None)\n"
        "    late = dict(kwargs)\n"
        "    ax.plot([1], zorder=3, **late)\n"
        "    ax.plot([1], zorder=3, **early)\n"
    )
    assert gate._findings(_module(source, tmp_path)) == [
        (
            2,
            "'zorder' written beside **kwargs in ax.plot(), so a caller cannot pass it",
        ),
        (
            7,
            "'zorder' written beside **kwargs in ax.plot(), so a caller cannot pass it",
        ),
        (
            13,
            "'zorder' written beside **kwargs in ax.plot(), so a caller cannot pass it",
        ),
    ]
