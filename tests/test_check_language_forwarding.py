#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate against a call that leaves the caller's language behind.

``scripts/check_language_forwarding.py`` indexes every helper that takes a
``language`` parameter and fails on a call to one of them, from a function
where a language is in scope, that does not pass it on. Every such helper
defaults to English, so the omission raises nothing: a Spanish figure simply
ships with an English decimal point on its frequency axis, which is how
``k_weighting_response(48000.0).plot(language="es")`` came to label its lowest
octave ``31.5``.

Matching the call by its text is not enough. A helper is reached under the
name its module was imported by, a result's ``.plot()`` shares its name with
matplotlib's ``Axes.plot``, and a ``**kwargs`` can carry the language or,
when the caller has already bound it by name, provably cannot. The tests below
build small packages in a temporary directory and fix each of those readings,
and the two ways the exemption table can rot.
"""

from __future__ import annotations

import pathlib
import sys
import textwrap

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_language_forwarding as clf

#: The helper every synthetic package draws its axis with, keyword-only like
#: ``format_frequency_axis``, and a formatter that takes it positionally.
_HELPERS = """
def axis(ax, fmin=None, fmax=None, *, language="en"):
    return ax


def fmt(value, language="en"):
    return str(value)
"""


def _tree(tmp_path: pathlib.Path, **modules: str) -> clf.Tree:
    """A package ``pkg`` of *modules* (dotted name to source) in *tmp_path*."""
    sources = {"pkg.__init__": "", "pkg.helpers": _HELPERS, **modules}
    for dotted, source in sources.items():
        path = tmp_path.joinpath(*dotted.split(".")).with_suffix(".py")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(source), encoding="utf-8")
    return clf.Tree.load(((tmp_path, tmp_path),), root=tmp_path)


def _dropped(tmp_path: pathlib.Path, **modules: str) -> list[clf.Finding]:
    found, stale = clf.classify(_tree(tmp_path, **modules), {})
    assert stale == []
    return found


def test_a_dropped_language_is_found(tmp_path: pathlib.Path) -> None:
    """The defect itself: the plot has the language and the axis never sees it."""
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis


            def plot_thing(result, ax, language="en"):
                ax.set_xlabel("Frequency")
                axis(ax, 20.0, 20000.0)
            """
        },
    )
    assert [(f.path, f.line, f.caller, f.helper) for f in found] == [
        ("pkg/plots.py", 7, "plot_thing", "pkg.helpers.axis")
    ]


def test_a_forwarded_language_is_clean(tmp_path: pathlib.Path) -> None:
    """By keyword, and by position where the helper takes it positionally."""
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis, fmt


            def plot_thing(result, ax, language="en"):
                axis(ax, language=language)
                ax.set_title(fmt(result.level, language))
            """
        },
    )
    assert found == []


def test_a_helper_is_followed_through_a_module_and_a_re_export(
    tmp_path: pathlib.Path,
) -> None:
    """``helpers.axis`` and a name the package ``__init__`` re-exports."""
    found = _dropped(
        tmp_path,
        **{
            "pkg.__init__": "from .helpers import axis as frequency_axis\n",
            "pkg.plots": """
            from pkg import frequency_axis, helpers


            def plot_thing(result, ax, language="en"):
                helpers.axis(ax)
                frequency_axis(ax)
            """,
        },
    )
    assert [f.helper for f in found] == ["pkg.helpers.axis", "pkg.helpers.axis"]


def test_kwargs_forwarding_is_clean(tmp_path: pathlib.Path) -> None:
    """A mapping that holds the language, or a ``**kwargs`` it may arrive in."""
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis


            def plot_thing(result, ax, language="en"):
                options = {"language": language}
                axis(ax, **options)


            def plot_other(result, ax, **kwargs):
                language = kwargs.get("language", "en")
                ax.set_title(language)
                axis(ax, **kwargs)
            """
        },
    )
    assert found == []


def test_kwargs_that_cannot_carry_the_language_do_not_forward_it(
    tmp_path: pathlib.Path,
) -> None:
    """A named ``language`` parameter catches the keyword before ``**kwargs``."""
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis


            def plot_thing(result, ax, language="en", **kwargs):
                axis(ax, **kwargs)


            def plot_other(result, ax, **kwargs):
                language = kwargs.pop("language", "en")
                ax.set_title(language)
                axis(ax, **kwargs)
            """
        },
    )
    assert [f.caller for f in found] == ["plot_thing", "plot_other"]


def test_a_function_without_a_language_in_scope_is_not_flagged(
    tmp_path: pathlib.Path,
) -> None:
    """Nothing to forward: the default is the only language the caller has."""
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis


            def draw_axis(ax):
                axis(ax)
            """
        },
    )
    assert found == []


