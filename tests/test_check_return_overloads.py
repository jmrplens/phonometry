#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate on returns whose type one argument decides, written as one type.

``scripts/check_return_overloads.py`` reads every function of the package and
asks that a return naming one axes and several (a tuple, a list or an array
of them) stand on an implementation with overload heads, never on a head,
that a function reaching a polar axes say ``PolarAxes``, or have a head that
does, and that a return naming a single value and an array stand on an
implementation whose heads say each case, the union only on the last head
left for what a type checker cannot shape. Its own run only says the tree is clean today; these tests fix what it
must catch, on small packages written for the purpose (a multiline signature,
an alias, a renamed import, a polar axes two calls away), and what it must
let through. Each route by which it follows a name (an import inside a
function, ``self`` and ``cls``, a package that re-exports) has a case of its
own, so that a route that breaks fails here even when another one would have
found the same function.
"""

from __future__ import annotations

import ast
import pathlib
import sys
import textwrap

import numpy as np
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


def test_a_generic_alias_is_read_with_the_arguments_it_is_given(
    tmp_path: pathlib.Path,
) -> None:
    """``Many[Axes]`` is a column of axes, whatever module defines ``Many``.

    A generic alias (``type Many[P] = tuple[P, ...]``, or an assignment generic
    in a module-level ``TypeVar``) stands for its value with each parameter
    read as the argument a use gives it, in the module that writes the use,
    so an axes class imported there under another name is still an axes.
    """
    refused = _refused(
        tmp_path,
        types="""
        from typing import TypeVar

        T = TypeVar("T")

        type Many[P] = tuple[P, ...]
        Listed = list[T]
        type Either[S, A] = S | NDArray[A]
        """,
        plots="""
        from matplotlib.axes import Axes as Panel

        from .types import Either, Listed, Many

        def plot_many(ax: Axes | None = None) -> Axes | Many[Axes]:
            raise NotImplementedError

        def plot_listed(ax: Axes | None = None) -> Axes | Listed[Axes]:
            raise NotImplementedError

        def plot_renamed(ax: Panel | None = None) -> Panel | Many[Panel]:
            raise NotImplementedError

        def level(x: object) -> Either[float, np.float64]:
            raise NotImplementedError

        def plot_counts(ax: Axes | None = None) -> Axes | Many[int]:
            raise NotImplementedError
        """,
    )
    assert sorted(refused) == ["level", "plot_listed", "plot_many", "plot_renamed"]


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


def test_a_name_the_function_binds_itself_reaches_no_function_of_the_package(
    tmp_path: pathlib.Path,
) -> None:
    """A call is looked up as Python looks it up: the function first.

    A call through a parameter, an assignment or a function defined inside
    the caller was followed to the module's function of the same name, so a
    function that never reaches it was refused for the polar axes it makes.
    """
    refused = _refused(
        tmp_path,
        plots="""
        import matplotlib.pyplot as plt

        def new_polar() -> PolarAxes:
            return plt.subplots(subplot_kw={"projection": "polar"})[1]

        def by_a_parameter(result: object, new_polar: Any) -> Axes:
            return new_polar()

        def by_an_assignment(result: object) -> Axes:
            new_polar = plt.gca
            return new_polar()

        def by_a_nested_function(result: object) -> Axes:
            def new_polar() -> Axes:
                return plt.subplots()[1]

            return new_polar()

        def through_the_module(result: object) -> Axes:
            return new_polar()
        """,
    )
    assert sorted(refused) == ["through_the_module"]


def test_every_definition_of_a_function_written_in_two_branches_is_read(
    tmp_path: pathlib.Path,
) -> None:
    """A function written in each branch of an ``if`` is either at run time.

    The functions were kept by their dotted name and the second definition
    took the place of the first, so a union the first returns without
    overloads passed, and a helper that makes a polar axes in one branch
    only made no caller of it reach one.
    """
    refused = _refused(
        tmp_path,
        plots="""
        import sys

        import matplotlib.pyplot as plt

        if sys.version_info >= (3, 13):
            def plot_pair(
                result: object, ax: Axes | None = None
            ) -> Axes | tuple[Axes, Axes]:
                return ax
        else:
            def plot_pair(result: object, ax: Axes | None = None) -> Axes:
                return ax

        if sys.version_info >= (3, 13):
            def _new_axes():
                return plt.subplots(subplot_kw={"projection": "polar"})[1]
        else:
            def _new_axes():
                return plt.subplots()[1]

        def plot_polar(result: object) -> Axes:
            return _new_axes()
        """,
    )
    assert sorted(refused) == ["plot_pair", "plot_polar"]


def test_a_definition_a_later_one_replaces_is_never_reached(
    tmp_path: pathlib.Path,
) -> None:
    """A call reaches the definitions a name may hold where it runs.

    A later ``def`` of a name was kept beside the earlier one as a second
    definition, though it replaces it unconditionally, so a caller of the
    plain helper was refused for the polar axes of code that never runs, at
    the top of a module and in a class. Of two imports of one name in the
    caller, the call read the first of the function, not the one written
    last before it.
    """
    refused = _refused(
        tmp_path,
        helpers="""
        import matplotlib.pyplot as plt

        def new_polar() -> PolarAxes:
            return plt.subplots(subplot_kw={"projection": "polar"})[1]

        def new_plain() -> Axes:
            return plt.subplots()[1]
        """,
        plots="""
        import matplotlib.pyplot as plt

        def _new_axes():
            return plt.subplots(subplot_kw={"projection": "polar"})[1]

        def _new_axes():
            return plt.subplots()[1]

        def plot_replaced(result: object) -> Axes:
            return _new_axes()

        class Result:
            def _draw(self):
                return plt.subplots(subplot_kw={"projection": "polar"})[1]

            def _draw(self):
                return plt.subplots()[1]

            def plot(self) -> Axes:
                return self._draw()

        if FAST:
            def _maybe_polar():
                return plt.subplots(subplot_kw={"projection": "polar"})[1]

        def plot_maybe(result: object) -> Axes:
            return _maybe_polar()

        def plot_imported(result: object, fast: bool) -> Axes:
            if fast:
                from .helpers import new_polar as make

                return plt.gca()
            from .helpers import new_plain as make

            return make()
        """,
    )
    assert sorted(refused) == ["plot_maybe"]


def test_a_call_from_a_function_reaches_every_definition_from_its_def_on(
    tmp_path: pathlib.Path,
) -> None:
    """A function reads the module's names when it is called, which may be
    during the import and before a later definition of a name, so a call in
    it may reach every definition that stands from its ``def`` on.

    ``FIGURE = plot_early(None)`` runs ``plot_early`` while ``_new_axes``
    still draws polar axes; the module's names were read as they stand once
    it has run, so only the plain ``_new_axes`` was reached and the polar
    axes passed.
    """
    refused = _refused(
        tmp_path,
        plots="""
        import matplotlib.pyplot as plt

        def _new_axes():
            return plt.subplots(subplot_kw={"projection": "polar"})[1]

        def plot_early(result: object) -> Axes:
            return _new_axes()

        FIGURE = plot_early(None)

        def _new_axes():
            return plt.subplots()[1]
        """,
    )
    assert sorted(refused) == ["plot_early"]


def test_a_method_of_a_class_a_later_class_replaces_is_never_reached(
    tmp_path: pathlib.Path,
) -> None:
    """A method is read in the class that holds it, and a class a later one
    of its name replaces holds none the module keeps.

    The ``_draw`` of two ``Result`` classes were read against each other, and
    two blocks that share nothing keep both, so the polar axes of the first,
    which no call reaches, refused the plain ``plot`` of the second.
    """
    refused = _refused(
        tmp_path,
        plots="""
        import matplotlib.pyplot as plt

        class Result:
            def _draw(self):
                return plt.subplots(subplot_kw={"projection": "polar"})[1]

        class Result:
            def _draw(self):
                return plt.subplots()[1]

            def plot(self) -> Axes:
                return self._draw()
        """,
    )
    assert refused == {}


def test_a_replaced_definition_is_never_reached_through_either_import(
    tmp_path: pathlib.Path,
) -> None:
    """A call that two imports may reach reaches what each module holds.

    The definitions a module holds once it has run were picked only when one
    target stood for the name, so with an import in each branch of an
    ``if``, the polar ``make`` a later plain one replaces was still read and
    the plain ``plot`` refused.
    """
    refused = _refused(
        tmp_path,
        helpers="""
        import matplotlib.pyplot as plt

        def make():
            return plt.subplots(subplot_kw={"projection": "polar"})[1]

        def make():
            return plt.subplots()[1]
        """,
        others="""
        import matplotlib.pyplot as plt

        def make():
            return plt.subplots()[1]
        """,
        plots="""
        def plot_either(result: object, fast: bool) -> Axes:
            if fast:
                from .helpers import make
            else:
                from .others import make
            return make()
        """,
    )
    assert refused == {}


def test_a_module_s_import_in_each_branch_is_either(tmp_path: pathlib.Path) -> None:
    """A name a module imports in each branch of an ``if`` is either at a call.

    The imports of a module were read into one table, the last import of a
    name standing for it, so the polar ``make`` the first branch imports was
    never read and the plain ``plot`` that may return it passed.
    """
    refused = _refused(
        tmp_path,
        helpers="""
        import matplotlib.pyplot as plt

        def make():
            return plt.subplots(subplot_kw={"projection": "polar"})[1]
        """,
        others="""
        import matplotlib.pyplot as plt

        def make():
            return plt.subplots()[1]
        """,
        plots="""
        if FAST:
            from .helpers import make
        else:
            from .others import make

        def plot_either(result: object) -> Axes:
            return make()
        """,
    )
    assert list(refused) == ["plot_either"]


def test_what_an_if_type_checking_block_binds_is_no_function_a_call_reaches(
    tmp_path: pathlib.Path,
) -> None:
    """A ``def`` or an import under ``if TYPE_CHECKING:`` never runs, so a
    plain ``plot`` that returns what ``make`` makes reaches none of them. They
    were read as what a function swaps in under ``global``, and as either of
    two beside the block's ``else``, so the polar axes they make were held
    against the plot.
    """
    refused = _refused(
        tmp_path,
        polar="""
        import matplotlib.pyplot as plt

        def make():
            return plt.subplots(subplot_kw={"projection": "polar"})[1]
        """,
        plots="""
        import matplotlib.pyplot as plt

        def make():
            return plt.subplots()[1]

        def swap():
            global make
            if TYPE_CHECKING:
                from .polar import make

        def plot_imported(result: object) -> Axes:
            return make()

        def build():
            return plt.subplots()[1]

        def swap_def():
            global build
            if TYPE_CHECKING:
                def build():
                    return plt.subplots(subplot_kw={"projection": "polar"})[1]

        def plot_defined(result: object) -> Axes:
            return build()

        if TYPE_CHECKING:
            def either():
                return plt.subplots(subplot_kw={"projection": "polar"})[1]
        else:
            def either():
                return plt.subplots()[1]

        def plot_either(result: object) -> Axes:
            return either()
        """,
    )
    assert refused == {}


_POLAR = 'plt.subplots(subplot_kw={"projection": "polar"})[1]'


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            f"""
        def plot_it(result: object) -> Axes:
            if not TYPE_CHECKING:
                return plt.subplots()[1]
            else:
                return {_POLAR}
        """,
            id="the-else-of-a-negated-test",
        ),
        pytest.param(
            f"""
        def plot_it(result: object) -> Axes:
            return {_POLAR} if TYPE_CHECKING else plt.subplots()[1]
        """,
            id="a-branch-of-an-expression",
        ),
        pytest.param(
            f"""
        if TYPE_CHECKING:
            def plot_it(result: object) -> Axes:
                return {_POLAR}
        """,
            id="a-function-in-the-block-at-the-top",
        ),
        pytest.param(
            f"""
        class Plotter:
            if TYPE_CHECKING:
                def plot_it(self) -> Axes:
                    return {_POLAR}
        """,
            id="a-method-in-the-block",
        ),
    ],
)
def test_what_a_test_on_type_checking_keeps_from_running_returns_nothing(
    tmp_path: pathlib.Path, source: str
) -> None:
    """Polar axes no run returns hide nothing, wherever the block is written."""
    planted = "import matplotlib.pyplot as plt\n" + textwrap.dedent(source)
    assert _refused(tmp_path, plots=planted) == {}


def test_the_body_of_a_negated_test_returns_what_it_returns(
    tmp_path: pathlib.Path,
) -> None:
    """``if not TYPE_CHECKING:`` is what the program runs."""
    refused = _refused(
        tmp_path,
        plots=f"""
        import matplotlib.pyplot as plt

        def plot_it(result: object) -> Axes:
            if not TYPE_CHECKING:
                return {_POLAR}
            return plt.subplots()[1]
        """,
    )
    assert set(refused) == {"plot_it"}


def test_what_a_function_s_if_type_checking_block_returns_is_not_returned(
    tmp_path: pathlib.Path,
) -> None:
    """The body of an ``if TYPE_CHECKING:`` in a function never runs, so the polar
    axes it returns are no return of a plain ``plot``.
    """
    refused = _refused(
        tmp_path,
        plots="""
        import matplotlib.pyplot as plt

        def plot_it(result: object) -> Axes:
            if TYPE_CHECKING:
                return plt.subplots(subplot_kw={"projection": "polar"})[1]
            return plt.subplots()[1]
        """,
    )
    assert refused == {}


def test_a_def_or_an_import_a_function_makes_under_global_may_be_reached(
    tmp_path: pathlib.Path,
) -> None:
    """A function that declares a module name ``global`` and defines or
    imports it there may have run before any call of the name, so the call
    may reach what it bound, as one in a branch of an ``if`` at the top may.

    The module's names were read from its top alone, so after ``_go_polar()``
    swapped in a helper that makes polar axes, a plain ``plot`` that returns
    what it makes passed, called bare, through an import of the name, through
    the module's attribute and through a module that re-exports the name and
    swaps it there; so did one whose helper a function imports under
    ``global`` from a module of polar helpers.
    """
    refused = _refused(
        tmp_path,
        polar="""
        import matplotlib.pyplot as plt

        def make():
            return plt.subplots(subplot_kw={"projection": "polar"})[1]
        """,
        helpers="""
        import matplotlib.pyplot as plt

        def _new_axes():
            return plt.subplots()[1]

        def _go_polar():
            global _new_axes
            def _new_axes():
                return plt.subplots(subplot_kw={"projection": "polar"})[1]

        def plot_swapped(result: object) -> Axes:
            return _new_axes()

        def _plain():
            return plt.subplots()[1]

        def _import_polar():
            global _plain
            from .polar import make as _plain

        def plot_imported(result: object) -> Axes:
            return _plain()

        def _kept():
            return plt.subplots()[1]

        def plot_kept(result: object) -> Axes:
            return _kept()
        """,
        shelf="""
        import matplotlib.pyplot as plt

        from .helpers import _kept

        def _swap():
            global _kept
            def _kept():
                return plt.subplots(subplot_kw={"projection": "polar"})[1]
        """,
        plots="""
        from . import helpers
        from .helpers import _new_axes
        from .shelf import _kept

        def plot_through_the_import(result: object) -> Axes:
            return _new_axes()

        def plot_through_the_attribute(result: object) -> Axes:
            return helpers._new_axes()

        def plot_through_a_re_export(result: object) -> Axes:
            return _kept()
        """,
    )
    assert sorted(refused) == [
        "plot_imported",
        "plot_swapped",
        "plot_through_a_re_export",
        "plot_through_the_attribute",
        "plot_through_the_import",
    ]


def test_a_generic_class_s_type_parameter_is_no_function_of_the_module(
    tmp_path: pathlib.Path,
) -> None:
    """A method reads a generic class's type parameter as the class's own, a
    method of a class written inside it too, whatever the module binds of that
    spelling.

    The lookup went from the method to the module past the class, so a call
    of ``T`` read as a call of the module's function ``T``, which makes polar
    axes, and the plain ``plot`` was refused. The same call in a class that
    declares no type parameter still reaches it.
    """
    refused = _refused(
        tmp_path,
        plots="""
        import matplotlib.pyplot as plt

        def T():
            return plt.subplots(subplot_kw={"projection": "polar"})[1]

        class Plotter[T]:
            def plot(self, result: object) -> Axes:
                return T()

            class Inner:
                def plot(self, result: object) -> Axes:
                    return T()

        class Plain:
            def plot(self, result: object) -> Axes:
                return T()
        """,
    )
    assert list(refused) == ["Plain.plot"]


def test_each_branch_keeps_its_own_overload_heads(tmp_path: pathlib.Path) -> None:
    """Overloads written in each branch of an ``if`` belong to that branch's function.

    The heads of the second branch joined the first branch's function, and
    the second implementation was kept with none, so a union it returns
    under heads of its own was refused for having no overloads.
    """
    refused = _refused(
        tmp_path,
        levels="""
        import sys

        if sys.version_info >= (3, 13):
            @overload
            def level(x: float) -> float: ...
            @overload
            def level(x: NDArray[np.float64]) -> NDArray[np.float64]: ...
            def level(x: float | NDArray[np.float64]) -> float | NDArray[np.float64]:
                return x
        else:
            @overload
            def level(x: float) -> float: ...
            @overload
            def level(x: NDArray[np.float64]) -> NDArray[np.float64]: ...
            def level(x: float | NDArray[np.float64]) -> float | NDArray[np.float64]:
                return x
        """,
    )
    assert refused == {}


def _package_of(tmp_path: pathlib.Path, **modules: str) -> cro.Package:
    root = _package(tmp_path, **modules)
    return cro.Package(sorted(root.rglob("*.py")), root)


def _call_in(package: cro.Package, key: str) -> tuple[cro.Function, ast.expr]:
    """The function under *key* and the callee of the one call it writes."""
    function = package.functions[key]
    assert function.implementation is not None
    calls = [
        node
        for node in ast.walk(function.implementation)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    return function, calls[-1].func


def test_a_call_is_read_in_the_scope_it_is_written_in(tmp_path: pathlib.Path) -> None:
    """An import counts only in the function that makes it, and a nested
    function reads the names of the definition it is written in.

    The imports of a function were read from every node of it, those of the
    functions written inside it included, so a call beside them in the
    function, or in a sibling, reached what another function imported. A
    function written in the second definition of the function around it
    read that function's names in the first definition.
    """
    package = _package_of(
        tmp_path,
        polar="""
        def new_axes():
            return None
        """,
        plots="""
        import sys

        def new_axes():
            return None

        def beside_a_nested_import(result: object) -> Axes:
            def make() -> None:
                from .polar import new_axes

                del new_axes

            return new_axes()

        if sys.version_info >= (3, 13):
            def outer(result: object) -> Axes:
                from .polar import new_axes

                def inner() -> Axes:
                    return new_axes()

                return inner()
        else:
            def outer(result: object) -> Axes:
                def inner() -> Axes:
                    return new_axes()

                return inner()
        """,
    )
    function, func = _call_in(package, "pkg.plots.beside_a_nested_import")
    assert package.call_target(function, func) == "pkg.plots.new_axes"
    first = package.functions["pkg.plots.outer.inner"]
    second = package.functions["pkg.plots.outer.inner#2"]
    for inner, reached in (
        (first, "pkg.polar.new_axes"),
        (second, "pkg.plots.new_axes"),
    ):
        assert inner.implementation is not None
        call = next(
            node
            for node in ast.walk(inner.implementation)
            if isinstance(node, ast.Call)
        )
        assert package.call_target(inner, call.func) == reached


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


# ---------------------------------------------------------------------------
# A single value or an array of them
# ---------------------------------------------------------------------------


def test_a_number_or_an_array_without_overloads_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        levels="""
        def room_constant(
            surface_area: float,
            mean_absorption: object,
        ) -> (
            float
            | NDArray[np.float64]
        ):
            raise NotImplementedError
        """,
    )
    assert refused == {
        "room_constant": "returns float | NDArray[np.float64], and no overload "
        "says which argument decides between the value and the array"
    }


@pytest.mark.parametrize(
    "returns",
    [
        "np.ndarray | float",
        "float | NDArray[np.float64]",
        "Union[float, np.ndarray]",
        "Optional[float] | np.ndarray",
        "int | np.ndarray",
        "complex | NDArray[np.complex128]",
        "bool | NDArray[np.bool_]",
        "np.float64 | NDArray[np.float64]",
        "np.double | np.ndarray",
        "np.int_ | np.ndarray",
        "float | np.matrix",
        "np.floating[Any] | np.ndarray",
        "Literal['A', 'B'] | NDArray[np.str_]",
        "str | NDArray[np.str_]",
        "'float | NDArray[np.float64]'",
    ],
)
def test_every_spelling_of_a_value_or_an_array_is_read(
    tmp_path: pathlib.Path, returns: str
) -> None:
    refused = _refused(
        tmp_path,
        levels=f"""
        def level(x: object) -> {returns}:
            raise NotImplementedError
        """,
    )
    assert list(refused) == ["level"]


def test_every_numpy_scalar_and_array_class_is_known() -> None:
    """The gate names numpy's types by hand, so a new numpy cannot slip one past it.

    It stays free of numpy, which leaves the two sets to be kept against the
    numpy installed here: every scalar class it exports (a subclass of
    ``numpy.generic``, aliases such as ``double`` and ``int_`` included) is a
    single value, and every array class (a subclass of ``numpy.ndarray``) an
    array.
    """
    exported = {name: getattr(np, name) for name in dir(np)}
    classes = {name: obj for name, obj in exported.items() if isinstance(obj, type)}
    scalars = {f"numpy.{n}" for n, c in classes.items() if issubclass(c, np.generic)}
    arrays = {f"numpy.{n}" for n, c in classes.items() if issubclass(c, np.ndarray)}
    assert scalars - cro._SCALARS == set()
    assert arrays - cro._ARRAYS == set()


@pytest.mark.parametrize(
    "returns",
    [
        "float",
        "NDArray[np.float64]",
        "float | None",
        "NDArray[np.float64] | None",
        "tuple[float, NDArray[np.float64]]",
        "dict[int, float | np.ndarray]",
        "list[float]",
    ],
)
def test_a_return_that_is_not_a_value_or_an_array_is_let_through(
    tmp_path: pathlib.Path, returns: str
) -> None:
    assert not _refused(
        tmp_path,
        levels=f"""
        def level(x: object) -> {returns}:
            raise NotImplementedError
        """,
    )


def test_an_alias_of_the_value_or_the_array_is_read_through(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        kinds="""
        Grade = Literal["A", "B", "C"]
        Levels = NDArray[np.float64]
        Either = float | Levels
        """,
        levels="""
        from .kinds import Either, Grade

        def level(x: object) -> Either:
            raise NotImplementedError

        def grade(x: object) -> Grade | NDArray[np.str_]:
            raise NotImplementedError
        """,
    )
    assert set(refused) == {"level", "grade"}


_SCALAR_HEADS = """
from numpy.typing import ArrayLike

