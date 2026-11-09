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

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_language_forwarding as clf

#: The tests that read the whole package run on one worker (rule T19), one
#: after the other, rather than two of them on two workers at once.
pytestmark = pytest.mark.xdist_group("language-forwarding")

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


def test_what_an_if_type_checking_block_imports_is_no_helper_a_call_reaches(
    tmp_path: pathlib.Path,
) -> None:
    """An import under ``if TYPE_CHECKING:`` never runs, so a call of ``axis``
    reaches the helper of that name and no other. It was read as what a
    function swaps in under ``global``, and as either of two beside the import
    at the top, so the call was refused for dropping ``fmt``'s language too.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.under_global": """
            from typing import TYPE_CHECKING

            from .helpers import axis


            def swap():
                global axis
                if TYPE_CHECKING:
                    from .helpers import fmt as axis


            def plot(result, ax, language="en"):
                axis(ax)
            """,
            "pkg.at_the_top": """
            from typing import TYPE_CHECKING

            from .helpers import axis

            if TYPE_CHECKING:
                from .helpers import fmt as axis


            def plot(result, ax, language="en"):
                axis(ax)
            """,
        },
    )
    assert {(f.path, f.helper) for f in found} == {
        ("pkg/under_global.py", "pkg.helpers.axis"),
        ("pkg/at_the_top.py", "pkg.helpers.axis"),
    }


def test_a_definition_the_negated_test_keeps_from_running_is_no_definition(
    tmp_path: pathlib.Path,
) -> None:
    """The ``else`` of ``if not TYPE_CHECKING:`` never runs, so a function written
    there is judged as nothing, and the body of that test runs, so one written
    there is judged as any other.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.mod": """
            from typing import TYPE_CHECKING

            from .helpers import axis

            if not TYPE_CHECKING:
                def runs(ax, language="en"):
                    return axis(ax)
            else:
                def never(ax, language="en"):
                    return axis(ax)
            """
        },
    )
    assert [finding.caller for finding in found] == ["runs"]


def test_a_parameter_defaulting_to_the_helper_reaches_it(
    tmp_path: pathlib.Path,
) -> None:
    """A parameter whose default names a helper holds it at any call that does
    not hand it another, read where the ``def`` runs its defaults, so the call
    drops the language as a call of the helper does. A parameter with no default,
    or a default that names no helper, reaches none.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.mod": """
            from . import helpers
            from .helpers import axis

            def same_name(ax, axis=axis, language="en"):
                return axis(ax)

            def other_name(ax, draw=axis, *, language="en"):
                return draw(ax)

            def dotted(ax, axis=helpers.axis, language="en"):
                return axis(ax)

            def no_default(ax, axis, language="en"):
                return axis(ax)

            def default_of_none(ax, axis=None, language="en"):
                return axis(ax)
            """
        },
    )
    assert sorted(finding.caller for finding in found) == [
        "dotted",
        "other_name",
        "same_name",
    ]


def test_a_comprehension_or_a_lambda_keeps_the_name_it_binds_for_itself(
    tmp_path: pathlib.Path,
) -> None:
    """A comprehension's variable and a lambda's parameter are names of their
    own, for what they hold and no further. A call of one is no call of the
    helper of that spelling; a call of that spelling beside them still is.

    Every name a comprehension stored counted as a local of the whole
    function, so ``axis(ax)`` written after one passed, and a lambda's
    parameter was not read at all, so a call of it was refused.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.inside": """
            from . import helpers
            from .helpers import axis


            def by_comprehension(result, ax, makers, language="en"):
                return [axis(ax) for axis in makers]


            def by_lambda(result, ax, language="en"):
                return (lambda axis: axis(ax))(print)


            def by_module(result, ax, modules, language="en"):
                return [helpers.axis(ax) for helpers in modules]
            """,
            "pkg.beside": """
            from .helpers import axis


            def beside_comprehension(result, ax, makers, language="en"):
                names = [axis for axis in makers]
                axis(ax)
                return names


            def beside_lambda(result, ax, language="en"):
                other = lambda axis: axis
                axis(ax)
                return other
            """,
        },
    )
    assert sorted(f.caller for f in found) == [
        "beside_comprehension",
        "beside_lambda",
    ]


def test_a_call_in_a_function_s_if_type_checking_block_drops_nothing(
    tmp_path: pathlib.Path,
) -> None:
    """The body of an ``if TYPE_CHECKING:`` in a function never runs, so a call
    written there drops no language; one in its ``else`` runs, and does.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from typing import TYPE_CHECKING

            from .helpers import axis


            def in_the_block(result, ax, language="en"):
                if TYPE_CHECKING:
                    axis(ax)


            def in_the_else(result, ax, language="en"):
                if TYPE_CHECKING:
                    pass
                else:
                    axis(ax)
            """,
        },
    )
    assert [f.caller for f in found] == ["in_the_else"]


def test_a_type_parameter_spelt_like_a_helper_is_not_the_helper(
    tmp_path: pathlib.Path,
) -> None:
    """A generic function's type parameter is its own name, and a generic
    class's is its methods' and those of a class written in it, so a call of
    one is no call of the helper of that spelling. The same call with no type
    parameter still drops the language.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis


            def by_function[axis](result, ax, language="en"):
                axis(ax, 20.0, 20000.0)


            class ByClass[axis]:
                def draw(self, ax, language="en"):
                    axis(ax, 20.0, 20000.0)

                class Inner:
                    def draw(self, ax, language="en"):
                        axis(ax, 20.0, 20000.0)


            def plain(result, ax, language="en"):
                axis(ax, 20.0, 20000.0)
            """
        },
    )
    assert [f.caller for f in found] == ["plain"]


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


def test_the_later_of_two_bindings_of_a_name_is_the_one_a_call_reaches(
    tmp_path: pathlib.Path,
) -> None:
    """Of two imports of one name, or two definitions, the call reaches the later.

    In the module and in a function alike, as Python binds them: the first
    of each pair takes no language, the second does, so each call drops it.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.other": """
            def axis(ax):
                return ax
            """,
            "pkg.plots": """
            from .other import axis
            from .helpers import axis


            def tick(ax):
                return ax


            def tick(ax, *, language="en"):
                return ax


            def plot_module_import(result, ax, language="en"):
                axis(ax)


            def plot_function_import(result, ax, language="en"):
                from .other import axis as draw
                from .helpers import axis as draw

                draw(ax)


            def plot_definition(result, ax, language="en"):
                tick(ax)
            """,
        },
    )
    assert [(f.caller, f.helper) for f in found] == [
        ("plot_module_import", "pkg.helpers.axis"),
        ("plot_function_import", "pkg.helpers.axis"),
        ("plot_definition", "pkg.plots.tick"),
    ]


def test_a_call_is_checked_against_either_import_of_two_branches(
    tmp_path: pathlib.Path,
) -> None:
    """Of two imports of one name in the branches of a ``try`` or an ``if``, either may stand.

    The ``try`` body stands when its import succeeds and the ``except``
    clause's when it fails; one branch of an ``if`` runs. A call that drops
    the language is found whichever of the two takes it, in either order,
    in the module and in a function.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.other": """
            def axis(ax):
                return ax
            """,
            "pkg.plots": """
            try:
                from .helpers import axis as tried_first
            except ImportError:
                from .other import axis as tried_first
            try:
                from .other import axis as tried_second
            except ImportError:
                from .helpers import axis as tried_second
            if FAST:
                from .helpers import axis as then_first
            else:
                from .other import axis as then_first
            if FAST:
                from .other import axis as then_second
            else:
                from .helpers import axis as then_second


            def plot_tried_first(result, ax, language="en"):
                tried_first(ax)


            def plot_tried_second(result, ax, language="en"):
                tried_second(ax)


            def plot_then_first(result, ax, language="en"):
                then_first(ax)


            def plot_then_second(result, ax, language="en"):
                then_second(ax)


            def plot_in_a_function(result, ax, language="en"):
                try:
                    from .helpers import axis as draw
                except ImportError:
                    from .other import axis as draw
                draw(ax)
            """,
        },
    )
    assert [(f.caller, f.helper) for f in found] == [
        ("plot_tried_first", "pkg.helpers.axis"),
        ("plot_tried_second", "pkg.helpers.axis"),
        ("plot_then_first", "pkg.helpers.axis"),
        ("plot_then_second", "pkg.helpers.axis"),
        ("plot_in_a_function", "pkg.helpers.axis"),
    ]


def test_an_import_a_function_makes_under_global_may_be_what_a_call_reaches(
    tmp_path: pathlib.Path,
) -> None:
    """A function that declares a module name ``global`` and imports it may
    run before a call of the name, so the call may reach that import too.

    The module's names were read from its top alone, so the call was checked
    against the import there, which takes no language, and passed.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.other": """
            def axis(ax):
                return ax
            """,
            "pkg.plots": """
            from .other import axis


            def _localized():
                global axis
                from .helpers import axis


            def plot_thing(result, ax, language="en"):
                axis(ax)
            """,
        },
    )
    assert [(f.caller, f.helper) for f in found] == [
        ("plot_thing", "pkg.helpers.axis"),
    ]


def test_a_later_binding_of_another_kind_ends_what_a_name_stood_for(
    tmp_path: pathlib.Path,
) -> None:
    """A lambda or a call's result bound to the name after an alias, an
    import or a ``def`` of it leaves the name holding what the guard cannot
    read, at the top of a module and in a function, and an alias in the
    function replaces the import before it; a ``functools.partial`` of what
    the name held is that helper still, with its arguments bound.

    Only a ``def``, a ``class``, an import and an alias at the top were read
    as bindings, so the helper the name first stood for stood past the
    lambda, and a call that draws nothing of it was refused for dropping its
    language, or for dropping the language of a helper the alias replaced.
    Read so, a partial ended the helper it wraps, and a call of it that
    drops the language passed.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            import functools

            from .helpers import axis, fmt

            by_lambda = axis
            by_lambda = lambda ax: None

            by_call = axis
            by_call = make()

            from .helpers import axis as imported
            imported = lambda ax: None

            standing = axis

            from .helpers import fmt as wrapped
            wrapped = functools.partial(wrapped)


            def _label(value, language="en"):
                return str(value)


            _label = functools.partial(_label)


            def plot_lambda(result, ax, language="en"):
                by_lambda(ax)


            def plot_call(result, ax, language="en"):
                by_call(ax)


            def plot_imported(result, ax, language="en"):
                imported(ax)


            def plot_standing(result, ax, language="en"):
                standing(ax)


            def plot_local_lambda(result, ax, language="en"):
                from .helpers import axis as draw
                draw = lambda ax: None
                draw(ax)


            def plot_local_alias(result, ax, language="en"):
                from .helpers import axis as draw
                draw = fmt
                draw(ax)


            def plot_wrapped(result, ax, language="en"):
                wrapped(ax)


            def plot_label(result, ax, language="en"):
                _label(ax)


            def plot_local_partial(result, ax, language="en"):
                from .helpers import fmt as draw
                draw = functools.partial(draw)
                draw(ax)
            """
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("plot_label", "pkg.plots._label"),
        ("plot_local_alias", "pkg.helpers.fmt"),
        ("plot_local_partial", "pkg.helpers.fmt"),
        ("plot_standing", "pkg.helpers.axis"),
        ("plot_wrapped", "pkg.helpers.fmt"),
    ]


def test_a_loop_s_target_leaves_what_the_name_stood_for_standing(
    tmp_path: pathlib.Path,
) -> None:
    """A loop binds its target only on a turn it runs, and it may run none,
    so after it the name may still hold the alias or the import before it,
    as after the branches of an ``if``, at the top of a module and in a
    function.

    The target was read as bound on every way past the loop, so it ended
    what the name stood for, and a call that drops its language passed.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis, fmt as draw

            no_turn = axis
            for no_turn in ():
                pass

            a_turn = axis
            for a_turn in [print]:
                pass

            for draw in ():
                pass


            def plot_no_turn(result, ax, language="en"):
                no_turn(ax)


            def plot_a_turn(result, ax, language="en"):
                a_turn(ax)


            def plot_imported(result, ax, language="en"):
                draw(ax)


            def plot_local(result, ax, language="en"):
                from .helpers import fmt as local
                for local in ():
                    pass
                local(ax)
            """
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("plot_a_turn", "pkg.helpers.axis"),
        ("plot_imported", "pkg.helpers.fmt"),
        ("plot_local", "pkg.helpers.fmt"),
        ("plot_no_turn", "pkg.helpers.axis"),
    ]


def test_an_alias_reads_its_value_where_the_assignment_runs(
    tmp_path: pathlib.Path,
) -> None:
    """``draw = axis`` written under ``global`` in a function that imports
    ``axis`` itself reads the import of that function, and ``draw =
    helpers.axis`` reads ``helpers`` as it stands at the assignment, not as
    the module binds it once it has run.

    The value was read at the top of the module once it had run, so the
    first alias reached nothing, and the second reached the ``axis`` of the
    module a later import bound ``helpers`` to.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.other": """
            def axis(ax, language="en"):
                return ax
            """,
            "pkg.plots": """
            from . import helpers


            def _setup():
                global draw
                from .helpers import axis
                draw = axis


            label = helpers.fmt
            from . import other as helpers


            def plot_global(result, ax, language="en"):
                draw(ax)


            def plot_dotted(result, ax, language="en"):
                label(ax)
            """,
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("plot_dotted", "pkg.helpers.fmt"),
        ("plot_global", "pkg.helpers.axis"),
    ]


def test_a_local_alias_reads_its_value_where_the_assignment_runs(
    tmp_path: pathlib.Path,
) -> None:
    """``saved = axis`` in a function, a module body or a class body holds
    what ``axis`` stands for where the assignment runs, so a later binding
    of ``axis`` leaves what a call of ``saved`` reaches as it was, through an
    assignment expression, an annotated assignment, a dotted name and a
    function written in the function alike.

    The value was read as its names stand once the scope has run, so a
    lambda bound to ``axis`` after the alias hid the helper the alias holds,
    and a call of it that drops the language passed, while a helper
    imported under the value's name after the alias was reported for a call
    that never reaches it.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            def plot_saved(result, ax, language="en"):
                from .helpers import axis
                saved = axis
                axis = lambda ax: None
                saved(ax)


            def plot_walrus(result, ax, language="en"):
                from .helpers import axis
                if (saved := axis) is not None:
                    pass
                axis = lambda ax: None
                saved(ax)


            def plot_annotated(result, ax, language="en"):
                from .helpers import axis
                saved: object = axis
                axis = lambda ax: None
                saved(ax)


            def plot_dotted(result, ax, language="en"):
                from . import helpers
                saved = helpers.axis
                helpers = None
                saved(ax)


            def plot_defined(result, ax, language="en"):
                def inner(ax, language="en"):
                    return ax
                saved = inner
                inner = lambda ax: None
                saved(ax)


            def plot_lambda(result, ax, language="en"):
                draw = lambda ax: None
                saved = draw
                from .helpers import axis as draw
                saved(ax)
            """,
            "figures.__init__": "",
            "figures.devices": """
            from pkg.helpers import axis

            saved = axis
            axis = lambda ax: None
            saved(None)


            class _Panel:
                from pkg.helpers import axis as draw
                kept = draw
                draw = None
                kept(None)
            """,
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("<module>", "pkg.helpers.axis"),
        ("_Panel.<class>", "pkg.helpers.axis"),
        ("plot_annotated", "pkg.helpers.axis"),
        ("plot_defined", "pkg.plots.plot_defined.<locals>.inner"),
        ("plot_dotted", "pkg.helpers.axis"),
        ("plot_saved", "pkg.helpers.axis"),
        ("plot_walrus", "pkg.helpers.axis"),
    ]


def test_a_class_body_reads_a_name_it_binds_later_in_its_module(
    tmp_path: pathlib.Path,
) -> None:
    """A class body that reads ``axis`` before any binding it makes of the
    name has run reads the module's ``axis``, as it stands where the class
    statement runs, whatever the body binds ``axis`` to after: in an alias's
    value, a call and an alias of a name the body imports too. Once the
    body has bound the name, it reads the body's binding.

    The body's name was read as the body held it once it had run, so a later
    ``axis = None`` hid the helper and the call that drops the language
    passed.
    """
    found = _dropped(
        tmp_path,
        **{
            "figures.__init__": "",
            "figures.devices": """
            from pkg.helpers import axis


            class _Alias:
                kept = axis
                axis = None
                kept(None)


            class _Call:
                axis(None)
                axis = None


            class _Imported:
                from pkg.helpers import fmt as shown
                shown = axis
                axis = None
                shown(None)


            class _Bound:
                axis = None
                kept = axis
                kept(None)
            """,
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("_Alias.<class>", "pkg.helpers.axis"),
        ("_Call.<class>", "pkg.helpers.axis"),
        ("_Imported.<class>", "pkg.helpers.axis"),
    ]


def test_a_class_body_reads_the_module_s_name_past_a_type_checker_s_binding(
    tmp_path: pathlib.Path,
) -> None:
    """A class body whose only binding of ``axis`` is under ``if
    TYPE_CHECKING:`` never binds it, so a call of ``axis`` there, and an
    alias of it, reach the module's helper, and the calls that drop the
    language are refused.

    The block's binding was taken for one that may have run, the only one of
    the name in the body, so the body's ``axis`` stood for ``None`` and both
    calls passed.
    """
    found = _dropped(
        tmp_path,
        **{
            "figures.__init__": "",
            "figures.devices": """
            from typing import TYPE_CHECKING

            from pkg.helpers import axis


            class _Called:
                if TYPE_CHECKING:
                    axis = None
                axis(None)


            class _Aliased:
                if TYPE_CHECKING:
                    axis = None
                kept = axis
                kept(None)
            """,
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("_Aliased.<class>", "pkg.helpers.axis"),
        ("_Called.<class>", "pkg.helpers.axis"),
    ]


def test_a_partial_reads_its_names_where_it_is_built(
    tmp_path: pathlib.Path,
) -> None:
    """``functools.partial(axis)`` reads ``partial`` and ``axis`` where it is
    built: in an assignment, at the top of a module and in a function, and
    where it is called at once, so a later binding of either name leaves the
    partial wrapping the helper.

    Both names were read as they stood once the scope had run, so a later
    ``partial = None`` made the call no partial at all, and a later lambda
    bound to ``axis`` hid the helper the partial wraps, and the call that
    drops the language passed.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            import functools
            from functools import partial

            from .helpers import axis

            _DRAW = partial(axis)
            partial = None


            def plot_top(result, ax, language="en"):
                _DRAW(ax)


            def plot_local(result, ax, language="en"):
                from functools import partial
                draw = partial(axis)
                partial = None
                draw(ax)


            def plot_at_once(result, ax, language="en"):
                from .helpers import axis
                functools.partial(axis)(ax)
                axis = lambda ax: None
            """
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("plot_at_once", "pkg.helpers.axis"),
        ("plot_local", "pkg.helpers.axis"),
        ("plot_top", "pkg.helpers.axis"),
    ]


def test_a_local_s_class_is_read_where_its_value_is_made(
    tmp_path: pathlib.Path,
) -> None:
    """``panel = Panel()`` holds an instance of the class ``Panel`` names
    where the assignment runs, so a later binding of ``Panel`` leaves a call
    of ``panel.draw`` reaching that class's method.

    The value was read as its names stood once the function had run, so
    ``Panel = None`` after it left the receiver untyped, the method was read
    by its name alone, which two classes write with and without the
    language, and the call that drops it passed.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.panels": """
            class Panel:
                def draw(self, ax, language="en"):
                    return ax


            class Other:
                def draw(self, ax):
                    return ax
            """,
            "pkg.plots": """
            def plot_typed(result, ax, language="en"):
                from .panels import Panel
                panel = Panel()
                Panel = None
                panel.draw(ax)
            """,
        },
    )
    assert [(f.caller, f.helper) for f in found] == [
        ("plot_typed", "pkg.panels.Panel.draw"),
    ]


def test_a_name_an_assignment_binds_at_the_top_reaches_the_helper(
    tmp_path: pathlib.Path,
) -> None:
    """``draw = axis`` at the top of a module, or under ``global`` in a
    function, binds the name to the helper, as an import of it would, and so
    does ``(draw := axis)``, there or in the function that calls it.

    Only a ``def``, a ``class`` or an import bound a module name, so a call
    through such an alias reached nothing and dropped the language unread.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis
            from . import helpers

            draw = axis
            label = helpers.axis


            def _localized():
                global swapped
                swapped = axis


            def plot_top(result, ax, language="en"):
                draw(ax)


            def plot_attribute(result, ax, language="en"):
                label(ax)


            def plot_global(result, ax, language="en"):
                swapped(ax)


            if (walked := axis) is not None:
                pass


            def plot_walrus(result, ax, language="en"):
                walked(ax)


            def plot_local_walrus(result, ax, language="en"):
                if (drawn := axis) is not None:
                    pass
                drawn(ax)
            """,
            # An alias a later ``def`` or import replaces stands for nothing
            # at a call that runs once the module has.
            "pkg.replaced": """
            from .helpers import fmt

            draw = fmt


            def draw(ax):
                return ax


            label = fmt
            from math import floor as label


            def plot_replaced_by_a_def(result, ax, language="en"):
                draw(ax)


            def plot_replaced_by_an_import(result, ax, language="en"):
                label(ax)
            """,
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("plot_attribute", "pkg.helpers.axis"),
        ("plot_global", "pkg.helpers.axis"),
        ("plot_local_walrus", "pkg.helpers.axis"),
        ("plot_top", "pkg.helpers.axis"),
        ("plot_walrus", "pkg.helpers.axis"),
    ]


@pytest.mark.parametrize(
    ("plots", "found"),
    [
        pytest.param(
            """
            from .helpers import axis


            def plot_thing(result, ax, language="en", draw=axis):
                draw(ax)


            def axis(ax):
                return ax
            """,
            [("plot_thing", "pkg.helpers.axis")],
            id="rebound-after-the-def",
        ),
        pytest.param(
            """
            def axis(ax):
                return ax


            def plot_thing(result, ax, language="en", draw=axis):
                draw(ax)


            from .helpers import axis
            """,
            [],
            id="rebound-before-the-def",
        ),
        pytest.param(
            """
            from .helpers import axis, fmt


            def plot_thing(result, ax, language="en", draw=axis):
                draw(ax)


            axis = fmt
            """,
            [("plot_thing", "pkg.helpers.axis")],
            id="aliased-after-the-def",
        ),
        pytest.param(
            """
            from .helpers import axis, fmt

            axis = fmt


            def plot_thing(result, ax, language="en", draw=axis):
                draw(ax)
            """,
            [("plot_thing", "pkg.helpers.fmt")],
            id="aliased-before-the-def",
        ),
        pytest.param(
            """
            from . import helpers


            def plot_thing(result, ax, language="en", draw=helpers.fmt):
                draw(ax)


            from . import other as helpers
            """,
            [("plot_thing", "pkg.helpers.fmt")],
            id="dotted-rebound-after-the-def",
        ),
    ],
)
def test_a_default_is_the_helper_its_name_holds_where_the_def_runs(
    tmp_path: pathlib.Path, plots: str, found: list[tuple[str, str]]
) -> None:
    """A parameter's default runs once, where the ``def`` does, so it is the
    helper the name holds there, not the one the module binds it to by its
    end, the first name of a dotted one alike.
    """
    dropped = _dropped(tmp_path, **{"pkg.plots": plots})
    assert [(f.caller, f.helper) for f in dropped] == found


def test_each_of_two_definitions_of_one_name_is_read(tmp_path: pathlib.Path) -> None:
    """A function defined in each branch of an ``if`` has its calls read in both.

    Either may be the one that runs, and so may one a later ``def`` of its
    name replaces, so neither body is passed over.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            from .helpers import axis

            if FAST:

                def plot_branch(result, ax, language="en"):
                    axis(ax)

            else:

                def plot_branch(result, ax, language="en"):
                    axis(ax, language=language)


            def plot_twice(result, ax, language="en"):
                axis(ax)


            def plot_twice(result, ax, language="en"):
                axis(ax, language=language)
            """,
        },
    )
    assert [(f.line, f.caller) for f in found] == [
        (7, "plot_branch"),
        (16, "plot_twice"),
    ]


def test_an_import_after_a_definition_of_its_name_is_what_a_call_reaches(
    tmp_path: pathlib.Path,
) -> None:
    """A definition and an import of one name stand in the order of the source.

    An import after a ``def`` of its name replaces it, in the module and in
    a function, so a call reaches the import's helper; a ``def`` after an
    import replaces the import the same way.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            def axis(ax):
                return ax


            from .helpers import axis
            from .helpers import axis as replaced


            def replaced(ax):
                return ax


            def plot_module(result, ax, language="en"):
                axis(ax)


            def plot_function(result, ax, language="en"):
                def draw(ax):
                    return ax

                from .helpers import axis as draw

                draw(ax)


            def plot_replaced(result, ax, language="en"):
                replaced(ax)
            """,
        },
    )
    assert [(f.caller, f.helper) for f in found] == [
        ("plot_module", "pkg.helpers.axis"),
        ("plot_function", "pkg.helpers.axis"),
    ]


def test_a_call_reaches_the_bindings_its_name_may_hold_when_it_runs(
    tmp_path: pathlib.Path,
) -> None:
    """A call reads its name where it runs: in its own scope, the binding
    standing there; from a function, every binding of the scope around that
    may stand from the ``def`` on, since the function may be called at once.

    ``TABLE = plot_early(...)`` runs ``plot_early`` while ``axis`` is still
    the helper that takes the language, though a later import replaces it;
    a call written before a second import in its own function reaches the
    first, which takes no language. The names were read as they stand once
    each scope has run, so the first call passed and the second was refused.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.other": """
            def axis(ax):
                return ax
            """,
            "pkg.plots": """
            from .helpers import axis


            def plot_early(result, ax, language="en"):
                axis(ax)


            TABLE = plot_early(None, None)
            from .other import axis


            def plot_before_the_import(result, ax, language="en"):
                from .other import axis as draw

                draw(ax)
                from .helpers import axis as draw
            """,
        },
    )
    assert [(f.caller, f.helper) for f in found] == [
        ("plot_early", "pkg.helpers.axis"),
    ]


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
    shift the slot the language is taken at. A partial bound at the top of the
    module is read as one bound in a function is; it was no binding the guard
    read there, so a call of it passed. A callable pulled out of a mapping
    stays out of reach, which the module docstring says rather than claims.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            import functools

            from .helpers import axis

            _TABLE = {"axis": axis}

            _DRAW = functools.partial(axis)


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


            def via_a_partial_at_the_top(ax, language="en"):
                _DRAW(ax)
            """
        },
    )
    assert [f.caller for f in found] == [
        "via_alias",
        "via_partial",
        "via_a_partial_at_the_top",
    ]


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


