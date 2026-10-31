#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate on returns whose type one argument decides, written as one type.

``scripts/check_return_overloads.py`` reads every function of the package and
asks that a return naming one axes and several (a tuple, a list or an array
of them) stand on an implementation with overload heads, never on a head, and
that a function reaching a polar axes say ``PolarAxes``, or have a head that
does. Its own run only says the tree is clean today; these tests fix what it
must catch, on small packages written for the purpose (a multiline signature,
an alias, a renamed import, a polar axes two calls away), and what it must
let through. Each route by which it follows a name (an import inside a
function, ``self`` and ``cls``, a package that re-exports) has a case of its
own, so that a route that breaks fails here even when another one would have
found the same function.
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


def test_an_axes_subclass_is_read_and_an_axes_image_is_not(
    tmp_path: pathlib.Path,
) -> None:
    """``Axes3D`` and ``HostAxes`` are axes; ``AxesImage`` and ``AxesWidget`` are not."""
    refused = _refused(
        tmp_path,
        plots="""
        from matplotlib.image import AxesImage
        from matplotlib.widgets import AxesWidget
        from mpl_toolkits.axes_grid1.parasite_axes import HostAxes
        from mpl_toolkits.mplot3d import Axes3D

        def plot_solid(ax: Axes3D | None = None) -> Axes3D | tuple[Axes3D, Axes3D]:
            raise NotImplementedError

        def plot_host(ax: HostAxes | None = None) -> HostAxes | list[HostAxes]:
            raise NotImplementedError

        def show_images(ax: Axes | None = None) -> AxesImage | tuple[AxesImage, AxesImage]:
            raise NotImplementedError

        def make_widgets(ax: Axes | None = None) -> AxesWidget | list[AxesWidget]:
            raise NotImplementedError
        """,
    )
    assert sorted(refused) == ["plot_host", "plot_solid"]


def test_a_bare_name_alias_of_an_axes_class_is_read(tmp_path: pathlib.Path) -> None:
    """``Panel = Axes`` is an alias; ``panel = some_function`` is not."""
    refused = _refused(
        tmp_path,
        types="""
        from matplotlib.axes import Axes as _MplAxes

        Panel = _MplAxes
        Board = Panel
        """,
        plots="""
        from .types import Board, Panel

        def _helper() -> None:
            pass

        Helper = _helper

        def plot_panel(ax: Panel | None = None) -> Panel | tuple[Panel, Panel]:
            raise NotImplementedError

        def plot_board(ax: Board | None = None) -> Board | list[Board]:
            raise NotImplementedError

        def plot_helper(ax: Axes | None = None) -> Helper | tuple[Helper, Helper]:
            raise NotImplementedError
        """,
    )
    assert sorted(refused) == ["plot_board", "plot_panel"]


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
        "Result.plot (overload ax: None)": "an overload head returns "
        "Axes | tuple[Axes, Axes]"
    }


def test_an_exemption_of_one_head_excuses_neither_the_other_nor_the_implementation(
    tmp_path: pathlib.Path,
) -> None:
    """A head is keyed by the parameters that tell it from its siblings."""
    root = _package(
        tmp_path,
        results=_OVERLOADED.replace(
            'def plot(self, ax: None = None, *, language: str = "en") '
            "-> tuple[Axes, Axes]: ...",
            'def plot(self, ax: None = None, *, language: str = "en") '
            "-> Axes | tuple[Axes, Axes]: ...",
        ).replace(
            'def plot(self, ax: Axes, *, language: str = "en") -> Axes: ...',
            'def plot(self, ax: Axes, *, language: str = "en") '
            "-> Axes | tuple[Axes, Axes]: ...",
        ),
    )
    path = ast_scan.relative(root / "results.py")
    found = cro.findings_in(sorted(root.rglob("*.py")), root)
    kept, stale = ast_scan.exempted(
        found, {(path, "Result.plot (overload ax: None)"): "the data decide"}
    )
    assert [finding.function for finding in kept] == ["Result.plot (overload ax: Axes)"]
    assert not stale


def test_a_head_key_names_every_parameter_that_tells_it_apart() -> None:
    import ast

    tree = ast.parse(
        textwrap.dedent(
            """
            @overload
            def plot(r, *, view: Literal["response"] = "response", ax: PolarAxes | None = None) -> PolarAxes: ...
            @overload
            def plot(r, *, view: Literal["weights"], ax: Axes | None = None) -> Axes: ...
            @overload
            def plot(r, *, view: Literal["weights"], ax: Axes | None = None, extra: int) -> Axes: ...
            """
        )
    )
    heads = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    assert [cro.head_key("plot", head, heads) for head in heads] == [
        "plot (overload view: Literal['response'], ax: PolarAxes | None)",
        "plot (overload view: Literal['weights'], ax: Axes | None)",
        "plot (overload view: Literal['weights'], ax: Axes | None, extra: int)",
    ]
    assert cro.head_key("plot", heads[0], heads[:1]) == "plot (overload)"


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