@overload
def level[S: float](x: S) -> float: ...
@overload
def level[V: list[float]](x: V) -> NDArray[np.float64]: ...
@overload
def level[A: ArrayLike](x: A) -> float | NDArray[np.float64]: ...
def level(x: ArrayLike) -> float | NDArray[np.float64]:
    raise NotImplementedError
"""


def test_heads_that_say_each_case_let_the_last_resort_through(
    tmp_path: pathlib.Path,
) -> None:
    """The union head is the one left for what a type checker cannot shape."""
    assert not _refused(tmp_path, levels=_SCALAR_HEADS)


@pytest.mark.parametrize(
    ("head", "union"),
    [
        (
            "def level[S: float](x: S) -> float: ...",
            "def level[S: float](x: S) -> float | NDArray[np.float64]: ...",
        ),
        (
            "def level[V: list[float]](x: V) -> NDArray[np.float64]: ...",
            "def level[V: list[float]](x: V) -> float | NDArray[np.float64]: ...",
        ),
    ],
)
def test_heads_that_leave_one_case_unsaid_are_refused(
    tmp_path: pathlib.Path, head: str, union: str
) -> None:
    """Without a head for the value alone, or the array alone, every union head fails."""
    refused = _refused(tmp_path, levels=_SCALAR_HEADS.replace(head, union))
    assert refused
    assert all(name.startswith("level (overload") for name in refused), refused
    assert all(
        "no other head returns the value alone" in why for why in refused.values()
    )


@pytest.mark.parametrize(
    ("heads", "missing"),
    [
        (
            """
            @overload
            def level[S: float](x: S) -> float: ...
            """,
            "the array",
        ),
        (
            """
            @overload
            def level[V: list[float]](x: V) -> NDArray[np.float64]: ...
            """,
            "the value",
        ),
    ],
)
def test_heads_that_never_return_one_case_leave_the_union_refused(
    tmp_path: pathlib.Path, heads: str, missing: str
) -> None:
    """A type checker reads only the heads: a float head alone refuses every array."""
    refused = _refused(
        tmp_path,
        levels=textwrap.dedent(heads)
        + """