def test_a_nested_function_inherits_the_language_of_its_enclosure(
    tmp_path: pathlib.Path,
) -> None:
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis


            def plot_thing(result, axes, language="en"):
                def _panel(ax):
                    axis(ax)

                for ax in axes:
                    _panel(ax)
            """
        },
    )
    assert [f.caller for f in found] == ["plot_thing.<locals>._panel"]


def test_a_figure_generator_has_the_language_of_its_pass(
    tmp_path: pathlib.Path,
) -> None:
    """``scripts/figures`` reads the language from ``_LANG``, not a parameter."""
    found = _dropped(
        tmp_path,
        **{
            "figures.__init__": "",
            "figures.devices": """
            from pkg.helpers import axis


            def generate_thing(output_dir):
                axis(None)
            """,
        },
    )
    assert [f.caller for f in found] == ["generate_thing"]


def test_a_call_outside_every_function_is_read(tmp_path: pathlib.Path) -> None:
    """A module body and a class body run in the pass their module runs in.

    Neither is a function, and neither was scanned at all, so a generator
    module could prepare its panel at import time and drop the language with
    nothing said, in the one tree that is treated as speaking everywhere.
    """
    found = _dropped(
        tmp_path,
        **{
            "figures.__init__": "",
            "figures.devices": """
            from pkg.helpers import axis

            _PREPARED = axis(None)


            class _Panel:
                default = axis(None)


            def generate_thing(output_dir):
                axis(None)
            """,
        },
    )
    assert [(f.line, f.caller) for f in found] == [
        (4, "<module>"),
        (8, "_Panel.<class>"),
        (12, "generate_thing"),
    ]


def test_a_helper_is_followed_through_an_alias_and_a_partial(
    tmp_path: pathlib.Path,
) -> None:
    """The two indirections the tree writes, and one it does not.

    ``functools.partial`` binds the result and hands the rest on, which is how
    the ISO 17497 fiches pass their drawings to the layout. The bound arguments
    shift the slot the language is taken at. A callable pulled out of a mapping
    stays out of reach, which the module docstring says rather than claims.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            import functools

            from .helpers import axis

            _TABLE = {"axis": axis}


            def via_alias(ax, language="en"):
                alias = axis
                alias(ax)


            def via_partial(ax, language="en"):
                draw = functools.partial(axis, ax)
                draw(20.0, 20000.0)


            def via_partial_that_binds_it(ax, language="en"):
                draw = functools.partial(axis, ax, language=language)
                draw(20.0, 20000.0)


            def via_mapping(ax, language="en"):
                _TABLE["axis"](ax)
            """
        },
    )
    assert [f.caller for f in found] == ["via_alias", "via_partial"]


def test_a_name_only_some_of_whose_methods_take_the_language_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    """One namesake without it switches the untyped-receiver fallback off.

    Silently, until this: every ``result.report(path)`` on a receiver the guard
    cannot type stops being checked the day one class writes a ``report`` that
    takes no language, and the gate stays green.
    """
    tree = _tree(
        tmp_path,
        **{
            "pkg.results": """
            class Result:
                def report(self, path, *, language="en"):
                    return path


            class Adapter:
                def report(self, path):
                    return path
            """
        },
    )
    assert [
        (name, [scope.label for scope in without])
        for name, without in tree.partial_namesakes()
    ] == [("report", ["pkg.results.Adapter.report"])]


def test_a_uniform_name_is_not_reported_as_mixed(tmp_path: pathlib.Path) -> None:
    """Every namesake taking it is the state the fallback needs, not a finding."""
    tree = _tree(
        tmp_path,
        **{
            "pkg.results": """
            class Result:
                def report(self, path, *, language="en"):
                    return path


            class Other:
                def report(self, path, *, language="en"):
                    return path
            """
        },
    )
    assert tree.partial_namesakes() == []


def test_an_exemption_covers_one_call_and_not_its_neighbour(
    tmp_path: pathlib.Path,
) -> None:
    """The key carries the line, so a second call needs a reason of its own.

    The clip whose axis reads the same in both languages is exempt; an axis
    added to the same generator afterwards would have inherited that reason
    without anyone writing one for it.
    """
    tree = _tree(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis


            def animate(ax_a, ax_b, language="en"):
                axis(ax_a, 50.0, 8000.0)
                axis(ax_b, 12.5, 20000.0)
            """
        },
    )
    key = "pkg/plots.py:6::animate -> pkg.helpers.axis"
    found, stale = clf.classify(tree, {key: "63 to 8k reads the same in both"})
    assert [(f.line, f.caller) for f in found] == [(7, "animate")]
    assert stale == []


