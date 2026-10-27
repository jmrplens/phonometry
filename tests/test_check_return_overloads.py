#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate on returns whose type one argument decides, written as one type.

``scripts/check_return_overloads.py`` reads every function of the package and
asks that a return naming one axes and several (a tuple, a list or an array
of them) stand on an implementation with overload heads, never on a head, and
that a function reaching a polar axes say ``PolarAxes``, or have a head that
does. Its own run only says the tree is clean today; these tests fix what it
must catch, on small packages written for the purpose (a multiline signature,
an alias, a renamed import, a polar axes two calls away), and what it must
let through.
"""

from __future__ import annotations

import pathlib
import sys
import textwrap

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import ast_scan
import check_return_overloads as cro

_IMPORTS = """
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional, Union, overload

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.projections.polar import PolarAxes
    from numpy.typing import NDArray
"""


def _package(tmp_path: pathlib.Path, **modules: str) -> pathlib.Path:
    """Write ``pkg`` with *modules*, each opened by the shared imports."""
    root = tmp_path / "pkg"
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    for name, source in modules.items():
        path = root / f"{name.replace('.', '/')}.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.parent != root and not (path.parent / "__init__.py").exists():
            (path.parent / "__init__.py").write_text("", encoding="utf-8")
        path.write_text(_IMPORTS + textwrap.dedent(source), encoding="utf-8")
    return root


def _refused(tmp_path: pathlib.Path, **modules: str) -> dict[str, str]:
    """The functions refused, by qualified name, with the reason."""
    root = _package(tmp_path, **modules)
    found = cro.findings_in(sorted(root.rglob("*.py")), root)
    return {finding.function: finding.sink for finding in found}


def test_a_column_of_axes_without_overloads_is_refused(tmp_path: pathlib.Path) -> None:
    refused = _refused(
        tmp_path,
        plots="""
        def plot_pair(
            result: object,
            ax: Axes | None = None,
            *,
            language: str = "en",
        ) -> (
            Axes
            | tuple[Axes, Axes]
        ):
            raise NotImplementedError
        """,
    )
    assert refused == {
        "plot_pair": "returns Axes | tuple[Axes, Axes], and no overload says "
        "which argument decides"
    }


@pytest.mark.parametrize(
    "returns",
    [
        "Axes | np.ndarray",
        "Axes | NDArray[Any]",
        "Union[Axes, np.ndarray]",
        "np.ndarray | Axes",
        "Axes | list[Axes]",
        "Axes | tuple[Axes, ...]",
        "'Axes | tuple[Axes, Axes, Axes]'",
    ],
)
def test_every_spelling_of_several_axes_is_read(
    tmp_path: pathlib.Path, returns: str
) -> None:
    refused = _refused(
        tmp_path,
        plots=f"""
        def plot_pair(result: object, ax: Axes | None = None) -> {returns}:
            raise NotImplementedError
        """,
    )
    assert list(refused) == ["plot_pair"]


@pytest.mark.parametrize(
    "returns",
    ["Axes", "Axes | None", "Optional[Axes]", "tuple[Axes, Axes]", "np.ndarray"],
)
def test_a_return_no_argument_decides_is_let_through(
    tmp_path: pathlib.Path, returns: str
) -> None:
    assert not _refused(
        tmp_path,
        plots=f"""
        def plot_one(result: object, ax: Axes | None = None) -> {returns}:
            raise NotImplementedError
        """,
    )


def test_an_alias_of_the_column_is_read_through(tmp_path: pathlib.Path) -> None:
    """An alias in another module, and an alias of that alias, are what they name."""
    refused = _refused(
        tmp_path,
        types="""
        from typing import TypeAlias

        Pair: TypeAlias = tuple["Axes", "Axes"]
        type Drawn = Axes | Pair
        """,
        plots="""
        from .types import Drawn, Pair

        def plot_pair(result: object, ax: Axes | None = None) -> Axes | Pair:
            raise NotImplementedError

        def plot_drawn(result: object, ax: Axes | None = None) -> Drawn:
            raise NotImplementedError
        """,
    )
    assert sorted(refused) == ["plot_drawn", "plot_pair"]


def test_an_axes_class_is_read_under_any_name(tmp_path: pathlib.Path) -> None:
    refused = _refused(
        tmp_path,
        plots="""
        import matplotlib.axes
        from matplotlib.axes import Axes as MplAxes

        def plot_renamed(ax: MplAxes | None = None) -> MplAxes | tuple[MplAxes, ...]:
            raise NotImplementedError

        def plot_dotted(
            ax: matplotlib.axes.Axes | None = None,
        ) -> matplotlib.axes.Axes | np.ndarray:
            raise NotImplementedError
        """,
    )
    assert sorted(refused) == ["plot_dotted", "plot_renamed"]


_OVERLOADED = """
class Result:
    @overload
    def plot(self, ax: None = None, *, language: str = "en") -> tuple[Axes, Axes]: ...

    @overload
    def plot(self, ax: Axes, *, language: str = "en") -> Axes: ...

    def plot(
        self, ax: Axes | None = None, *, language: str = "en"
    ) -> Axes | tuple[Axes, Axes]:
        raise NotImplementedError