def test_a_constructor_declared_for_the_type_checker_is_no_namesake(
    tmp_path: pathlib.Path,
) -> None:
    """A ``TYPE_CHECKING`` ``__init__`` is never defined when the code runs.

    A record declares the constructor a type checker reads inside ``if
    TYPE_CHECKING:``, and one that takes a ``language`` would otherwise make
    ``__init__`` a name only some of whose methods take it.
    """
    tree = _tree(
        tmp_path,
        **{
            "pkg.records": """
            from typing import TYPE_CHECKING


            class Frame:
                language: str = "en"

                if TYPE_CHECKING:

                    def __init__(self, *, language="en"): ...


            class Other:
                def __init__(self, size):
                    self.size = size
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


def test_a_method_a_class_inherits_is_read_from_the_base_its_statement_reads(
    tmp_path: pathlib.Path,
) -> None:
    """A class's base is what its name stands for where the ``class``
    statement reads it, so the ``plot`` a result inherits is that base's,
    not that of a later class of the base's name.

    A base was read as its module stood once it had run, so the call that
    drops the language ``Shown.plot`` takes passed, and the one to
    ``Plain.plot``, which takes none, was refused.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.results": """
            from __future__ import annotations


            class _Late:
                def plot(self, ax=None, *, language="en"):
                    return ax


            class Shown(_Late):
                pass


            class _Late:
                def plot(self, ax=None):
                    return ax


            class _Early:
                def plot(self, ax=None):
                    return ax


            class Plain(_Early):
                pass


            class _Early:
                def plot(self, ax=None, *, language="en"):
                    return ax


            def shown() -> Shown:
                return Shown()


            def plain() -> Plain:
                return Plain()
            """,
            "pkg.plots": """
            from .results import plain, shown


            def figure(ax, language="en"):
                shown().plot(ax)
                plain().plot(ax)
            """,
        },
    )
    assert [(f.line, f.helper) for f in found] == [(6, "pkg.results._Late.plot")]


def test_a_method_a_class_inherits_comes_from_its_method_resolution_order(
    tmp_path: pathlib.Path,
) -> None:
    """A class takes a method from the first class of its method resolution
    order that defines it, and ``super()`` from the first after it:
    ``Shown(_Left, _Right)``, both on ``_Base``, resolves ``_Left, _Right,
    _Base``, so its ``plot`` and the one ``Relayed``'s ``super()`` reaches
    are ``_Right.plot``, which takes the language. An attribute's class is
    read the same way: ``Holder``'s ``result`` is the ``Shown`` that
    ``_HoldsRight`` annotates, not the ``_Plain`` of ``_Holds``.

    The bases were looked up depth first, ``_Left`` then its own base, and
    ``super()`` read the first base alone, so the three calls reached a
    ``plot`` that takes no language, and passed.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.results": """
            from __future__ import annotations


            class _Base:
                def plot(self, ax=None):
                    return ax


            class _Left(_Base):
                pass


            class _Right(_Base):
                def plot(self, ax=None, *, language="en"):
                    return ax


            class Shown(_Left, _Right):
                pass


            class Relayed(_Left, _Right):
                def plot(self, ax=None, *, language="en"):
                    return super().plot(ax)


            class _Plain:
                def plot(self, ax=None):
                    return ax


            class _Holds:
                result: _Plain


            class _HoldsLeft(_Holds):
                pass


            class _HoldsRight(_Holds):
                result: Shown


            class Holder(_HoldsLeft, _HoldsRight):
                pass


            def shown() -> Shown:
                return Shown()


            def holder() -> Holder:
                return Holder()
            """,
            "pkg.plots": """
            from .results import holder, shown


            def figure(ax, language="en"):
                shown().plot(ax)
                holder().result.plot(ax)
            """,
        },
    )
    assert sorted((f.path, f.line, f.caller, f.helper) for f in found) == [
        ("pkg/plots.py", 6, "figure", "pkg.results._Right.plot"),
        ("pkg/plots.py", 7, "figure", "pkg.results._Right.plot"),
        ("pkg/results.py", 25, "Relayed.plot", "pkg.results._Right.plot"),
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


def test_a_keyword_reaches_no_positional_only_language(
    tmp_path: pathlib.Path,
) -> None:
    """A keyword, or a ``**`` mapping, that names a positional-only language
    goes to the helper's ``**kw``, and the helper draws in its default.

    ``language=language`` was read as forwarding whatever the helper's
    parameter was, so both calls passed; the language in its place
    forwards it.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.plots": """
            def _label(value, language="en", /, **kw):
                return value


            def by_keyword(result, ax, language="en"):
                _label(ax, language=language)


            def by_mapping(result, ax, language="en"):
                _label(ax, **{"language": language})


            def by_place(result, ax, language="en"):
                _label(ax, language)
            """
        },
    )
    assert sorted(f.caller for f in found) == ["by_keyword", "by_mapping"]


def test_a_call_of_a_class_runs_the_init_its_order_gives(
    tmp_path: pathlib.Path,
) -> None:
    """A call of a class runs the ``__init__`` of the first class of its
    method resolution order that has one of its own: ``@dataclass`` writes
    ``Rec`` one, whichever spelling of the decorator it is, so a call of
    ``Rec`` runs no ``_Labelled.__init__`` and has no language to hand it.
    ``Plain``, and a dataclass told ``init=False``, run the one
    ``_Labelled`` writes, and drop the language it takes.

    The ``__init__`` was looked up by name through the bases, so ``Rec``
    was read as calling ``_Labelled.__init__`` and refused for a language
    its constructor does not take.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.records": """
            import dataclasses as dc
            from dataclasses import dataclass


            class _Labelled:
                def __init__(self, value, language="en"):
                    self.value = value


            @dataclass(frozen=True)
            class Rec(_Labelled):
                value: float = 0.0


            @dc.dataclass(frozen=True)
            class Dotted(_Labelled):
                value: float = 0.0


            @dc.dataclass(frozen=True, init=False)
            class Unwritten(_Labelled):
                value: float = 0.0


            class Plain(_Labelled):
                pass


            def plot_rec(ax, *, language="en"):
                return Rec(1.0)


            def plot_dotted(ax, *, language="en"):
                return Dotted(1.0)


            def plot_unwritten(ax, *, language="en"):
                return Unwritten(1.0)


            def plot_plain(ax, *, language="en"):
                return Plain(1.0)
            """
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("plot_plain", "pkg.records._Labelled.__init__"),
        ("plot_unwritten", "pkg.records._Labelled.__init__"),
    ]


def test_super_init_and_an_init_by_name_run_the_init_the_order_gives(
    tmp_path: pathlib.Path,
) -> None:
    """``super().__init__(...)`` and ``Rec.__init__(obj, ...)`` run the
    ``__init__`` of the first class of the order that has one of its own, as
    a call of the class does: past ``Rec``, which ``@dataclass`` writes one,
    no ``_Labelled.__init__`` runs, so ``Sub`` and ``plot_via_init`` have no
    language to hand it. Over ``Plain``, which writes none, both reach the
    one ``_Labelled`` writes and drop the language it takes.

    The ``__init__`` was looked up by name through the bases, so both were
    refused for a helper that never runs.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.records": """
            from dataclasses import dataclass


            class _Labelled:
                def __init__(self, value, language="en"):
                    self.value = value


            @dataclass
            class Rec(_Labelled):
                value: float = 0.0


            class Plain(_Labelled):
                pass


            class Sub(Rec):
                def __init__(self, value, *, language="en"):
                    super().__init__(value)


            class PlainSub(Plain):
                def __init__(self, value, *, language="en"):
                    super().__init__(value)


            def plot_via_init(ax, *, language="en"):
                r = Rec.__new__(Rec)
                Rec.__init__(r, 1.0)


            def plot_plain_via_init(ax, *, language="en"):
                r = Plain.__new__(Plain)
                Plain.__init__(r, 1.0)
            """
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("PlainSub.__init__", "pkg.records._Labelled.__init__"),
        ("plot_plain_via_init", "pkg.records._Labelled.__init__"),
    ]


def test_super_of_a_named_class_and_a_class_method_through_its_class(
    tmp_path: pathlib.Path,
) -> None:
    """``super(_Plain, self).plot(ax)`` looks the method up past ``_Plain``
    in the order of the class it is written in: in ``PastPlain(_Plain,
    _Labelled)`` it reaches ``_Labelled.plot``, which takes the language and
    is not handed it; in ``PastLabelled(_Labelled, _Plain)``,
    ``super(_Labelled, self)`` reaches ``_Plain.plot``, which takes none. A
    class method called through its class, ``_Labelled.build(ax,
    language)``, is bound to the class, so the language it is handed second
    fills its ``language``.

    ``super(Base, self)`` was read as ``super()``, past the class the method
    is written in, so the first call passed and the second was refused; and
    a method called through its class was read as taking the class's first
    argument in its first parameter, ``cls`` for a class method, so the
    language landed one place short and the call was refused.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.records": """
            class _Plain:
                def plot(self, ax=None):
                    return ax


            class _Labelled:
                def plot(self, ax=None, *, language="en"):
                    return ax

                @classmethod
                def build(cls, ax=None, language="en"):
                    return ax


            class PastPlain(_Plain, _Labelled):
                def plot(self, ax=None, *, language="en"):
                    return super(_Plain, self).plot(ax)


            class PastLabelled(_Labelled, _Plain):
                def plot(self, ax=None, *, language="en"):
                    return super(_Labelled, self).plot(ax)


            def through_class(ax, language="en"):
                return _Labelled.build(ax, language)


            def through_class_without_language(ax, language="en"):
                return _Labelled.build(ax)
            """
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("PastPlain.plot", "pkg.records._Labelled.plot"),
        ("through_class_without_language", "pkg.records._Labelled.build"),
    ]


def test_an_init_a_record_binds_or_writes_is_the_one_a_call_runs(
    tmp_path: pathlib.Path,
) -> None:
    """``@dataclass`` writes no ``__init__`` its class body binds, so
    ``__init__ = _Labelled.__init__`` is the one ``Assigned(1.0)`` runs,
    and it drops the language; a ``dataclass`` the module rebinds to a
    decorator of its own writes none, so ``Rebound(1.0)`` runs
    ``_Labelled.__init__`` too. The ``__init__`` ``@dataclass`` writes
    takes the record's fields, so ``Spoken(1.0)`` drops the language its
    ``language`` field takes, and ``Spoken(1.0, language)`` and
    ``KeywordOnly(1.0, language=language)`` hand it on.

    A record's ``__init__`` was read as generated whenever an import named
    the decorator ``dataclass``, so a body that binds one and a decorator
    rebound to write none were passed over, and a generated one was read as
    taking no language, so a call that drops it passed.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.labelled": """
            class _Labelled:
                def __init__(self, value, language="en"):
                    self.value = value
            """,
            "pkg.records": """
            from dataclasses import KW_ONLY, dataclass

            from .labelled import _Labelled


            @dataclass
            class Assigned(_Labelled):
                value: float = 0.0
                __init__ = _Labelled.__init__


            @dataclass
            class Spoken:
                value: float = 0.0
                language: str = "en"


            @dataclass
            class KeywordOnly:
                value: float = 0.0
                _: KW_ONLY
                language: str = "en"


            def plot_assigned(ax, *, language="en"):
                return Assigned(1.0)


            def plot_spoken(ax, *, language="en"):
                return Spoken(1.0)


            def plot_spoken_on(ax, *, language="en"):
                return Spoken(1.0, language)


            def plot_keyword_only(ax, *, language="en"):
                return KeywordOnly(1.0, language=language)
            """,
            "pkg.rebound": """
            from dataclasses import dataclass

            from .labelled import _Labelled


            def dataclass(cls):
                return cls


            @dataclass
            class Rebound(_Labelled):
                value: float = 0.0


            def plot_rebound(ax, *, language="en"):
                return Rebound(1.0)
            """,
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("plot_assigned", "pkg.labelled._Labelled.__init__"),
        ("plot_rebound", "pkg.labelled._Labelled.__init__"),
        ("plot_spoken", "pkg.records.Spoken.__init__"),
    ]


#: A base whose ``__init__`` takes the language, which a class over it runs
#: when no ``@dataclass`` writes it one.
_LABELLED = """
class _Labelled:
    def __init__(self, value, language="en"):
        self.value = value
"""


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """
            from dataclasses import dataclass

            from .labelled import _Labelled


            def _keep(cls):
                return cls


            def plot(ax, *, language="en"):
                dataclass = _keep

                @dataclass
                class Sub(_Labelled):
                    value: float = 0.0

                return Sub(1.0)
            """,
            [("plot", "pkg.labelled._Labelled.__init__")],
        ),
        (
            """
            from dataclasses import dataclass

            from .labelled import _Labelled


            def plot(ax, *, language="en"):
                dataclass = lambda cls: cls

                @dataclass
                class Sub(_Labelled):
                    value: float = 0.0

                return Sub(1.0)
            """,
            [("plot", "pkg.labelled._Labelled.__init__")],
        ),
        (
            """
            from dataclasses import dataclass

            from .labelled import _Labelled


            def plot(ax, *, language="en"):
                def dataclass(cls):
                    return cls

                def build(language):
                    @dataclass
                    class Sub(_Labelled):
                        value: float = 0.0

                    return Sub(1.0)

                return build(language)
            """,
            [("plot.<locals>.build", "pkg.labelled._Labelled.__init__")],
        ),
        (
            """
            try:
                from dataclasses import dataclass
            except ImportError:
                def dataclass(cls):
                    return cls


            class _Plain:
                def __init__(self, value):
                    self.value = value


            @dataclass
            class Sub(_Plain):
                value: float = 0.0
                language: str = "en"


            def plot(ax, *, language="en"):
                return Sub(1.0)
            """,
            [("plot", "pkg.mod.Sub.__init__")],
        ),
        (
            """
            from dataclasses import dataclass


            def plot(ax, *, language="en"):
                @dataclass
                class Sub:
                    value: float = 0.0
                    language: str = "en"

                return Sub(1.0)
            """,
            [("plot", "pkg.mod.plot.<locals>.Sub.__init__")],
        ),
    ],
    ids=["assigned-here", "lambda-here", "defined-around", "either", "imported"],
)
def test_a_decorator_is_read_through_the_bindings_that_stand_where_the_class_runs(
    tmp_path: pathlib.Path, source: str, expected: list[tuple[str, str]]
) -> None:
    """The decorator of a class is what its name holds where the ``class``
    statement runs: in the function that writes the class, ``dataclass =
    _keep`` and ``dataclass = lambda cls: cls`` replace the import, as a
    ``def`` of it in a function around does, so ``Sub(1.0)`` runs
    ``_Labelled.__init__``, which takes the language; with an import and a
    fallback that may each stand, either constructor may run, and the
    generated one takes the language its field holds. With the import
    alone, the generated one runs.

    A function's assignment of the name and a function around were passed
    over for the module's import, so the call was read as running the
    generated ``__init__``, which takes no language, and passed; and of two
    bindings that may stand, only the fallback was read, so a call that
    drops the language the generated one takes passed.
    """
    found = _dropped(tmp_path, **{"pkg.labelled": _LABELLED, "pkg.mod": source})
    assert sorted((f.caller, f.helper) for f in found) == expected


#: A class over :data:`_LABELLED` with a ``language`` field, whose decorator
#: ``IMPORT`` binds: a call of it runs the ``__init__`` ``@dataclass`` writes
#: when the decorator is ``dataclasses``' own, ``_Labelled.__init__`` when
#: it is not.
_TAKEN_FROM = """
IMPORT

from .labelled import _Labelled


@dataclass
class Sub(_Labelled):
    value: float = 0.0
    language: str = "en"


def plot(ax, *, language="en"):
    return Sub(1.0)
"""


@pytest.mark.parametrize(
    ("imported", "exporting", "expected"),
    [
        ("from .dc import dataclass", "from dataclasses import dataclass", "Sub"),
        ("from pkg.dc import dataclass", "from dataclasses import dataclass", "Sub"),
        (
            "from . import dc\n\ndataclass = dc.dataclass",
            "import dataclasses\n\ndataclass = dataclasses.dataclass",
            "Sub",
        ),
        (
            "import functools\n\nfrom .dc import dataclass as _record\n\n"
            "dataclass = functools.partial(_record, eq=False)",
            "from dataclasses import dataclass",
            "Sub",
        ),
        (
            "from .dc import dataclass",
            "def dataclass(cls):\n    return cls",
            "_Labelled",
        ),
    ],
    ids=["relative", "absolute", "alias", "partial", "own"],
)
def test_a_decorator_a_module_of_the_package_re_exports_is_read_through_it(
    tmp_path: pathlib.Path, imported: str, exporting: str, expected: str
) -> None:
    """``@dataclass`` taken from a module of the package is what that module
    took, and an alias of it is what it names: ``dataclasses``' own,
    through a relative import or an absolute one, an alias in either module
    or a ``functools.partial`` of it, so ``Sub(1.0)`` runs the ``__init__``
    it writes, which takes the record's ``language`` field. A module that
    writes a ``dataclass`` of its own leaves ``Sub`` to
    ``_Labelled.__init__``, which takes it too. Either drops the language.

    An import was read as it is written and every assignment as replacing
    the decorator, so the call was read as running ``_Labelled.__init__``
    whatever the decorator was.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.labelled": _LABELLED,
            "pkg.dc": exporting + "\n",
            "pkg.mod": _TAKEN_FROM.replace("IMPORT", imported),
        },
    )
    helper = (
        "pkg.mod.Sub.__init__"
        if expected == "Sub"
        else "pkg.labelled._Labelled.__init__"
    )
    assert sorted((f.caller, f.helper) for f in found) == [("plot", helper)]