def test_an_exemption_whose_call_moved_is_stale(tmp_path: pathlib.Path) -> None:
    """A moved call is re-approved rather than carried along unread."""
    source = "\n" + _EXEMPTED
    tree = _tree(tmp_path, **{"pkg.plots": source})
    found, stale = clf.classify(tree, {_KEY: "an axis a reader compares in English"})
    assert [f.line for f in found] == [7]
    assert stale == [_KEY]


def test_a_method_call_is_covered(tmp_path: pathlib.Path) -> None:
    """A result's ``.plot()``, typed from an annotation or from a return."""
    found = _dropped(
        tmp_path,
        **{
            "pkg.results": """
            from __future__ import annotations


            class Result:
                def plot(self, ax=None, *, language="en", **kwargs):
                    return ax


            def compute() -> Result:
                return Result()
            """,
            "pkg.plots": """
            from __future__ import annotations

            from typing import TYPE_CHECKING

            from .results import compute

            if TYPE_CHECKING:
                from .results import Result


            def figure(result: Result, ax, language="en"):
                result.plot(ax)
                compute().plot(ax=ax, language=language)
                again = compute()
                again.plot(ax, color="k")
                ax.plot([1, 2], [3, 4])
            """,
        },
    )
    assert [(f.line, f.helper) for f in found] == [
        (13, "pkg.results.Result.plot"),
        (16, "pkg.results.Result.plot"),
    ]


def test_an_untyped_result_plot_is_told_apart_from_axes_plot(
    tmp_path: pathlib.Path,
) -> None:
    """No positional data, or ``ax=``, is a result; data first is matplotlib."""
    found = _dropped(
        tmp_path,
        **{
            "pkg.results": """
            class Result:
                def plot(self, ax=None, *, language="en"):
                    return ax
            """,
            "pkg.plots": """
            def figure(thing, ax, language="en"):
                thing.plot(ax=ax)
                ax.plot(thing.x, thing.y, color="k")
            """,
        },
    )
    assert [(f.line, f.helper) for f in found] == [(3, "?.plot")]


def test_a_method_that_hands_its_kwargs_on_takes_the_language(
    tmp_path: pathlib.Path,
) -> None:
    """``plot(ax, **kwargs)`` that reaches the renderer is held to the rule."""
    found = _dropped(
        tmp_path,
        **{
            "pkg.results": """
            from __future__ import annotations


            class Result:
                def plot(self, ax=None, **kwargs):
                    from .helpers import axis

                    return axis(ax, **kwargs)
            """,
            "pkg.plots": """
            from .results import Result


            def figure(ax, language="en"):
                Result().plot(ax)
            """,
        },
    )
    assert [f.helper for f in found] == ["pkg.results.Result.plot"]


def test_a_literal_language_does_not_forward_the_callers(
    tmp_path: pathlib.Path,
) -> None:
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis, fmt


            def plot_thing(result, ax, language="en"):
                axis(ax, language="en")
                ax.set_title(fmt(result.level, "en"))
            """
        },
    )
    assert [f.helper for f in found] == ["pkg.helpers.axis", "pkg.helpers.fmt"]


def test_a_star_argument_cannot_reach_a_keyword_only_language(
    tmp_path: pathlib.Path,
) -> None:
    """``axis(ax, *range)`` fills the limits and leaves the language alone."""
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis, fmt

            _RANGE = (20.0, 20000.0)


            def plot_thing(result, ax, language="en"):
                axis(ax, *_RANGE)
                ax.set_title(fmt(*result.pair))
            """
        },
    )
    assert [f.helper for f in found] == ["pkg.helpers.axis"]


_EXEMPTED = """
from .helpers import axis


def plot_thing(result, ax, language="en"):
    axis(ax)
"""

_KEY = "pkg/plots.py:6::plot_thing -> pkg.helpers.axis"


def test_an_exemption_is_honoured(tmp_path: pathlib.Path) -> None:
    tree = _tree(tmp_path, **{"pkg.plots": _EXEMPTED})
    found, stale = clf.classify(tree, {_KEY: "an axis a reader compares in English"})
    assert found == []
    assert stale == []


def test_an_exemption_whose_call_forwards_now_is_stale(
    tmp_path: pathlib.Path,
) -> None:
    source = _EXEMPTED.replace("axis(ax)", "axis(ax, language=language)")
    tree = _tree(tmp_path, **{"pkg.plots": source})
    found, stale = clf.classify(tree, {_KEY: "an axis a reader compares in English"})
    assert found == []
    assert stale == [_KEY]


def test_every_exemption_carries_a_reason() -> None:
    assert all(reason.strip() for reason in clf.EXEMPT.values())


def test_the_tree_passes_its_language_on() -> None:
    """The corpus itself, which is what the gate protects."""
    assert clf.main([]) == 0