@pytest.mark.parametrize(
    "making",
    [
        "plt.subplots(subplot_kw=_POLAR)[1]",
        "plt.subplots(subplot_kw=IMPORTED_POLAR)[1]",
        "plt.figure().add_subplot(1, 1, 1, projection=_PROJECTION)",
        "plt.figure().add_subplot(1, 1, 1, projection=IMPORTED_PROJECTION)",
        "plt.subplot(polar=_FLAG)",
        "plt.figure().add_subplot(1, 1, 1, **_KEYWORDS)",
        "plt.subplots(subplot_kw=_SPREAD)[1]",
    ],
)
def test_a_polar_axes_asked_for_through_a_module_constant_is_refused(
    tmp_path: pathlib.Path, making: str
) -> None:
    refused = _refused(
        tmp_path,
        settings="""
        IMPORTED_POLAR = {"projection": "polar"}
        IMPORTED_PROJECTION = "polar"
        """,
        plots=f"""
        import matplotlib.pyplot as plt

        from .settings import IMPORTED_POLAR, IMPORTED_PROJECTION

        _POLAR = dict(projection="polar")
        _PROJECTION = "polar"
        _FLAG = True
        _KEYWORDS = {{"projection": _PROJECTION}}
        _SPREAD = {{**_POLAR, "facecolor": "none"}}

        def plot_polar(result: object, ax: Axes | None = None) -> Axes:
            return ax if ax is not None else {making}
        """,
    )
    assert refused == {"plot_polar": "reaches a polar axes and returns Axes"}


@pytest.mark.parametrize(
    "making",
    [
        "plt.subplots(subplot_kw=_FLAT)[1]",
        "plt.figure().add_subplot(1, 1, 1, projection=_PROJECTION)",
        "plt.subplot(polar=_FLAG)",
        "plt.subplots(subplot_kw=options)[1]",
    ],
)
def test_a_module_constant_that_asks_for_no_polar_axes_is_let_through(
    tmp_path: pathlib.Path, making: str
) -> None:
    """A constant says what it says; a mapping a caller hands in says nothing."""
    assert not _refused(
        tmp_path,
        plots=f"""
        import matplotlib.pyplot as plt

        _FLAT = {{"projection": "rectilinear"}}
        _PROJECTION = "rectilinear"
        _FLAG = False

        def plot_flat(result: object, options: dict[str, object]) -> Axes:
            return {making}
        """,
    )


def test_a_name_the_function_binds_itself_is_not_read_as_the_module_constant(
    tmp_path: pathlib.Path,
) -> None:
    """A parameter that shadows a flat constant may still be polar."""
    refused = _refused(
        tmp_path,
        plots="""
        import matplotlib.pyplot as plt

        projection = "rectilinear"

        def plot_any(result: object, projection: str = "polar") -> Axes:
            return plt.figure().add_subplot(1, 1, 1, projection=projection)
        """,
    )
    assert refused == {"plot_any": "reaches a polar axes and returns Axes"}


_PANELS = """
import matplotlib.pyplot as plt

def plot_panels(result: object) -> {returns}:
    figure = plt.figure()
    figure.add_subplot(1, 2, 1, projection="polar")
    figure.add_subplot(1, 2, 2)
    raise NotImplementedError
"""


@pytest.mark.parametrize(
    "returns", ["Any", "tuple[Axes, Axes]", "list[Axes]", "Optional[Any]"]
)
def test_a_polar_axes_hidden_behind_any_or_plain_axes_panels_is_refused(
    tmp_path: pathlib.Path, returns: str
) -> None:
    refused = _refused(tmp_path, plots=_PANELS.format(returns=returns))
    assert refused == {"plot_panels": f"reaches a polar axes and returns {returns}"}


@pytest.mark.parametrize(
    "returns", ["tuple[Axes, PolarAxes]", "tuple[PolarAxes, ...]", "None", "np.ndarray"]
)
def test_panels_that_name_their_polar_axes_or_no_axes_are_let_through(
    tmp_path: pathlib.Path, returns: str
) -> None:
    assert not _refused(tmp_path, plots=_PANELS.format(returns=returns))


def test_a_polar_axes_reached_through_an_import_inside_a_method_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """The import in the method's own body is the only route to the renderer."""
    refused = _refused(
        tmp_path,
        renderers="""
        import matplotlib.pyplot as plt

        def draw(result: object) -> PolarAxes:
            return plt.subplot(polar=True)
        """,
        results="""
        class Result:
            def plot(self) -> Axes:
                from .renderers import draw

                return draw(self)
        """,
    )
    assert refused == {"Result.plot": "reaches a polar axes and returns Axes"}


@pytest.mark.parametrize(
    ("receiver", "decorator"), [("self", ""), ("cls", "@classmethod")]
)
def test_a_polar_axes_reached_through_self_or_cls_is_refused(
    tmp_path: pathlib.Path, receiver: str, decorator: str
) -> None:
    """The class's own helper is the only route; nothing is imported."""
    refused = _refused(
        tmp_path,
        results=f"""
        import matplotlib.pyplot as plt

        class Result:
            {decorator}
            def _helper({receiver}) -> PolarAxes:
                return plt.subplot(polar=True)

            {decorator}
            def plot({receiver}) -> Axes:
                return {receiver}._helper()
        """,
    )
    assert refused == {"Result.plot": "reaches a polar axes and returns Axes"}


def test_names_a_package_re_exports_are_followed_to_their_module(
    tmp_path: pathlib.Path,
) -> None:
    """An alias, an axes class and a polar helper, each re-exported by ``__init__``."""
    refused = _refused(
        tmp_path,
        **{
            "_plot._common": """
            import matplotlib.pyplot as plt
            from matplotlib.axes import Axes as PanelAxes

            Pair = tuple[PanelAxes, PanelAxes]

            def new_polar() -> PolarAxes:
                return plt.subplot(polar=True)
            """,
            "_plot.__init__": """
            from ._common import PanelAxes, Pair, new_polar
            """,
            "results": """
            from ._plot import PanelAxes, Pair, new_polar

            def plot_pair(result: object, ax: PanelAxes | None = None) -> PanelAxes | Pair:
                raise NotImplementedError

            def plot_polar(result: object) -> PanelAxes:
                return new_polar()
            """,
        },
    )
    assert refused == {
        "plot_pair": "returns PanelAxes | Pair, and no overload says which "
        "argument decides",
        "plot_polar": "reaches a polar axes and returns PanelAxes",
    }


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