def level(x: object) -> float | NDArray[np.float64]:
    raise NotImplementedError
""",
    )
    assert refused == {
        "level": f"returns float | NDArray[np.float64], and no overload head "
        f"returns {missing}"
    }


def test_heads_overloaded_on_something_else_still_need_both_cases(
    tmp_path: pathlib.Path,
) -> None:
    """Two heads for two keywords, each returning the union, say nothing of the shape."""
    refused = _refused(
        tmp_path,
        levels="""
        @overload
        def distance(room_constant: object) -> float | np.ndarray: ...
        @overload
        def distance(*, absorption_area: object) -> float | np.ndarray: ...
        def distance(
            room_constant: object = None, *, absorption_area: object = None
        ) -> float | np.ndarray:
            raise NotImplementedError
        """,
    )
    assert set(refused) == {
        "distance (overload room_constant: object)",
        "distance (overload absorption_area: object)",
    }


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


def test_a_statement_in_any_block_is_read_through() -> None:
    """The statements of a ``case``, an ``except*``, a loop and a ``while`` are
    read as those of an ``if`` or a ``try`` are.

    Only ``if``, ``try`` and ``with`` were read through, so a definition or an
    assignment in any other block was missed.
    """
    source = textwrap.dedent(
        """\
        import contextlib
        import sys

        match sys.maxsize:
            case 0:
                from json import dumps as in_case
                IN_CASE = 0
            case _:
                from json import dumps as in_case
                IN_CASE = 1
        try:
            from json import loads as in_try
            IN_TRY = 1
        except* ImportError:
            pass
        with contextlib.nullcontext():
            from json import JSONDecoder as in_with
            IN_WITH = 1
        for _ in range(1):
            from json import JSONEncoder as in_loop
            IN_LOOP = 1
        while False:
            IN_WHILE = 1
        """
    )
    statements = {ast.unparse(node) for node in cro._statements(ast.parse(source).body)}
    assert {"IN_CASE = 1", "IN_TRY = 1", "IN_LOOP = 1", "IN_WHILE = 1"} <= statements