"""


def test_overloads_let_the_union_through(tmp_path: pathlib.Path) -> None:
    assert not _refused(tmp_path, results=_OVERLOADED)


def test_the_union_on_a_head_is_refused_under_the_heads_key(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        results=_OVERLOADED.replace(
            'def plot(self, ax: None = None, *, language: str = "en") '
            "-> tuple[Axes, Axes]: ...",
            'def plot(self, ax: None = None, *, language: str = "en") '
            "-> Axes | tuple[Axes, Axes]: ...",
        ),
    )
    assert refused == {
        "Result.plot" + cro.OVERLOAD_KEY: "an overload head returns "
        "Axes | tuple[Axes, Axes]"
    }


@pytest.mark.parametrize(
    "making",
    [
        'plt.subplots(subplot_kw={"projection": "polar"})[1]',
        'plt.figure().add_subplot(1, 1, 1, projection="polar")',
        "plt.subplot(polar=True)",
    ],
)
def test_a_polar_axes_typed_plain_axes_is_refused(
    tmp_path: pathlib.Path, making: str
) -> None:
    refused = _refused(
        tmp_path,
        plots=f"""
        import matplotlib.pyplot as plt

        def plot_polar(result: object, ax: Axes | None = None) -> Axes:
            return ax if ax is not None else {making}
        """,
    )
    assert refused == {"plot_polar": "reaches a polar axes and returns Axes"}


def test_a_polar_axes_reached_through_other_functions_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """Through an import, a module, ``self`` and a helper typed ``Axes``, at any depth."""
    refused = _refused(
        tmp_path,
        helpers="""
        import matplotlib.pyplot as plt

        def new_polar() -> PolarAxes:
            return plt.subplots(subplot_kw={"projection": "polar"})[1]

        def draw_one(polar: bool) -> Axes:
            return new_polar() if polar else plt.subplots()[1]
        """,
        plots="""
        from . import helpers
        from .helpers import draw_one

        def plot_imported(result: object) -> Axes:
            return draw_one(True)

        def plot_through_module(result: object) -> Axes:
            return helpers.new_polar()

        def plot_two_calls_away(result: object) -> Axes:
            return plot_imported(result)

        class Result:
            def _draw(self) -> Axes:
                return draw_one(True)

            def plot(self, ax: Axes | None = None) -> Axes:
                from .helpers import draw_one as late

                return self._draw() if ax is None else late(False)
        """,
    )
    assert sorted(refused) == [
        "Result._draw",
        "Result.plot",
        "draw_one",
        "plot_imported",
        "plot_through_module",
        "plot_two_calls_away",
    ]


def test_a_polar_axes_typed_polar_or_overloaded_on_it_is_let_through(
    tmp_path: pathlib.Path,
) -> None:
    assert not _refused(
        tmp_path,
        plots="""
        import matplotlib.pyplot as plt

        def plot_polar(result: object, ax: PolarAxes | None = None) -> PolarAxes:
            return ax if ax is not None else plt.subplot(polar=True)

        @overload
        def plot_view(
            result: object, *, view: Literal["response"] = "response"
        ) -> PolarAxes: ...

        @overload
        def plot_view(result: object, *, view: Literal["weights"]) -> Axes: ...

        def plot_view(
            result: object, *, view: Literal["response", "weights"] = "response"
        ) -> Axes:
            return plot_polar(result) if view == "response" else plt.subplot()
        """,
    )


def test_overloads_none_of_which_returns_polar_are_refused(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        plots="""
        import matplotlib.pyplot as plt

        @overload
        def plot_view(result: object, *, view: Literal["response"] = "response") -> Axes: ...

        @overload
        def plot_view(result: object, *, view: Literal["weights"]) -> Axes: ...

        def plot_view(
            result: object, *, view: Literal["response", "weights"] = "response"
        ) -> Axes:
            return plt.subplot(polar=view == "response")
        """,
    )
    assert refused == {
        "plot_view": "reaches a polar axes, and none of its overloads returns PolarAxes"
    }


def test_an_exemption_covers_only_what_it_names(tmp_path: pathlib.Path) -> None:
    root = _package(
        tmp_path,
        plots="""
        def plot_pair(result: object, ax: Axes | None = None) -> Axes | np.ndarray:
            raise NotImplementedError
        """,
    )
    path = ast_scan.relative(root / "plots.py")
    found = cro.findings_in(sorted(root.rglob("*.py")), root)
    kept, stale = ast_scan.exempted(
        found,
        {(path, "plot_pair"): "a reason", (path, "plot_gone"): "an old reason"},
    )
    assert not kept
    assert stale == [(path, "plot_gone")]


def test_the_package_keeps_the_rule() -> None:
    """The tree today, with its exemptions, and none of them stale."""
    found, stale = ast_scan.exempted(
        cro.findings_in(ast_scan.python_files([], cro.SOURCE), cro.SOURCE),
        cro.EXEMPT,
    )
    assert not found, "\n".join(
        f"{f.path}:{f.line}: {f.function}: {f.sink}" for f in found
    )
    assert not stale


def test_the_script_reports_and_fails(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _package(
        tmp_path,
        plots="""
        def plot_pair(result: object, ax: Axes | None = None) -> Axes | np.ndarray:
            raise NotImplementedError
        """,
    )
    assert cro.main([str(root)]) == 1
    out = capsys.readouterr().out
    assert "::error::a return that one argument decides is written as one type" in out
    assert "plots.py:" in out
    assert "plot_pair: returns Axes | np.ndarray" in out
    assert cro.main([]) == 0