@pytest.mark.parametrize(
    ("imported", "expected"),
    [
        (
            "import dataclasses\nimport functools\n\n"
            "dataclass = functools.partial(dataclasses.dataclass, init=False)",
            ["_Labelled"],
        ),
        ("import dataclasses\n\ndataclass = dataclasses.dataclass(eq=False)", ["Sub"]),
        (
            "import dataclasses\nimport os\n\ndataclass = (\n"
            "    dataclasses.dataclass if os.environ.get('RECORDS') else (lambda cls: cls)\n"
            ")",
            ["_Labelled", "Sub"],
        ),
        (
            "import dataclasses\nimport functools\n\n"
            "dataclass = functools.partial(dataclasses.dataclass, eq=False)",
            ["Sub"],
        ),
    ],
    ids=["partial-init-off", "called", "conditional", "partial"],
)
def test_what_an_alias_of_the_decorator_presets_is_read_with_it(
    tmp_path: pathlib.Path, imported: str, expected: list[str]
) -> None:
    """An alias of ``@dataclass`` is read with what it presets: a
    ``functools.partial`` that presets ``init=False`` writes ``Sub`` no
    ``__init__``, so ``Sub(1.0)`` runs ``_Labelled.__init__``; a call of the
    decorator with keywords alone is the decorator, so the call runs the
    ``__init__`` it writes; and a conditional expression that gives it or
    another may run either. Each drops the language one of them takes.

    What a partial presets was not read, and a call of the decorator or a
    conditional expression was read as another decorator, so the call was
    read as running the generated ``__init__``, or ``_Labelled.__init__``
    alone.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.labelled": _LABELLED,
            "pkg.mod": _TAKEN_FROM.replace("IMPORT", imported),
        },
    )
    helpers = {
        "Sub": "pkg.mod.Sub.__init__",
        "_Labelled": "pkg.labelled._Labelled.__init__",
    }
    assert sorted((f.caller, f.helper) for f in found) == sorted(
        ("plot", helpers[name]) for name in expected
    )


@pytest.mark.parametrize(
    ("option", "expected"),
    [
        ("NO_INIT = False", [("draw", "pkg.records._Labelled.__init__")]),
        ("NO_INIT = True", []),
        (
            "NO_INIT = sys.flags.optimize > 9",
            [("draw", "pkg.records._Labelled.__init__")],
        ),
    ],
    ids=["false", "true", "unread"],
)
def test_an_init_option_is_read_through_the_name_that_holds_it(
    tmp_path: pathlib.Path, option: str, expected: list[tuple[str, str]]
) -> None:
    """``@dataclass(init=NO_INIT)`` with ``NO_INIT = False`` writes no
    ``__init__``, so ``Spoken(1.0)`` runs ``_Labelled.__init__``, which
    takes the language and is handed none; with ``NO_INIT = True`` the
    generated one runs, and it takes no language. A value the guard cannot
    read may be either, so the call is read through both constructors, and
    ``_Labelled.__init__`` is handed no language.

    A name was read as no value, ``init=True``, so the call that drops the
    language passed; and so was a value the guard cannot read.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.records": """
            import sys
            from dataclasses import dataclass

            OPTION


            class _Labelled:
                def __init__(self, value, language="en"):
                    self.language = language


            @dataclass(init=NO_INIT)
            class Spoken(_Labelled):
                value: float = 0.0


            def draw(language="en"):
                return Spoken(1.0)
            """.replace("OPTION", option)
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == expected


def test_a_class_method_an_alias_holds_and_super_of_another_instance(
    tmp_path: pathlib.Path,
) -> None:
    """An alias of a class method, ``build = Maker.build``, holds it bound to
    its class, so ``build(ax, language)`` hands the language to its
    ``language`` and ``build(ax)`` drops it. ``super(Base, other)`` reads
    the order of the class of ``other``, past ``Base``: in
    ``Receiver(Base, Tail)`` it reaches ``Tail.plot``, which takes the
    language, from a method of ``Caller(Tail)``, whose own order holds no
    ``Base``.

    An alias was read as taking the class's first argument in ``cls``, so
    the language landed one place short and both calls were refused; and
    ``super(Base, other)`` read the order of the class the method is
    written in, which holds no ``Base``, so the call reached nothing and
    passed.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.records": """
            class Maker:
                @classmethod
                def build(cls, ax=None, language="en"):
                    return ax


            def through_alias(ax, language="en"):
                build = Maker.build
                return build(ax, language)


            def through_alias_without_language(ax, language="en"):
                build = Maker.build
                return build(ax)


            class Base:
                def plot(self, ax=None):
                    return ax


            class Tail:
                def plot(self, ax=None, *, language="en"):
                    return ax


            class Receiver(Base, Tail):
                pass


            class Caller(Tail):
                def plot(self, ax=None, *, language="en"):
                    other = Receiver()
                    return super(Base, other).plot(ax)
            """
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("Caller.plot", "pkg.records.Tail.plot"),
        ("through_alias_without_language", "pkg.records.Maker.build"),
    ]


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


@pytest.mark.whole_tree
def test_the_tree_passes_its_language_on() -> None:
    """The corpus itself, which is what the gate protects."""
    assert clf.main([]) == 0


def test_a_call_on_self_reaches_the_method_the_class_of_the_instance_holds(
    tmp_path: pathlib.Path,
) -> None:
    """``self._label(ax)`` in ``_Base.draw`` runs what the class of the
    instance holds: on a ``Public``, ``Public._label``, which takes the
    language, so the call drops it; on a ``_Base``, ``_Base._label``, which
    takes none.

    A call on ``self`` reached only the method the order of the class it is
    written in finds, ``_Base._label``, so the call passed.
    """
    found = _dropped(
        tmp_path,
        **{
            "pkg.records": """
            class _Base:
                def draw(self, ax, language="en"):
                    return self._label(ax)

                def _label(self, ax):
                    return ax


            class Public(_Base):
                def _label(self, ax, language="en"):
                    return language


            class Other:
                def _label(self, ax, language="en"):
                    return language
            """
        },
    )
    assert sorted((f.caller, f.helper) for f in found) == [
        ("_Base.draw", "pkg.records.Public._label")
    ]
