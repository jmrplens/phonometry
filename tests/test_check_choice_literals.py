#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate that holds every fixed choice of the public API to a ``Literal``.

``scripts/check_choice_literals.py`` reads each public string parameter and
field and calls it a closed choice when the function itself treats it as one:
it hands it to a shared validator, compares it with a set of strings, looks it
up by key, documents two quoted options or more, or passes it on untouched to
a function that does one of those. A closed choice typed ``str`` fails, and a
string that is open by its nature goes in ``OPEN`` with its reason. These
tests pin each way a choice is recognised, the hatch, and the package itself,
and that every vocabulary typed ``Literal`` offers exactly what its table
holds.
"""

from __future__ import annotations

import ast
import contextlib
import dataclasses
import enum
import importlib.util
import inspect
import pathlib
import sys
import textwrap
import typing
import warnings
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_choice_literals as ccl
import guard_caches
import pytest

from phonometry import building, emission, environment, io, vibration
from phonometry._internal.frozen import OwnsArrays
from phonometry._internal.validation import require_choice
from phonometry.filters.weighting import time_weighting

#: The tests that read the whole package share what the guard keeps of it, so
#: they run on one worker (rule T19), and the guard lets it go after them.
pytestmark = pytest.mark.xdist_group("choice-literals")


@pytest.fixture(scope="module", autouse=True)
def _forget_the_guard() -> Iterator[None]:
    """Let go of what the guard read once this module's tests are done."""
    yield
    guard_caches.forget(ccl)


def _tree(function: object) -> ast.AST:
    return ast.parse(textwrap.dedent(inspect.getsource(function)))  # type: ignore[arg-type]


def _compared(mode: str) -> str:
    if mode not in ("fast", "slow"):
        raise ValueError(mode)
    return mode


def _equal(mode: str) -> bool:
    return mode == "fast"


def _validated(mode: str) -> str:
    return require_choice(mode, "mode", ("fast", "slow"))


def _passed_on(x: list[float], mode: str) -> object:
    return time_weighting(x, 48000, mode=mode)  # type: ignore[arg-type]


def _free(label: str) -> str:
    return label.upper()


#: A table a caller hands a helper beside the text it checks.
_SIDE_TABLE = {"left": 1, "right": 2}


class _Colour(enum.Enum):
    RED = "red"
    BLUE = "blue"


def _normalised(mode: str) -> bool:
    return str(mode).strip().lower() in ("fast", "slow")


def _resolve(text: str) -> str:
    return text


def _derived(mode: str) -> int:
    key = _resolve(mode)
    if key not in ("fast", "slow"):
        raise ValueError(key)
    return 0


def _check_against(name: str, table: dict[str, int]) -> int:
    key = name.lower()
    if key not in table:
        raise ValueError(name)
    return table[key]


def _hands_a_table(side: str) -> int:
    return _check_against(side, _SIDE_TABLE)


def _spreads(x: list[float], mode: str) -> object:
    options = {"mode": mode}
    return time_weighting(x, 48000, **options)  # type: ignore[arg-type]


def _imports_inside(x: list[float], mode: str) -> object:
    from phonometry.filters.weighting import time_weighting as weigh

    return weigh(x, 48000, mode=mode)  # type: ignore[arg-type]


def _documented(mode: str) -> None:
    """Take a mode.

    :param mode: ``"fast"`` or ``"slow"``.
    """


#: The sides a collection of strings is checked against, below.
_SIDES = ("left", "right", "top", "bottom")


def _set_difference(sides: Sequence[str]) -> None:
    unknown = set(sides) - set(_SIDES)
    if unknown:
        raise ValueError(sorted(unknown))


def _subset(sides: Sequence[str]) -> bool:
    return set(sides) <= set(_SIDES)


def _issubset(sides: Sequence[str]) -> bool:
    return set(sides).issubset(_SIDES)


def _issuperset(sides: Sequence[str]) -> bool:
    return set(_SIDES).issuperset(sides)


def _one_or_several(sides: str | Iterable[str]) -> tuple[str, ...]:
    named = (sides,) if isinstance(sides, str) else tuple(sides)
    if set(named) - set(_SIDES):
        raise ValueError(named)
    return named


def _once_each(sides: Sequence[str]) -> tuple[str, ...]:
    rows = tuple(dict.fromkeys(sides))
    for side in rows:
        if side not in _SIDES:
            raise ValueError(side)
    return rows


def _item_by_item(levels: dict[str, float]) -> None:
    for side, level in levels.items():
        if side not in _SIDES or level < 0.0:
            raise ValueError(side)


def _held_table(sides: Sequence[str]) -> None:
    table = _SIDES
    if set(sides) - set(table):
        raise ValueError(sides)


def _picked_table(sides: Sequence[str], *, strict: bool) -> None:
    table = _SIDES if strict else ("top", "bottom")
    if set(sides) - set(table):
        raise ValueError(sides)


#: A table of tables, one picked by the caller's kind.
_TABLES = {"plan": _SIDES, "section": ("up", "down")}


def _one_of_the_tables(levels: dict[str, float], kind: str) -> None:
    table = _TABLES[kind]
    unknown = [key for key in levels if key not in table]
    if unknown:
        raise ValueError(unknown)


#: A frozen table the source builds with code, whose keys only the running
#: module holds.
_BUILT = MappingProxyType(dict.fromkeys(name.lower() for name in ("North", "South")))


def _built_table(sides: Sequence[str]) -> None:
    if set(sides) - set(_BUILT):
        raise ValueError(sides)


def _a_set_copy(limits: Mapping[str, float]) -> None:
    given = {str(direction) for direction in limits}
    if given - set(_SIDES):
        raise ValueError(sorted(given))


def _a_list_copy(sides: Sequence[str]) -> None:
    names = [side.strip().lower() for side in sides]
    if set(names) - set(_SIDES):
        raise ValueError(names)


#: An alias that hides a collection of any strings behind a name.
_FreeSides = Iterable[str]

#: An alias of the options, which stays a closed choice once spelled out.
_Side = Literal["left", "right"]


def _one_looked_for(sides: Sequence[str]) -> bool:
    return "top" in sides


def _a_label(labels: Sequence[str]) -> bool:
    return any(label == "" for label in labels)


def _check_travel(travel: str) -> None:
    if travel not in ("up", "down"):
        raise ValueError(travel)


@dataclass(frozen=True)
class _Wave(OwnsArrays):
    """A record whose field a helper checks, its __post_init__ wrapped."""

    travel: str

    def __post_init__(self) -> None:
        _check_travel(self.travel)


@dataclass(frozen=True)
class _Source:
    """A record whose field the module checks where it is used."""

    direction: str


def _place(source: _Source) -> int:
    if source.direction not in ("down", "up"):
        raise ValueError(source.direction)
    return 0


class _Elsewhere:
    """Another class's attribute of the same name is not the record's field."""

    label = "x"

    def title(self) -> bool:
        return self.label == "probes"


@dataclass(frozen=True)
class _Labelled:
    label: str


def test_a_collection_of_strings_is_read_as_a_choice() -> None:
    """A collection of ``str``, alone or in a union, or a mapping keyed by
    ``str``, takes the choice one string at a time; a typed item does not.
    """
    for annotation in (
        "Sequence[str]",
        "str | Iterable[str] | None",
        "tuple[str, ...]",
        "frozenset[str]",
        "collections.abc.Sequence[str]",
        "Mapping[str, float] | None",
        "dict[str, tuple[NDArray[np.float64], NDArray[np.float64]]]",
    ):
        assert ccl.takes_any_strings(annotation), annotation
    for annotation in (
        "tuple[str, str]",
        "Sequence[Side]",
        "Mapping[int, str]",
        "list[float]",
        "str",
    ):
        assert not ccl.takes_any_strings(annotation), annotation


def test_a_literal_inside_a_collection_is_a_literal() -> None:
    """Handing a collection to a parameter of Literal items is a choice."""
    assert ccl._is_literal("Sequence[Literal['a', 'b']]")
    assert ccl._is_literal("Mapping[Literal['a'], float] | None")
    assert not ccl._is_literal("Sequence[str]")


def _classified(values: str | list[float]) -> None:
    found = _misread_member(values)
    if found not in ("bytearray", "nesting"):
        return
    msg = "text"
    raise TypeError(msg)


def _misread_member(value: object) -> str | None:
    return None if value else "bytearray"


def test_a_helper_that_classifies_the_value_is_no_cleaned_up_copy_of_it() -> None:
    """What ``_misread_member`` answers is a word of its own about the value,
    not the value: comparing it with a text compares no option. A private
    helper that hands the value back cleaned up is still followed.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    assert (
        ccl.code_evidence(
            _tree(_classified),
            ccl._the_name("values"),
            constants,
            module_name=__name__,
        )
        == []
    )
    assert ccl.code_evidence(
        _tree(_derived), ccl._the_name("mode"), constants, module_name=__name__
    )


def test_a_set_difference_or_subset_against_strings_is_a_choice() -> None:
    """What is left once the options are taken away is refused, or the
    collection is tested as a subset of them: either way its strings are a
    closed set.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    for function in (_set_difference, _subset, _issubset, _issuperset):
        found = ccl.code_evidence(
            _tree(function),
            ccl._the_name("sides"),
            constants,
            collection=True,
            module_name=__name__,
        )
        assert found, function.__name__


def test_the_strings_held_in_a_local_are_followed() -> None:
    """``(x,)``, ``tuple(x)`` and ``dict.fromkeys(x)`` hold the caller's strings."""
    constants = ccl._module_constants(sys.modules[__name__])
    for function in (_one_or_several, _once_each):
        found = ccl.code_evidence(
            _tree(function),
            ccl._the_name("sides"),
            constants,
            collection=True,
            module_name=__name__,
        )
        assert found, function.__name__


def test_a_table_held_in_a_local_is_the_table_written_in_place() -> None:
    """``table = _SIDES``, a table picked by a conditional expression and one
    table of a table of tables are the sets of strings they hold.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    for function, name in (
        (_held_table, "sides"),
        (_picked_table, "sides"),
        (_one_of_the_tables, "levels"),
    ):
        found = ccl.code_evidence(
            _tree(function),
            ccl._the_name(name),
            constants,
            collection=True,
            module_name=__name__,
        )
        assert found, function.__name__


def test_a_table_of_tables_holds_the_keys_of_all_its_tables() -> None:
    """Whichever table is picked, a key of any of them is an option."""
    constants = ccl._module_constants(sys.modules[__name__])
    picked = ast.parse("_TABLES[kind]", mode="eval").body
    assert set(ccl.strings_of(picked, constants)) == {*_SIDES, "up", "down"}
    # A table of numbers is no set of strings.
    assert (
        ccl.strings_of(ast.parse("_SIDE_TABLE[k]", mode="eval").body, constants) == ()
    )


def test_a_frozen_table_built_with_code_is_read_off_the_module() -> None:
    """The keys of a table the source builds when it runs come from the module."""
    constants = ccl._module_constants(sys.modules[__name__])
    assert set(ccl.strings_of(ast.Name(id="_BUILT"), constants)) == {"north", "south"}
    found = ccl.code_evidence(
        _tree(_built_table),
        ccl._the_name("sides"),
        constants,
        collection=True,
        module_name=__name__,
    )
    assert found == ["a set difference with a set of strings"]


def test_a_comprehension_that_copies_the_items_is_followed() -> None:
    """``{str(d) for d in limits}`` and ``[s.lower() for s in sides]`` hold the
    caller's strings, so a set difference on the copy closes the original.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    for function, name in ((_a_set_copy, "limits"), (_a_list_copy, "sides")):
        found = ccl.code_evidence(
            _tree(function),
            ccl._the_name(name),
            constants,
            collection=True,
            module_name=__name__,
        )
        assert "a set difference with a set of strings" in found, function.__name__


def test_an_alias_is_read_as_what_it_stands_for() -> None:
    """A collection of strings behind an alias takes any strings; an alias of
    the options stays a ``Literal``, and a quoted option is never a name.
    """
    read = ccl.expanded("_FreeSides | None", __name__)
    assert read == "Iterable[str] | None"
    assert ccl.takes_any_strings(read)
    assert ccl._is_literal(ccl.expanded("Sequence[_Side]", __name__))
    assert ccl.expanded("Literal['_FreeSides']", __name__) == "Literal['_FreeSides']"


def test_an_imported_alias_is_read_where_it_is_written(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``NamesOrNone = _Names | None`` imported alone names the ``_Names`` of
    its own module, which the importing module does not hold; read where it is
    written, it takes any strings all the same.
    """
    sources = {
        "_alias_home": (
            "from collections.abc import Iterable\n\n"
            "_Names = Iterable[str]\n"
            "NamesOrNone = _Names | None\n"
        ),
        "_alias_user": (
            "from ._alias_home import NamesOrNone\n\n\n"
            "def pick(names: NamesOrNone = None) -> None:\n"
            "    del names\n"
        ),
    }
    for stem, text in sources.items():
        path = tmp_path / f"{stem}.py"
        path.write_text(text, encoding="utf-8")
        name = f"phonometry.{stem}"
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
    read = ccl.expanded("NamesOrNone", "phonometry._alias_user")
    assert read == "Iterable[str] | None"
    assert ccl.takes_any_strings(read)


def test_the_later_of_two_imports_of_one_name_is_the_one_read(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Of two imports of one name, a module holds the later, as Python leaves it.

    ``from ._later_first import KINDS, Names`` then ``from ._later_second
    import KINDS, Names`` makes the importing module's ``KINDS`` the second
    module's table and its ``Names`` the second module's alias, a closed
    choice where the first module's takes any strings.
    """
    sources = {
        "_later_first": (
            "from collections.abc import Iterable\n\n"
            "KINDS = ('a', 'b')\n"
            "Names = Iterable[str]\n"
        ),
        "_later_second": (
            "from typing import Literal\n\n"
            "KINDS = ('c', 'd')\n"
            "Names = Literal['c', 'd']\n"
        ),
        "_later_user": (
            "from ._later_first import KINDS, Names\n"
            "from ._later_second import KINDS, Names\n"
        ),
    }
    for stem, text in sources.items():
        path = tmp_path / f"{stem}.py"
        path.write_text(text, encoding="utf-8")
        name = f"phonometry.{stem}"
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
    constants = ccl._constants_of("phonometry._later_user")
    assert set(ccl.strings_of(ast.Name(id="KINDS"), constants)) == {"c", "d"}
    assert ccl.expanded("Names", "phonometry._later_user") == "Literal['c', 'd']"


def _plant_modules(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, sources: dict[str, str]
) -> None:
    """Write and import each of *sources* as ``phonometry.<stem>``, in order."""
    for stem, text in sources.items():
        path = tmp_path / f"{stem}.py"
        path.write_text(textwrap.dedent(text), encoding="utf-8")
        name = f"phonometry.{stem}"
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)


#: Two modules that bind ``KINDS`` and ``Names`` to two different choices.
_TWO_CHOICES = {
    "_branch_first": """
        from collections.abc import Iterable

        KINDS = ('a', 'b')
        Names = Iterable[str]
        """,
    "_branch_second": """
        from typing import Literal

        KINDS = ('c', 'd')
        Names = Literal['c', 'd']
        """,
}


@pytest.mark.parametrize(
    ("stem", "user"),
    [
        (
            "_branch_try_second",
            """
            try:
                from ._branch_second import KINDS, Names
            except ImportError:
                from ._branch_first import KINDS, Names
            """,
        ),
        (
            "_branch_try_first",
            """
            try:
                from ._branch_first import KINDS, Names
            except ImportError:
                from ._branch_second import KINDS, Names
            """,
        ),
        (
            "_branch_if_second",
            """
            import sys

            if sys.version_info >= (3,):
                from ._branch_second import KINDS, Names
            else:
                from ._branch_first import KINDS, Names
            """,
        ),
        (
            "_branch_if_first",
            """
            import sys

            if sys.version_info >= (3,):
                from ._branch_first import KINDS, Names
            else:
                from ._branch_second import KINDS, Names
            """,
        ),
        (
            "_branch_global_in_a_function",
            """
            from ._branch_first import KINDS, Names

            def _swap():
                global KINDS, Names
                from ._branch_second import KINDS, Names
            """,
        ),
    ],
    ids=["try-second", "try-first", "if-second", "if-first", "global-in-a-function"],
)
def test_two_imports_in_branches_that_disagree_give_no_value(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, stem: str, user: str
) -> None:
    """Of two imports of one name in the branches of a ``try`` or an ``if``,
    either may be what the module holds, so a table or an alias they bind to
    two values is read as neither.

    The later stood for the name, so the ``except`` clause's or the
    ``else``'s import was read where the ``try`` body's or the ``if``'s,
    which runs whenever it can, holds another table and another alias. A
    function that imports the name under ``global`` may have run too, and
    what it binds may stand as much. Each case is a module of its own name,
    since the readers keep what they read of a module by its name.
    """
    _plant_modules(tmp_path, monkeypatch, {**_TWO_CHOICES, stem: user})
    constants = ccl._constants_of(f"phonometry.{stem}")
    assert "KINDS" not in constants
    assert ccl.expanded("Names", f"phonometry.{stem}") == "Names"


def test_an_alias_of_a_constant_holds_what_its_value_named_where_it_was_bound(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``ALLOWED = KINDS`` holds the table ``KINDS`` names where the
    assignment runs, whatever a later assignment binds ``KINDS`` to, in its
    module and read through an import of it; one written after the last
    binding of ``KINDS`` holds that one.

    The alias's value was read as the module held ``KINDS`` once it had run,
    so its options were those of the table a later assignment bound.
    """
    _plant_modules(
        tmp_path,
        monkeypatch,
        {
            "_alias_point": """
                KINDS = ("fast", "slow")
                ALLOWED = KINDS
                KINDS = ("other",)

                TABLE = {"a": 1, "b": 2}
                KEYS = TABLE
                TABLE = {"z": 0}

                STANDING = KINDS
                """,
            "_alias_point_user": """
                from ._alias_point import ALLOWED
                """,
        },
    )
    assert sys.modules["phonometry._alias_point"].ALLOWED == ("fast", "slow")
    constants = ccl._constants_of("phonometry._alias_point")
    assert ccl.strings_of(ast.Name(id="ALLOWED"), constants) == ("fast", "slow")
    assert ccl.strings_of(ast.Name(id="KEYS"), constants) == ("a", "b")
    assert ccl.strings_of(ast.Name(id="STANDING"), constants) == ("other",)
    imported = ccl._constants_of("phonometry._alias_point_user")
    assert ccl.strings_of(ast.Name(id="ALLOWED"), imported) == ("fast", "slow")


def test_two_imports_in_branches_that_agree_give_their_value(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two imports of one name in the branches of a ``try`` from one module
    bind it to one table and one alias, whichever runs.
    """
    user = """
        try:
            from ._branch_second import KINDS, Names
        except ImportError:
            from ._branch_second import KINDS, Names
        """
    _plant_modules(tmp_path, monkeypatch, {**_TWO_CHOICES, "_branch_agree": user})
    constants = ccl._constants_of("phonometry._branch_agree")
    assert set(ccl.strings_of(ast.Name(id="KINDS"), constants)) == {"c", "d"}
    assert ccl.expanded("Names", "phonometry._branch_agree") == "Literal['c', 'd']"


def test_a_name_imported_for_the_type_checker_is_the_import_that_stands(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A name a module imports under ``TYPE_CHECKING`` alone is read as the
    import of it that stands: the later of two in a row, and none of two in
    the branches of a ``try`` that bring in two different objects.

    The first import of the name in the source was read, so the earlier of
    two in a row stood for it, and either branch's for two that disagree.
    """
    sources = {
        "_checked_a": "class Thing:\n    pass\n",
        "_checked_b": "class Thing:\n    pass\n",
        "_checked_in_a_row": """
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                from ._checked_a import Thing
                from ._checked_b import Thing
            """,
        "_checked_in_branches": """
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                try:
                    from ._checked_a import Thing
                except ImportError:
                    from ._checked_b import Thing
            """,
    }
    _plant_modules(tmp_path, monkeypatch, sources)
    later = sys.modules["phonometry._checked_b"].Thing
    assert ccl._resolved("Thing", "phonometry._checked_in_a_row") is later
    assert ccl._resolved("Thing", "phonometry._checked_in_branches") is None


def test_an_annotation_reads_the_type_checker_s_block_and_a_value_the_else(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A type checker reads an ``if TYPE_CHECKING:`` block and never its ``else``,
    so an alias is what the block says, while the program runs the ``else``, so a
    table read as values is what that says. The ``else`` stood for the alias too,
    which read a valid ``Literal`` as a closed choice typed ``str``.
    """
    sources = {
        "_mode_alias": """
            from __future__ import annotations

            from typing import TYPE_CHECKING, Literal

            if TYPE_CHECKING:
                Mode = Literal['fast', 'slow']
                KINDS = ('a', 'b')
            else:
                Mode = str
                KINDS = ('c', 'd')

            def weigh(levels, mode: Mode = 'fast'):
                if mode == 'fast':
                    return levels
                if mode == 'slow':
                    return -levels
                raise ValueError(mode)
            """,
        "_mode_user": """
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                from ._branch_second import KINDS, Names
            else:
                from ._branch_first import KINDS, Names
            """,
        "_mode_negated": """
            from typing import TYPE_CHECKING

            if not TYPE_CHECKING:
                from ._branch_first import KINDS, Names
            else:
                from ._branch_second import KINDS, Names
            """,
    }
    _plant_modules(tmp_path, monkeypatch, {**_TWO_CHOICES, **sources})
    planted = sys.modules["phonometry._mode_alias"]
    monkeypatch.setattr(
        ccl,
        "_targets",
        lambda: iter([("phonometry._mode_alias", "weigh", planted.weigh)]),
    )
    assert list(ccl.string_choices()) == []
    assert ccl.expanded("Mode", "phonometry._mode_alias") == "Literal['fast', 'slow']"
    constants = ccl._constants_of("phonometry._mode_alias")
    assert set(ccl.strings_of(ast.Name(id="KINDS"), constants)) == {"c", "d"}
    assert ccl.expanded("Names", "phonometry._mode_user") == "Literal['c', 'd']"
    constants = ccl._constants_of("phonometry._mode_user")
    assert set(ccl.strings_of(ast.Name(id="KINDS"), constants)) == {"a", "b"}
    assert ccl.expanded("Names", "phonometry._mode_negated") == "Literal['c', 'd']"
    constants = ccl._constants_of("phonometry._mode_negated")
    assert set(ccl.strings_of(ast.Name(id="KINDS"), constants)) == {"a", "b"}


def test_a_comparison_a_test_on_type_checking_keeps_from_running_says_nothing(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A comparison no run reaches is no evidence of a closed choice: what only a
    type checker reads of a function was read as what the function does.
    """
    source = """
        from __future__ import annotations

        from typing import TYPE_CHECKING

        def in_the_block(levels, mode: str = 'fast'):
            if TYPE_CHECKING:
                if mode == 'fast':
                    return levels
                if mode == 'slow':
                    return -levels
            return levels

        def in_the_negated_else(levels, mode: str = 'fast'):
            if not TYPE_CHECKING:
                return levels
            else:
                if mode == 'fast':
                    return levels
                if mode == 'slow':
                    return -levels

        def in_a_branch(levels, mode: str = 'fast'):
            return (mode == 'fast' or mode == 'slow') if TYPE_CHECKING else levels

        def runs_in_the_negated(levels, mode: str = 'fast'):
            if not TYPE_CHECKING:
                if mode == 'fast':
                    return levels
                if mode == 'slow':
                    return -levels
            return levels
        """
    _plant_modules(tmp_path, monkeypatch, {"_kept_from_running": source})
    planted = sys.modules["phonometry._kept_from_running"]
    names = (
        "in_the_block",
        "in_the_negated_else",
        "in_a_branch",
        "runs_in_the_negated",
    )
    monkeypatch.setattr(
        ccl,
        "_targets",
        lambda: iter(
            [("phonometry._kept_from_running", n, getattr(planted, n)) for n in names]
        ),
    )
    assert {choice.qualname: choice.evidence for choice in ccl.string_choices()} == {
        "in_the_block": (),
        "in_the_negated_else": (),
        "in_a_branch": (),
        "runs_in_the_negated": ("== 'fast'", "== 'slow'"),
    }


def test_a_table_imported_from_a_sibling_module_is_followed() -> None:
    """``from .fdtd import _SIDES`` gives the elastic engine the acoustic one's
    sides, read where they are written, and a set difference with them closes
    a collection of sides.
    """
    from phonometry.simulation import elastic_fdtd

    constants = ccl._constants_of(elastic_fdtd.__name__)
    assert set(ccl.strings_of(ast.Name(id="_SIDES"), constants)) == {
        "left",
        "right",
        "top",
        "bottom",
    }
    tree = ast.parse("def f(sides):\n    return set(sides) - set(_SIDES)\n")
    found = ccl.code_evidence(
        tree,
        ccl._the_name("sides"),
        dict(constants),
        collection=True,
        module_name=__name__,
    )
    assert found == ["a set difference with a set of strings"]


def test_each_item_and_each_key_is_read() -> None:
    """A loop over the items, or over the keys of ``.items()``, checks each."""
    constants = ccl._module_constants(sys.modules[__name__])
    found = ccl.code_evidence(
        _tree(_item_by_item),
        ccl._the_name("levels"),
        constants,
        collection=True,
        module_name=__name__,
    )
    assert "each item 'in' a set of strings" in found


def test_a_string_below_the_top_level_is_read_as_it_stands() -> None:
    """The columns of each row, or the items of each list, are not followed.

    ``verify_signal_burst_response(measured)`` read the columns of each burst
    length against the printed ones while the annotation let any string in;
    a key one level down is called a choice by its annotation alone.
    """
    assert ccl.takes_nested_strings("Mapping[int, Mapping[str, float]]")
    assert ccl.takes_nested_strings("Sequence[Sequence[str]]")
    assert ccl.takes_nested_strings("tuple[Mapping[str, Any], ...] | None")
    assert ccl.takes_nested_strings("Mapping[int, tuple[Sequence[str], float]]")
    assert not ccl.takes_nested_strings("Mapping[str, float]")
    assert not ccl.takes_nested_strings("Mapping[int, str]")
    assert not ccl.takes_nested_strings(
        "Mapping[int, Mapping[Literal['rms', 'vdv'], float]]"
    )


def test_one_string_looked_for_in_a_collection_is_a_choice() -> None:
    """``"top" in sides`` names one option, as ``side == "top"`` does."""
    found = ccl.code_evidence(
        _tree(_one_looked_for),
        ccl._the_name("sides"),
        {},
        collection=True,
        module_name=__name__,
    )
    assert found == ["'top' 'in' it"]


def test_an_empty_text_is_no_option() -> None:
    """``label == ""`` asks whether a label was written, not which."""
    found = ccl.code_evidence(
        _tree(_a_label),
        ccl._the_name("labels"),
        {},
        collection=True,
        module_name=__name__,
    )
    assert found == []


def test_a_field_handed_to_a_helper_is_followed() -> None:
    """``__post_init__`` hands ``self.<field>`` to a helper that checks it, and
    the wrapper a record's ``__post_init__`` gets does not hide the helper.
    """
    assert hasattr(vars(_Wave)["__post_init__"], "__wrapped__")
    found = ccl._field_evidence(_Wave, "travel", {}, collection=False)
    assert found == ["handed to _check_travel(travel)"]


def test_a_field_compared_where_it_is_used_is_a_choice() -> None:
    """A field the record does not check is checked by the function that
    reads it; ``self.<name>`` of another class only shares the name.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    found = ccl.compared_in_module(_Source, "direction", constants)
    assert found == ["'in' a set of strings in _place()"]
    assert ccl.compared_in_module(_Labelled, "label", constants) == []


def test_a_catalogue_row_constructor_is_passed_over() -> None:
    """A catalogue row takes its cells as text by the catalogue contract."""
    from phonometry._internal.catalogue import CatalogueRow

    for home, qualname, _ in ccl._targets():
        owner = qualname.partition(".")[0]
        cls = getattr(sys.modules[home], owner, None)
        if qualname.endswith(".__init__") and isinstance(cls, type):
            assert not issubclass(cls, CatalogueRow), qualname


def test_a_membership_test_against_strings_is_a_choice() -> None:
    """``mode not in ("fast", "slow")`` is the commonest closed choice."""
    found = ccl.code_evidence(
        _tree(_compared), ccl._the_name("mode"), {}, module_name=__name__
    )
    assert "'in' a set of strings" in found


def test_an_equality_with_a_string_is_a_choice() -> None:
    """``mode == "fast"`` names one option, so the set is closed."""
    found = ccl.code_evidence(
        _tree(_equal), ccl._the_name("mode"), {}, module_name=__name__
    )
    assert "== 'fast'" in found


def test_a_shared_validator_is_a_choice() -> None:
    """``require_choice`` refuses anything but its options."""
    found = ccl.code_evidence(
        _tree(_validated), ccl._the_name("mode"), {}, module_name=__name__
    )
    assert "require_choice()" in found


def test_a_parameter_passed_on_to_a_literal_is_a_choice() -> None:
    """Handing the text to a ``Literal`` parameter makes it the same choice."""
    found = ccl.passed_on_evidence(_passed_on, "mode")
    assert found == ["handed to time_weighting(mode)"]


def test_a_str_inside_a_union_is_read_as_a_choice() -> None:
    """``str | float`` lets any string through as surely as ``str`` alone.

    So does the ``Literal[...] | str`` the guide forbids, while a ``str``
    nested inside another type (``Mapping[str, float]``) is not the choice.
    """
    assert ccl.takes_any_string("str | float | np.ndarray | None")
    assert ccl.takes_any_string("Literal['zero', 'first'] | str")
    assert ccl.takes_any_string("Optional[str]")
    assert not ccl.takes_any_string("Literal['zero', 'first'] | float | None")
    assert not ccl.takes_any_string("Mapping[str, float] | None")


def test_a_text_cleaned_up_before_the_check_is_a_choice() -> None:
    """``str(mode).strip().lower() in (...)`` checks the caller's choice."""
    found = ccl.code_evidence(
        _tree(_normalised), ccl._the_name("mode"), {}, module_name=__name__
    )
    assert "'in' a set of strings" in found


def test_a_local_bound_from_the_text_is_followed() -> None:
    """``key = _resolve(mode)`` and then ``key not in (...)`` is the same check."""
    found = ccl.code_evidence(
        _tree(_derived), ccl._the_name("mode"), {}, module_name=__name__
    )
    assert "'in' a set of strings" in found


def test_a_table_handed_on_beside_the_text_closes_the_helper() -> None:
    """The helper's ``key not in table`` is closed by the caller's table."""
    found = ccl.passed_on_evidence(_hands_a_table, "side")
    assert found == ["handed to _check_against(name)"]


def test_a_parameter_spread_from_a_dict_is_followed() -> None:
    """``f(**options)`` hands each key of the dict to the parameter it names."""
    found = ccl.passed_on_evidence(_spreads, "mode")
    assert found == ["handed to time_weighting(mode)"]


@dataclass
class _Built:
    kind: str
    other: int = 0


@pytest.mark.parametrize(
    ("call", "handed"),
    [
        ("R(**options, kind='a')", "'a'"),
        ("R(kind='a', **options)", "'a'"),
        ("R('a', **options)", "'a'"),
        ("R(*rest, kind='a')", "'a'"),
        ("R(**options)", "**"),
        ("R(*rest)", "**"),
        ("R(other=1)", None),
    ],
)
def test_a_mapping_hands_nothing_to_a_place_an_argument_fills(
    call: str, handed: str | None
) -> None:
    """A place the call fills by its keyword, or in its place before any
    ``*`` argument, is that argument's alone: a ``**`` mapping that filled it
    too would make the call raise. Only a place nothing fills is one the
    mapping, or a ``*`` argument at or before it, may fill.

    The keyword was looked for only until the first mapping, and a mapping
    anywhere opened the place an argument filled, so a record built with
    ``kind='a'`` beside ``**options`` read as built with anything.
    """
    node = ast.parse(call, mode="eval").body
    assert isinstance(node, ast.Call)
    kind = next(f for f in dataclasses.fields(_Built) if f.name == "kind")
    found = ccl._argument_for(node, kind, ["kind", "other"])
    shown = ast.unparse(found) if isinstance(found, ast.expr) else found
    assert shown == handed


@pytest.mark.parametrize(
    ("call", "texts"),
    [
        ("_helper(text, kind='a')", None),
        ("_helper('a', **{'kind': text})", frozenset({"a"})),
    ],
)
def test_a_keyword_fills_no_positional_only_parameter(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    call: str,
    texts: frozenset[str] | None,
) -> None:
    """A keyword, or a ``**`` mapping, that names a positional-only parameter
    of a private helper goes to its ``**kw``; the place is the argument's.

    The keyword was read as the parameter's, so ``_helper(text, kind='a')``
    read as handing the helper the fixed text ``'a'`` where it hands the
    caller's free one, and a mapping beside a fixed text read as handing
    anything.
    """
    source = (
        "def _helper(kind, /, **kw):\n    return kind\n\n"
        f"def make(text):\n    return {call}\n"
    )
    _plant_modules(tmp_path, monkeypatch, {"_positional_only": source})
    tree = ast.parse(source)
    helper, make = tree.body
    assert isinstance(helper, ast.FunctionDef)
    assert isinstance(make, ast.FunctionDef)
    assert isinstance(make.body[0], ast.Return)
    site = make.body[0].value
    assert isinstance(site, ast.Call)
    module = "phonometry._positional_only"
    monkeypatch.setattr(
        ccl, "_construction_sites", lambda: {"_helper": ((module, make, site),)}
    )
    found = ccl._callers_source(helper, "kind", module, 0)
    assert (found.texts if found.kind == "texts" else None) == texts


def test_a_private_method_called_through_its_class_takes_the_instance_first(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``Maker._helper(self, "a", text)`` hands ``self`` to the method's
    ``self`` and the fixed text to its ``kind``, as ``self._helper("b",
    text)`` does, and a class method called through its class is bound to
    it: every caller hands ``kind`` a fixed text.

    A method's ``self`` was taken as filled by the call whatever named the
    method, so ``self`` was read as the ``kind`` the first call hands, and
    the texts came back open.
    """
    source = (
        "class Maker:\n"
        "    def _helper(self, kind, other):\n"
        "        return kind\n\n"
        "    @classmethod\n"
        "    def _once(cls, kind):\n"
        "        return kind\n\n"
        "    def through_the_class(self, text):\n"
        "        return Maker._helper(self, 'a', text)\n\n"
        "    def on_self(self, text):\n"
        "        return self._helper('b', text)\n\n"
        "    def bound_to_the_class(self):\n"
        "        return Maker._once('c')\n"
    )
    _plant_modules(tmp_path, monkeypatch, {"_through_the_class": source})
    tree = ast.parse(source)
    maker = tree.body[0]
    assert isinstance(maker, ast.ClassDef)
    helper, once, *callers = maker.body
    assert isinstance(helper, ast.FunctionDef)
    assert isinstance(once, ast.FunctionDef)
    module = "phonometry._through_the_class"
    sites: dict[str, list[tuple[str, ast.AST | None, ast.Call]]] = {}
    for caller in callers:
        assert isinstance(caller, ast.FunctionDef)
        assert isinstance(caller.body[0], ast.Return)
        site = caller.body[0].value
        assert isinstance(site, ast.Call)
        assert isinstance(site.func, ast.Attribute)
        sites.setdefault(site.func.attr, []).append((module, caller, site))
    monkeypatch.setattr(
        ccl,
        "_construction_sites",
        lambda: {name: tuple(found) for name, found in sites.items()},
    )
    assert ccl._callers_source(helper, "kind", module, 0) == ccl._Source(
        "texts", frozenset({"a", "b"})
    )
    assert ccl._callers_source(helper, "other", module, 0).kind == "open"
    assert ccl._callers_source(once, "kind", module, 0) == ccl._Source(
        "texts", frozenset({"c"})
    )


def test_a_private_function_or_static_method_takes_what_its_callers_hand(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``_shaped(Maker, "a")`` hands the class to ``_shaped``'s ``cls`` and
    the fixed text to its ``kind``, as ``Maker._for(Maker, "b")`` and
    ``self._for(Maker, "c")`` do to a static method's: a function and a
    static method take every argument a call hands them, whatever their
    first parameter is called.

    A first parameter called ``cls`` was taken as filled by every call, so
    the class was read as the ``kind`` the call hands, and the texts came
    back open.
    """
    source = (
        "def _shaped(cls, kind):\n"
        "    return kind\n\n"
        "class Maker:\n"
        "    @staticmethod\n"
        "    def _for(cls, kind):\n"
        "        return kind\n\n"
        "    def by_name(self, text):\n"
        "        return _shaped(Maker, 'a')\n\n"
        "    def through_the_class(self, text):\n"
        "        return Maker._for(Maker, 'b')\n\n"
        "    def on_self(self, text):\n"
        "        return self._for(Maker, 'c')\n"
    )
    _plant_modules(tmp_path, monkeypatch, {"_helpers_with_cls": source})
    tree = ast.parse(source)
    shaped, maker = tree.body
    assert isinstance(shaped, ast.FunctionDef)
    assert isinstance(maker, ast.ClassDef)
    static, *callers = maker.body
    assert isinstance(static, ast.FunctionDef)
    module = "phonometry._helpers_with_cls"
    sites: dict[str, list[tuple[str, ast.AST | None, ast.Call]]] = {}
    for caller in callers:
        assert isinstance(caller, ast.FunctionDef)
        assert isinstance(caller.body[0], ast.Return)
        site = caller.body[0].value
        assert isinstance(site, ast.Call)
        assert isinstance(site.func, ast.Name | ast.Attribute)
        called = site.func.id if isinstance(site.func, ast.Name) else site.func.attr
        sites.setdefault(called, []).append((module, caller, site))
    monkeypatch.setattr(
        ccl,
        "_construction_sites",
        lambda: {name: tuple(found) for name, found in sites.items()},
    )
    assert ccl._callers_source(shaped, "kind", module, 0) == ccl._Source(
        "texts", frozenset({"a"})
    )
    assert ccl._callers_source(static, "kind", module, 0) == ccl._Source(
        "texts", frozenset({"b", "c"})
    )


def test_a_function_the_body_imports_is_followed() -> None:
    """A call to a name the body imports itself reaches the library function."""
    found = ccl.passed_on_evidence(_imports_inside, "mode")
    assert found == ["handed to time_weighting(mode)"]


def test_a_str_beside_an_enum_is_a_choice() -> None:
    """``_Colour | str`` takes the members or the strings they stand for."""
    module = sys.modules[__name__]
    assert ccl.enum_beside("_Colour | str", module) == ["a str beside the Enum _Colour"]
    assert ccl.enum_beside("float | str", module) == []


def test_a_free_text_is_not_a_choice() -> None:
    """A label that is only transformed is open text, and nothing is reported."""
    assert (
        ccl.code_evidence(
            _tree(_free), ccl._the_name("label"), {}, module_name=__name__
        )
        == []
    )
    assert ccl.passed_on_evidence(_free, "label") == []


def test_two_quoted_options_in_the_docstring_are_a_choice() -> None:
    """The documented options count even when the body checks nothing."""
    assert ccl.documented_options(_documented.__doc__, "mode") == ("fast", "slow")


@pytest.mark.whole_tree
def test_a_stale_open_entry_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exemption that names nothing the walk finds cannot outlive its reason."""
    key = ("phonometry.nowhere", "gone", "mode")
    monkeypatch.setitem(ccl.OPEN, key, "a reason that no longer applies")
    found, stale = ccl.offenders()
    assert found == []
    assert stale == [key]


def test_a_class_written_into_between_two_methods_is_still_read_whole() -> None:
    """The methods of a class are read off its namespace as it was at the start.

    Reading a class's annotations on Python 3.14 stores them in its namespace,
    and what the walk does with one method may read them before the next; a
    namespace that grows while its methods are handed out must neither stop
    the walk nor change it.
    """

    class _Grows:
        def first(self, mode: str) -> str:
            return mode

        def second(self, mode: str) -> str:
            return mode

    names = []
    for name, _ in ccl._public_methods(_Grows):
        names.append(name)
        setattr(_Grows, f"added_after_{name}", lambda self: None)
    assert names == ["first", "second"]


@pytest.mark.whole_tree
def test_every_public_choice_of_the_package_is_a_literal() -> None:
    """The package passes: no closed choice is typed ``str``, no entry is stale."""
    found, stale = ccl.offenders()
    assert found == []
    assert stale == []


def _closed(pairs: list[tuple[object, object]]) -> list[tuple[object, object]]:
    """The pairs whose two sides differ, with the alias read as a set."""
    return [
        (alias, options)
        for alias, options in pairs
        if set(typing.get_args(alias)) != set(options)  # type: ignore[call-overload]
    ]


def test_every_vocabulary_offers_what_its_table_holds() -> None:
    """A ``Literal`` and the table that answers it name the same options.

    The alias is what a type checker holds the caller to and the table is
    what the function reads, so an option in one and not the other is either
    refused by the checker and accepted when the call runs, or the reverse.
    """
    from phonometry._internal import catalogue
    from phonometry.aircraft import measurement_system
    from phonometry.building.measurement import survey_insulation, uncertainty
    from phonometry.building.prediction import panel_transmission
    from phonometry.electroacoustics import headphones
    from phonometry.emission import free_field_qualification
    from phonometry.environment.assessment import soundscape, soundscape_binaural
    from phonometry.environment.sources import (
        cnossos_rail,
        cnossos_road,
        rolling_stock_noise,
        track_decay,
    )
    from phonometry.hearing import sound_field_audiometry
    from phonometry.materials.absorbers import porous, suspended_ceilings
    from phonometry.metrology import (
        comparison_calibration,
        free_field_corrections,
        reciprocity_calibration,
        sound_level_meter,
    )
    from phonometry.noise_control import (
        _duct_path,
        duct_modes,
        enclosure_insulation,
        silencers,
    )
    from phonometry.underwater.bioacoustics import audiograms
    from phonometry.underwater.bioacoustics import weighting as hearing
    from phonometry.underwater.sources import ship_traffic_noise
    from phonometry.vibration.human import exposure, signal_burst
    from phonometry.vibration.immission import coupling, train_categories

    rooms = {key for row in survey_insulation._TABLE3.values() for key in row}
    # A duct section's dimensions are spread into plane_wave_limit as its
    # keywords; the flow and the speed of sound are not dimensions.
    dimensions = set(inspect.signature(duct_modes.plane_wave_limit).parameters) - {
        "flow_velocity",
        "speed_of_sound",
    }
    groups = {key for table in hearing._PARAMETERS.values() for key in table}
    # The base standards of Table 1 of ISO 11546, by the quantity each row
    # gives: a sound power (D_W...) or a sound pressure level (D_p, D_pA).
    methods = [row for rows in enclosure_insulation._METHODS.values() for row in rows]
    power = {
        row.base_standard
        for row in methods
        if any(q.startswith("D_W") for q in row.quantities)
    }
    pressure = {
        row.base_standard
        for row in methods
        if any(q in {"D_p", "D_pA"} for q in row.quantities)
    }
    comparison = comparison_calibration
    reciprocity = reciprocity_calibration
    pairs: list[tuple[object, object]] = [
        (exposure.WeightingName, exposure._WEIGHTINGS),
        (signal_burst.BurstApplication, signal_burst.SAWTOOTH_BURST_TESTS),
        (train_categories.TrainKind, train_categories.TRAIN_KINDS),
        (coupling.DisplayedQuantity, coupling.INSTRUMENT_CONFIDENCE_LIMITS_PERCENT),
        (audiograms.AudiogramGroup, audiograms._AUDIOGRAM_ORIGINAL),
        (hearing.HearingGroup, groups),
        (ship_traffic_noise.VesselClass, ship_traffic_noise._VESSEL_CLASSES),
        (
            uncertainty.SingleNumberQuantity,
            set(uncertainty._SINGLE) | set(uncertainty._ALIASES),
        ),
        (survey_insulation.SurveyRoom, rooms),
        (panel_transmission.PlateauMaterialName, panel_transmission.PLATEAU_MATERIALS),
        (porous.DelanyBazleyPreset, porous.DELANY_BAZLEY_COEFFICIENTS),
        (suspended_ceilings.MountingLetter, suspended_ceilings.MOUNTING_TYPES),
        (
            enclosure_insulation.TestEnvironmentStandard,
            enclosure_insulation.TEST_ENVIRONMENT_REQUIREMENTS,
        ),
        (
            cnossos_road.RoadVehicleCode,
            [member.value for member in cnossos_road.RoadVehicleCategory],
        ),
        (
            cnossos_road.RoadSurfaceName,
            [member.value for member in cnossos_road.RoadSurface],
        ),
        (cnossos_rail.BrakeCode, [member.value for member in cnossos_rail.BrakeType]),
        (cnossos_rail.RailRoughnessCode, cnossos_rail._TABLE_G1B),
        (
            cnossos_rail.TabulatedRailRoughness,
            [
                member
                for member in cnossos_rail.RailRoughnessClass
                if member.value in cnossos_rail._TABLE_G1B
            ],
        ),
        (
            cnossos_rail.TrackTransferCode,
            [member.value for member in cnossos_rail.TrackTransferClass],
        ),
        (
            cnossos_rail.TractionVehicleName,
            [member.value for member in cnossos_rail.TractionVehicle],
        ),
        (
            cnossos_rail.BridgeTypeName,
            [member.value for member in cnossos_rail.BridgeType],
        ),
        (catalogue.ProvenanceKind, catalogue.PROVENANCE_KINDS),
        (measurement_system.LinearityRange, measurement_system._LINEARITY_LIMITS),
        (headphones.TransducerPrinciple, headphones.TRANSDUCER_PRINCIPLES),
        (headphones.EarphoneType, headphones.EARPHONE_TYPES),
        (headphones.AcousticCoupling, headphones.ACOUSTIC_COUPLINGS),
        (headphones.BackRadiation, headphones.BACK_RADIATIONS),
        (free_field_qualification.PathTarget, free_field_qualification._PATH_TARGETS),
        (
            soundscape.AffectiveQuality,
            soundscape.PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES,
        ),
        (soundscape_binaural.BinauralRow, soundscape_binaural.BINAURAL_PARAMETERS),
        (
            sound_field_audiometry.SoundFieldPosition,
            sound_field_audiometry._DIFFUSE_POSITIONS,
        ),
        (
            sound_field_audiometry.LateralPosition,
            sound_field_audiometry._LATERAL_POSITIONS,
        ),
        (
            free_field_corrections.TableI1Descriptor,
            free_field_corrections.IEC62585_TABLE_I1,
        ),
        (sound_level_meter.MeterWeighting, sound_level_meter._WEIGHTINGS),
        (sound_level_meter.WeightingVersusA, sound_level_meter._WEIGHTINGS_VS_A),
        (sound_level_meter.DisplayVersusF, sound_level_meter._TIME_WEIGHTINGS_VS_F),
        (sound_level_meter.ToneburstResponse, sound_level_meter._TONEBURST_KEYS),
        (sound_level_meter.RangeReading, sound_level_meter._RANGE_READINGS),
        (sound_level_meter.SlmRequirement, sound_level_meter.SLM_PERIODIC_REQUIREMENTS),
        (sound_level_meter.SlmClause, set(sound_level_meter._CLAUSES.values())),
        (silencers.SilencerDimension, silencers._GEOMETRY_KEYS),
        (_duct_path.DuctSectionDimension, dimensions),
        (signal_burst.BurstQuantity, signal_burst.BURST_TOLERANCE_PERCENT),
        (comparison.PressureComparisonComponent, comparison.IEC61094_5_TABLE_D1),
        (comparison.FreeFieldComparisonComponent, comparison.IEC61094_8_TABLE_2),
        (
            comparison.ComparisonComponent,
            {*comparison.IEC61094_5_TABLE_D1, *comparison.IEC61094_8_TABLE_2},
        ),
        (
            comparison.SharedComparisonComponent,
            set(comparison.IEC61094_5_TABLE_D1) & set(comparison.IEC61094_8_TABLE_2),
        ),
        (reciprocity.PressureReciprocityComponent, reciprocity.IEC61094_2_TABLE_1),
        (reciprocity.FreeFieldReciprocityComponent, reciprocity.IEC61094_3_TABLE_1),
        (
            reciprocity.ReciprocityComponent,
            {*reciprocity.IEC61094_2_TABLE_1, *reciprocity.IEC61094_3_TABLE_1},
        ),
        (
            reciprocity.SharedReciprocityComponent,
            set(reciprocity.IEC61094_2_TABLE_1) & set(reciprocity.IEC61094_3_TABLE_1),
        ),
        (enclosure_insulation.SoundPowerStandard, power),
        (enclosure_insulation.SoundPressureStandard, pressure),
        (track_decay.Direction, track_decay.TRACK_DECAY_DIRECTIONS),
        (
            track_decay.Direction,
            rolling_stock_noise.REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M,
        ),
    ]
    assert _closed(pairs) == []


def test_an_area_type_is_one_every_limit_table_prints() -> None:
    """RD 1367 area ``f`` has no row in Tables A, A1, A2 or B1, so it is no option.

    Each option, a letter or an alias, resolves to a row of all four tables.
    """
    from phonometry.environment.assessment import spain

    tables = (
        spain._OUTDOOR_OBJECTIVES,
        spain._INFRASTRUCTURE_LIMITS,
        spain._MAX_INFRASTRUCTURE_LIMITS,
        spain._ACTIVITY_LIMITS,
    )
    resolved = {spain._AREA_ALIASES.get(o, o) for o in typing.get_args(spain.AreaType)}
    assert all(resolved == set(table) for table in tables)


# --------------------------------------------------------------------------
# One spelling (rule A45): a choice typed Literal is checked as written.

#: The options of the synthetic choices below.
_Pace = Literal["fast", "slow"]
_PACES: tuple[_Pace, ...] = ("fast", "slow")


def _folded_before_the_check(mode: _Pace) -> str:
    key = mode.strip().lower()
    return require_choice(key, "mode", _PACES)


def _checked_before_the_fold(mode: _Pace) -> str:
    named = require_choice(mode, "mode", _PACES)
    return named.upper()


def _refused_before_the_fold(mode: _Pace) -> str:
    if mode not in _PACES:
        raise ValueError(mode)
    return mode.title()


def _made_a_text(mode: _Pace) -> str:
    return require_choice(
        str(mode),
        "mode",
        _PACES,
    )


def _lowered(text: str) -> str:
    return text.lower()


def _folded_by_a_helper(mode: _Pace) -> str:
    return require_choice(_lowered(mode), "mode", _PACES)


def _checks(text: object) -> _Pace:
    return require_choice(text, "mode", _PACES)


def _checked_by_a_helper(mode: _Pace) -> str:
    _checks(mode)
    return mode.casefold()


def _folded_after_a_private_helper(mode: _Pace) -> bool:
    return _resolve(mode).upper() == "FAST"


#: Spellings no option lists, mapped to one.
_UNLISTED_ALIASES = {"quick": "fast"}

#: A spelling the Literal lists on purpose, mapped to the option it stands for.
_LISTED_ALIASES = {"slow": "fast"}


def _maps_an_unlisted_alias(mode: _Pace) -> str:
    key = _UNLISTED_ALIASES.get(mode, mode)
    return require_choice(key, "mode", _PACES)


def _maps_a_listed_alias(mode: _Pace) -> str:
    key = _LISTED_ALIASES.get(mode, mode)
    return require_choice(key, "mode", _PACES)


def _items_folded(sides: Sequence[_Side]) -> set[str]:
    return {side.lower() for side in sides if side.lower() in ("left", "right")}


def _keys_checked_as_a_whole(levels: Mapping[_Side, float]) -> set[str]:
    extra = set(levels) - {"left", "right"}
    if extra:
        raise ValueError(sorted(extra))
    return {str(side) for side in levels}


def _cleaned(
    function: object, name: str, *, options: tuple[str, ...], collection: bool = False
) -> list[str]:
    reading = ccl._received(
        function,
        name,
        options=frozenset(options),
        collection=collection,
        depth=0,
    )
    return ccl._cleans_up_first(reading)


def test_a_clean_up_before_the_check_is_refused() -> None:
    """``mode.strip().lower()`` ahead of ``require_choice`` lets ``" FAST "`` in."""
    assert _cleaned(_folded_before_the_check, "mode", options=_PACES) == [
        ".lower()",
        ".strip()",
    ]


def test_a_check_as_written_before_the_clean_up_passes() -> None:
    """A clean-up after the text is checked as written accepts nothing more."""
    assert _cleaned(_checked_before_the_fold, "mode", options=_PACES) == []
    assert _cleaned(_refused_before_the_fold, "mode", options=_PACES) == []


def test_a_text_made_of_any_value_is_a_clean_up() -> None:
    """``str(mode)`` takes ``2`` for ``"2"``, on a line of its own or not."""
    assert _cleaned(_made_a_text, "mode", options=_PACES) == ["str()"]


def test_a_clean_up_in_a_helper_is_followed() -> None:
    """The helper folds the text it is handed before anyone checks it."""
    assert _cleaned(_folded_by_a_helper, "mode", options=_PACES) == [
        "handed to _lowered(text), .lower()"
    ]


def test_a_check_in_a_helper_is_a_check_where_it_is_called() -> None:
    """A helper that checks the text first checks it for its caller."""
    assert _cleaned(_checked_by_a_helper, "mode", options=_PACES) == []


def test_a_clean_up_of_what_a_private_helper_hands_back_is_one() -> None:
    """``_resolve(mode).upper()`` folds the text the helper hands back."""
    assert _cleaned(_folded_after_a_private_helper, "mode", options=_PACES) == [
        ".upper()"
    ]


def test_an_alias_the_literal_does_not_list_is_refused() -> None:
    """``ALIASES.get(mode, mode)`` with a key no option spells takes it in;
    a map of spellings the ``Literal`` lists on purpose accepts nothing more.
    """
    assert _cleaned(_maps_an_unlisted_alias, "mode", options=_PACES) == [
        "an alias map .get(text, text)"
    ]
    assert _cleaned(_maps_a_listed_alias, "mode", options=_PACES) == []


def test_the_items_of_a_collection_are_read_one_by_one() -> None:
    """Each item folded before its check is a clean-up; a leftover refused as
    a whole (``set(levels) - OPTIONS``) is a check of every key as written.
    """
    sides = ("left", "right")
    assert _cleaned(_items_folded, "sides", options=sides, collection=True) == [
        ".lower()"
    ]
    assert (
        _cleaned(_keys_checked_as_a_whole, "levels", options=sides, collection=True)
        == []
    )


@dataclass(frozen=True)
class _Checked:
    """A record that checks its choice as written when it is built."""

    pace: _Pace

    def __post_init__(self) -> None:
        require_choice(self.pace, "pace", _PACES)


@dataclass(frozen=True)
class _Unchecked:
    """A record that leaves its choice to whoever reads it."""

    stride: _Pace


def _reads_checked(record: _Checked) -> bool:
    return record.pace.lower() == "fast"


def _reads_unchecked(record: _Unchecked) -> bool:
    return record.stride.lower() == "fast"


def test_a_record_field_is_read_where_its_module_uses_it() -> None:
    """A field checked when the record is built may be cleaned up later; one
    that is not is cleaned up by the module that reads it.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    options = frozenset(_PACES)
    checked = ccl._field_spelling(
        _Checked, "pace", constants, options=options, collection=False
    )
    unchecked = ccl._field_spelling(
        _Unchecked, "stride", constants, options=options, collection=False
    )
    assert checked == []
    assert unchecked == [".lower() in _reads_unchecked()"]


@pytest.mark.whole_tree
def test_every_literal_choice_is_checked_as_written() -> None:
    """The package passes: no public choice typed ``Literal`` is cleaned up
    before its check, here or in a function it is handed to (rule A45).
    """
    assert list(ccl.cleaned_up_choices()) == []


#: Two route names, bound to constants a table is keyed by.
_PER_LEAF = "per_leaf"
_TOGETHER = "together"
_ROUTES = {_PER_LEAF: 40.0, _TOGETHER: 50.0}


def _route(quantity: str) -> float:
    if quantity not in _ROUTES:
        raise ValueError(quantity)
    return _ROUTES[quantity]


def test_a_table_keyed_by_named_constants_holds_their_strings() -> None:
    """``{_DNT_A: ...}`` is keyed by the text ``_DNT_A`` is bound to, so a
    ``str`` checked against it is a closed choice like one checked against
    ``{"DnT,A": ...}``.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    assert ccl.strings_of(ast.Name(id="_ROUTES"), constants) == ("per_leaf", "together")
    found = ccl.code_evidence(
        _tree(_route), ccl._the_name("quantity"), constants, module_name=__name__
    )
    assert found == ["'in' a set of strings", "a lookup by key"]


class _Pacer:
    """A class whose public method hands its choice to a method of its own."""

    def pace(self, mode: _Pace) -> bool:
        return self._matches(mode)

    def _matches(self, mode: str) -> bool:
        return mode.lower() in _PACES


@dataclass(frozen=True)
class _Holder:
    """A record whose public method hands its choice to an object it holds."""

    pacer: _Pacer

    def pace(self, mode: _Pace) -> bool:
        return self.pacer.pace(mode)


def test_a_clean_up_in_a_method_of_its_own_class_is_followed() -> None:
    """``self._matches(mode)`` and ``self.pacer.pace(mode)`` are followed
    into the method they call, through the class and through the annotation
    of the field that holds the object.
    """
    assert _cleaned(_Pacer.pace, "mode", options=_PACES) == [
        "handed to _Pacer._matches(mode), .lower()"
    ]
    assert _cleaned(_Holder.pace, "mode", options=_PACES) == [
        "handed to _Pacer.pace(mode), handed to _Pacer._matches(mode), .lower()"
    ]


#: The options of a check that also takes a spelling of its own.
_QUICK = {"quick": "fast"}


def _checked_against_more(mode: _Pace) -> str:
    named = require_choice(mode, "mode", (*_PACES, *_QUICK))
    return _QUICK.get(named, named)


def test_a_check_against_options_the_literal_does_not_list_is_refused() -> None:
    """``require_choice(mode, "mode", (*_PACES, *_QUICK))`` reads the text as
    written and still takes ``"quick"``, which no option spells.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    starred = ast.parse("(*_PACES, *_QUICK)", mode="eval").body
    assert ccl.strings_of(starred, constants) == ("fast", "slow", "quick")
    assert _cleaned(_checked_against_more, "mode", options=_PACES) == [
        "options wider than the Literal ('quick',)"
    ]
    assert _cleaned(_checked_before_the_fold, "mode", options=_PACES) == []


def _refused_against_more(mode: _Pace) -> str:
    if mode not in ("fast", "slow", "quick"):
        raise ValueError(mode)
    return mode.lower()


def _sides_held_to_more(sides: Sequence[_Side]) -> set[str]:
    if not set(sides) <= {"left", "right", "top"}:
        raise ValueError(sides)
    return {side.upper() for side in sides}


def _keys_held_to_more(levels: Mapping[_Side, float]) -> set[str]:
    extra = set(levels) - {"left", "right", "top"}
    if extra:
        raise ValueError(sorted(extra))
    return {side.upper() for side in levels}


def test_a_membership_test_against_options_the_literal_does_not_list_is_refused() -> (
    None
):
    """``if mode not in ("fast", "slow", "quick"): raise`` reads the text as
    written and still takes ``"quick"``; so do a subset test and a leftover
    refused as a whole against a set wider than the ``Literal``.
    """
    sides = ("left", "right")
    assert _cleaned(_refused_against_more, "mode", options=_PACES) == [
        "options wider than the Literal ('quick',)"
    ]
    assert _cleaned(_sides_held_to_more, "sides", options=sides, collection=True) == [
        "options wider than the Literal ('top',)"
    ]
    assert _cleaned(_keys_held_to_more, "levels", options=sides, collection=True) == [
        "options wider than the Literal ('top',)"
    ]
    assert _cleaned(_refused_before_the_fold, "mode", options=_PACES) == []
    assert (
        _cleaned(_keys_checked_as_a_whole, "levels", options=sides, collection=True)
        == []
    )


#: The options of two kinds of record, one row each, as a shared helper picks
#: the row of the record it is handed.
_ROWS_BY_KIND = {"pace": ("fast", "slow"), "gait": ("walk", "run")}

#: The same table, with a row for the pace that also takes a spelling of its own.
_WIDER_ROWS = {"pace": ("fast", "slow", "quick"), "gait": ("walk", "run")}


def _refused_against_a_picked_row(mode: _Pace, kind: str) -> str:
    paces = _ROWS_BY_KIND[kind]
    if mode not in paces:
        raise ValueError(mode)
    return mode.lower()


def _refused_against_a_wider_row(mode: _Pace, kind: str) -> str:
    if mode not in _WIDER_ROWS[kind]:
        raise ValueError(mode)
    return mode.lower()


def test_a_check_against_a_row_picked_at_run_time_is_held_to_the_closest_row() -> None:
    """``_ROWS_BY_KIND[kind]`` is one row of the table, and the row of the
    ``Literal``'s own options takes nothing more; a table none of whose rows
    is the ``Literal``'s alone lets through what the closest row adds.
    """
    assert _cleaned(_refused_against_a_picked_row, "mode", options=_PACES) == []
    assert _cleaned(_refused_against_a_wider_row, "mode", options=_PACES) == [
        "options wider than the Literal ('quick',)"
    ]


def test_an_escape_in_a_literal_option_is_the_character_it_spells() -> None:
    """An escape written in a ``Literal`` option is the character it spells,
    a tab and not a backslash and a ``t``, so ``write_catalogue``'s tab
    delimiter is one of the options its check holds it to.
    """
    assert ccl._literal_options('Literal[",", ";", "\\t"]') == {",", ";", "\t"}


class _PrivateBase:
    """A base the package would not export, with a public method."""

    def paced(self, mode: _Pace) -> bool:
        return mode.upper() == "FAST"


class _Exported(_PrivateBase):
    """A class that inherits ``paced`` and defines nothing of its own."""


class _Overriding(_PrivateBase):
    """A class that defines ``paced`` again, so it inherits nothing."""

    def paced(self, mode: _Pace) -> bool:
        return require_choice(mode, "mode", _PACES) == "fast"


def test_a_public_method_inherited_from_a_private_base_is_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``paced`` is a public method of ``_Exported``, defined on its base:
    it is read, under the base, and its clean-up fails; a method the class
    defines again is its own.
    """
    monkeypatch.setattr(_PrivateBase, "__module__", "phonometry.synthetic")
    inherited = list(ccl._inherited_methods(_Exported))
    overridden = list(ccl._inherited_methods(_Overriding))
    assert inherited == [(_PrivateBase, "paced", _PrivateBase.paced)]
    assert overridden == []
    assert _cleaned(_PrivateBase.paced, "mode", options=_PACES) == [".upper()"]


def test_a_method_the_package_inherits_from_a_private_base_is_read_once() -> None:
    """``plot`` of the six layers of ``materials.absorbers.layered`` is
    defined on ``_DrawableLayer``: the walk reads it once, under that base.
    """
    plots = [
        (home, qualname)
        for home, qualname, _ in ccl._targets()
        if qualname.endswith("_DrawableLayer.plot")
    ]
    assert plots == [("phonometry.materials.absorbers.layered", "_DrawableLayer.plot")]


def _never_checked(mode: _Pace) -> bool:
    return mode == "fast"


def _checked_with_not_in(mode: _Pace) -> _Pace:
    if mode not in _PACES:
        raise ValueError(mode)
    return mode


def _checked_beside_another(mode: _Pace, *, strict: bool) -> _Pace:
    if strict:
        require_choice(mode, "mode", _PACES)
    return mode


def _checked_behind_its_own_test(mode: _Pace | None) -> _Pace | None:
    if mode is not None:
        require_choice(mode, "mode", _PACES)
    return mode


def _verdict_of(
    function: Callable[..., object],
    name: str,
    *,
    collection: bool = False,
    options: Iterable[str] = (),
) -> str | None:
    return ccl._verdict(
        ccl._checks_of(
            function,
            name,
            field=False,
            collection=collection,
            depth=0,
            options=frozenset(options),
        )
    )


def test_a_choice_is_checked_by_a_shared_validator_on_every_path() -> None:
    """``require_choice`` where the function starts passes; a check only
    beside another argument, a ``not in`` that refuses a number with
    ``ValueError`` and no check at all each fail with their own verdict.
    """
    assert _verdict_of(_validated, "mode") is None
    assert _verdict_of(_checked_behind_its_own_test, "mode") is None
    assert _verdict_of(_checked_beside_another, "mode") == (
        "checked on some paths only, so a misspelling passes on the others"
    )
    assert _verdict_of(_checked_with_not_in, "mode") == (
        "checked with ``not in``, so a value that is not a text is refused "
        "with ValueError instead of TypeError"
    )
    assert _verdict_of(_never_checked, "mode") == (
        "never checked, so a misspelling passes"
    )


def _checked_after_an_early_return(mode: _Pace, *, quick: bool) -> _Pace:
    if quick:
        return "fast"
    require_choice(mode, "mode", _PACES)
    return mode


def _column_of(mode: _Pace, *, quick: bool) -> int:
    if quick:
        return 0
    require_choice(mode, "mode", _PACES)
    return 1


def _checked_after_a_helper_returns_early(mode: _Pace, *, quick: bool) -> int:
    return _column_of(mode, quick=quick)


def _checked_after_its_own_early_return(mode: _Pace | None) -> _Pace | None:
    if mode is None:
        return None
    require_choice(mode, "mode", _PACES)
    return mode


def _checked_before_an_early_return(mode: _Pace, *, quick: bool) -> _Pace:
    require_choice(mode, "mode", _PACES)
    if quick:
        return "fast"
    return mode


def _checked_after_a_yield(mode: _Pace) -> typing.Iterator[_Pace]:
    yield "fast"
    yield require_choice(mode, "mode", _PACES)


def _items_skipped_before_the_check(paces: Sequence[_Pace], *, skip: bool) -> None:
    for pace in paces:
        if skip:
            continue
        require_choice(pace, "paces", _PACES)


def _items_checked_after_an_inner_loop(paces: Sequence[_Pace]) -> None:
    for pace in paces:
        for _ in range(2):
            if pace:
                break
        require_choice(pace, "paces", _PACES)


def test_a_return_before_the_check_leaves_a_path_unchecked() -> None:
    """A ``return`` that runs before the check, in the function or in a
    helper the choice is handed to, ends the paths that take it with the
    choice unchecked, and so does a ``continue`` of the loop that checks each
    item; one behind a test of the choice itself, one after the check, a
    ``yield`` and a ``break`` of an inner loop leave none.
    """
    some_paths = "checked on some paths only, so a misspelling passes on the others"
    assert _verdict_of(_checked_after_an_early_return, "mode") == some_paths
    assert _verdict_of(_checked_after_a_helper_returns_early, "mode") == some_paths
    assert (
        _verdict_of(_items_skipped_before_the_check, "paces", collection=True)
        == some_paths
    )
    assert _verdict_of(_checked_after_its_own_early_return, "mode") is None
    assert _verdict_of(_checked_before_an_early_return, "mode") is None
    assert _verdict_of(_checked_after_a_yield, "mode") is None
    assert (
        _verdict_of(_items_checked_after_an_inner_loop, "paces", collection=True)
        is None
    )


def _checked_behind_a_test_of_its_text(mode: str) -> str:
    if mode == "fast":
        require_choice(mode, "mode", _PACES)
    return mode


def _checked_behind_a_test_of_its_form_and_more(
    mode: _Pace | None, *, strict: bool
) -> _Pace | None:
    if strict and mode is not None:
        require_choice(mode, "mode", _PACES)
    return mode


def _checked_after_a_misspelling_returns(mode: str) -> str:
    if mode == "typo":
        return "fast"
    require_choice(mode, "mode", _PACES)
    return mode


def _checked_after_an_empty_text_returns(mode: str) -> str:
    if not mode:
        return "fast"
    require_choice(mode, "mode", _PACES)
    return mode


def _checked_after_a_text_matched_returns(mode: str) -> str:
    match mode:
        case "typo":
            return "fast"
    require_choice(mode, "mode", _PACES)
    return mode


def _checked_after_a_listed_option_returns(mode: _Pace) -> int:
    if mode == "fast":
        return 0
    require_choice(mode, "mode", ("slow",))
    return 1


def _checked_but_for_a_listed_option(mode: _Pace) -> _Pace:
    if mode != "fast":
        require_choice(mode, "mode", _PACES)
    return mode


def _checked_in_the_else_of_a_listed_option(mode: _Pace) -> int:
    if mode == "fast":
        column = 0
    else:
        column = 1
        require_choice(mode, "mode", _PACES)
    return column


def _checked_after_listed_options_return(mode: _Pace) -> int:
    if mode in ("fast", "slow"):
        return 0
    require_choice(mode, "mode", _PACES)
    return 1


def _checked_after_none_is_matched(mode: _Pace | None) -> _Pace | None:
    match mode:
        case None:
            return None
    require_choice(mode, "mode", _PACES)
    return mode


def _items_checked_after_an_empty_collection_returns(paces: Sequence[_Pace]) -> None:
    if not paces:
        return
    for pace in paces:
        require_choice(pace, "paces", _PACES)


def test_only_a_test_of_its_form_or_of_a_listed_option_keeps_every_path() -> None:
    """A check behind a test of the text, or one a misspelling can return
    before, leaves a misspelling unchecked on the other path: ``if mode ==
    "fast": require_choice(...)``, ``if mode == "typo": return``, ``if not
    mode: return`` (an empty text is not an option), ``case "typo": return``
    and ``if strict and mode is not None`` (a test that asks something
    besides the form). A test of the form (``is None``, the emptiness of a
    collection, ``case None``) keeps every path, and so does one that skips
    the check only for an option the ``Literal`` lists (``if method ==
    "vdi2081": return ...``), in either branch.
    """
    some_paths = "checked on some paths only, so a misspelling passes on the others"
    paces = frozenset(_PACES)
    for leaky in (
        _checked_behind_a_test_of_its_text,
        _checked_behind_a_test_of_its_form_and_more,
        _checked_after_a_misspelling_returns,
        _checked_after_an_empty_text_returns,
        _checked_after_a_text_matched_returns,
    ):
        assert _verdict_of(leaky, "mode", options=paces) == some_paths, leaky
    for tight in (
        _checked_after_a_listed_option_returns,
        _checked_but_for_a_listed_option,
        _checked_in_the_else_of_a_listed_option,
        _checked_after_listed_options_return,
        _checked_after_none_is_matched,
    ):
        assert _verdict_of(tight, "mode", options=paces) is None, tight
    assert (
        _verdict_of(
            _items_checked_after_an_empty_collection_returns,
            "paces",
            collection=True,
            options=paces,
        )
        is None
    )
    # An option is known only from the Literal: without it, the return
    # before the check is a path a misspelling could take.
    assert _verdict_of(_checked_after_a_listed_option_returns, "mode") == some_paths


def _rows_once_each(paces: Sequence[_Pace]) -> tuple[_Pace, ...]:
    rows = tuple(dict.fromkeys(paces))
    for row in rows:
        require_choice(row, "paces", _PACES)
    return rows


def _one_or_several_paces(paces: _Pace | Sequence[_Pace]) -> list[_Pace]:
    chosen = (paces,) if isinstance(paces, str) else tuple(paces)
    return [require_choice(pace, "paces", _PACES) for pace in chosen]


def _keys_of_a_copy(levels: Mapping[_Pace, float]) -> None:
    given: Mapping[_Pace, float] = dict(levels.items())
    for key in given:
        require_choice(key, "levels", _PACES)


def _a_copy_left_unchecked(levels: Mapping[_Pace, float]) -> None:
    given = dict(levels.items())
    if not given:
        raise ValueError(levels)


def test_a_check_of_a_copy_of_the_items_is_a_check_of_the_items() -> None:
    """``tuple(dict.fromkeys(x))``, ``(x,) if isinstance(x, str) else
    tuple(x)`` and ``dict(x.items())`` hold the caller's items, so a check
    of each item of the copy checks each item of the choice; a copy nobody
    checks leaves the choice unchecked.
    """
    assert _verdict_of(_rows_once_each, "paces", collection=True) is None
    assert _verdict_of(_one_or_several_paces, "paces", collection=True) is None
    assert _verdict_of(_keys_of_a_copy, "levels", collection=True) is None
    assert _verdict_of(_a_copy_left_unchecked, "levels", collection=True) == (
        "never checked, so a misspelling passes"
    )


@dataclass(frozen=True)
class _Strides:
    """A record that checks each of its choices when it is built."""

    paces: tuple[_Pace, ...]

    def __post_init__(self) -> None:
        for pace in self.paces:
            require_choice(pace, "paces", _PACES)

    @classmethod
    def of(cls, paces: Sequence[_Pace]) -> _Strides:
        return cls(paces=tuple(paces))


def test_a_choice_handed_to_the_record_a_classmethod_builds_is_checked_there() -> None:
    """``cls(paces=tuple(paces))`` is followed into the record's
    ``__post_init__``, where each item is checked.
    """
    assert _verdict_of(_Strides.of, "paces", collection=True) is None


@dataclass(frozen=True)
class _CheckedPaceLimits:
    """A record that checks each key of its limits when it is built."""

    limits: Mapping[_Pace, float]

    def __post_init__(self) -> None:
        for pace in self.limits:
            require_choice(pace, "limits", _PACES)


@dataclass(frozen=True)
class _UncheckedPaceLimits:
    """A record that keeps its limits as they come."""

    limits: Mapping[_Pace, float]


def _limits_rebuilt(limits: Mapping[_Pace, float]) -> _CheckedPaceLimits:
    return _CheckedPaceLimits(
        limits={pace: float(value) for pace, value in limits.items()}
    )


def _limits_rebuilt_unchecked(limits: Mapping[_Pace, float]) -> _UncheckedPaceLimits:
    return _UncheckedPaceLimits(
        limits={pace: abs(value) for pace, value in limits.items()}
    )


def test_a_dict_comprehension_that_keeps_the_keys_hands_them_on() -> None:
    """``{pace: float(value) for pace, value in limits.items()}`` gives each
    key a new value and keeps the key, so the record that checks its keys
    checks the caller's; a record that checks nothing leaves them unchecked.
    """
    assert _verdict_of(_limits_rebuilt, "limits", collection=True) is None
    assert _verdict_of(_limits_rebuilt_unchecked, "limits", collection=True) == (
        "never checked, so a misspelling passes"
    )


def _limits_kept_if_listed(limits: Mapping[_Pace, float]) -> _CheckedPaceLimits:
    return _CheckedPaceLimits(
        limits={pace: float(value) for pace, value in limits.items() if pace in _PACES}
    )


def _limits_kept_if_set(limits: Mapping[_Pace, float]) -> _CheckedPaceLimits:
    return _CheckedPaceLimits(
        limits={pace: float(value) for pace, value in limits.items() if value}
    )


def _limits_kept_if_set_then_checked(limits: Mapping[_Pace, float]) -> None:
    kept = {pace: value for pace, value in limits.items() if value}
    for key in kept:
        require_choice(key, "limits", _PACES)


def _limits_kept_but_one_option(limits: Mapping[_Pace, float]) -> _CheckedPaceLimits:
    return _CheckedPaceLimits(
        limits={pace: float(value) for pace, value in limits.items() if pace != "fast"}
    )


def test_a_dict_comprehension_that_drops_keys_hands_on_only_the_kept_ones() -> None:
    """A filter drops the keys it fails for before any check sees them, so a
    misspelling the filter drops passes unchecked, handed on or held in a
    local: ``if pace in _PACES`` drops it silently and ``if value`` drops any
    key whose value is zero. A filter that drops only an option the
    ``Literal`` lists (``if pace != "fast"``) drops no misspelling.
    """
    never = "never checked, so a misspelling passes"
    assert _verdict_of(_limits_kept_if_listed, "limits", collection=True) == never
    assert _verdict_of(_limits_kept_if_set, "limits", collection=True) == never
    assert (
        _verdict_of(_limits_kept_if_set_then_checked, "limits", collection=True)
        == never
    )
    assert (
        _verdict_of(
            _limits_kept_but_one_option, "limits", collection=True, options=_PACES
        )
        is None
    )


def _paces_checked_in_a_comprehension(paces: Sequence[_Pace]) -> list[_Pace]:
    return [require_choice(pace, "paces", _PACES) for pace in paces]


def _paces_checked_where_a_filter_holds(paces: Sequence[_Pace]) -> list[_Pace]:
    return [require_choice(pace, "paces", _PACES) for pace in paces if pace]


def _paces_checked_but_one_option(paces: Sequence[_Pace]) -> list[_Pace]:
    return [require_choice(pace, "paces", _PACES) for pace in paces if pace != "fast"]


def _pace_checked_per_step(pace: _Pace, steps: int) -> list[_Pace]:
    return [require_choice(pace, "pace", _PACES) for _ in range(steps)]


def test_a_check_in_a_comprehension_runs_only_where_its_clauses_let_it() -> None:
    """A check in the element of a comprehension runs once for each item its
    filters keep, so a filter that drops a text the ``Literal`` does not list
    (``if pace`` drops ``""``) leaves it unchecked, as a ``continue`` would; a
    comprehension over something else than the choice runs it only when that
    holds an item, as a ``for`` loop does. A comprehension over the choice
    itself, and a filter that drops only a listed option, leave none.
    """
    some_paths = "checked on some paths only, so a misspelling passes on the others"
    assert (
        _verdict_of(_paces_checked_in_a_comprehension, "paces", collection=True) is None
    )
    assert (
        _verdict_of(
            _paces_checked_where_a_filter_holds,
            "paces",
            collection=True,
            options=_PACES,
        )
        == some_paths
    )
    assert (
        _verdict_of(
            _paces_checked_but_one_option, "paces", collection=True, options=_PACES
        )
        is None
    )
    assert _verdict_of(_pace_checked_per_step, "pace") == some_paths


def _pace_checked_in_a_later_link(pace: _Pace, low: int) -> bool:
    return 0 < low < len(require_choice(pace, "pace", _PACES))


def _pace_checked_in_the_first_link(pace: _Pace, high: int) -> bool:
    return len(require_choice(pace, "pace", _PACES)) < high < 10  # noqa: PLR2004


def _pace_checked_in_an_assert(pace: _Pace) -> _Pace:
    assert require_choice(pace, "pace", _PACES)
    return pace


def _paces_checked_in_a_generator_left_undrawn(
    paces: Sequence[_Pace],
) -> Sequence[_Pace]:
    checks = (require_choice(pace, "paces", _PACES) for pace in paces)
    del checks
    return paces


def _paces_checked_in_a_generator_drawn_whole(
    paces: Sequence[_Pace],
) -> tuple[_Pace, ...]:
    return tuple(require_choice(pace, "paces", _PACES) for pace in paces)


def test_a_check_that_may_be_skipped_checks_on_some_paths_only() -> None:
    """A check in a later link of a chained comparison runs only when the
    links before it hold, ``python -O`` leaves one in an ``assert`` out, and
    one in a generator runs only as far as something draws from it; one in
    the first link, or in a generator a call draws whole, always runs.
    """
    some_paths = "checked on some paths only, so a misspelling passes on the others"
    assert _verdict_of(_pace_checked_in_a_later_link, "pace") == some_paths
    assert _verdict_of(_pace_checked_in_the_first_link, "pace") is None
    assert _verdict_of(_pace_checked_in_an_assert, "pace") == some_paths
    assert (
        _verdict_of(
            _paces_checked_in_a_generator_left_undrawn, "paces", collection=True
        )
        == some_paths
    )
    assert (
        _verdict_of(_paces_checked_in_a_generator_drawn_whole, "paces", collection=True)
        is None
    )


_TERMINATIONS = (
    "Literal['fast', 'slow'] | Mapping[Literal['left', 'right'], "
    "Literal['fast', 'slow'] | float]"
)
_TWO_SIDES = ("left", "right")


@dataclass(frozen=True)
class _Terminations:
    """A record that checks a single pace, each side and each pace it maps to."""

    sides: _Pace | Mapping[_Side, _Pace | float]

    def __post_init__(self) -> None:
        if isinstance(self.sides, Mapping):
            for side, value in self.sides.items():
                require_choice(side, "sides", _TWO_SIDES)
                if isinstance(value, str):
                    require_choice(value, "sides", _PACES)
        else:
            require_choice(self.sides, "sides", _PACES)


@dataclass(frozen=True)
class _KeysUnchecked:
    """A record that checks its single pace and the paces it maps to, not the sides."""

    sides: _Pace | Mapping[_Side, _Pace | float]

    def __post_init__(self) -> None:
        if isinstance(self.sides, Mapping):
            for value in self.sides.values():
                if isinstance(value, str):
                    require_choice(value, "sides", _PACES)
        else:
            require_choice(self.sides, "sides", _PACES)


@dataclass(frozen=True)
class _ValuesUnchecked:
    """A record that checks its single pace and its sides, not the paces they map to."""

    sides: _Pace | Mapping[_Side, _Pace | float]

    def __post_init__(self) -> None:
        if isinstance(self.sides, Mapping):
            for side in self.sides:
                require_choice(side, "sides", _TWO_SIDES)
        else:
            require_choice(self.sides, "sides", _PACES)


@dataclass(frozen=True)
class _SingleUnchecked:
    """A record that checks every side and pace of a mapping, and no single pace."""

    sides: _Pace | Mapping[_Side, _Pace | float]

    def __post_init__(self) -> None:
        if isinstance(self.sides, Mapping):
            for side, value in self.sides.items():
                require_choice(side, "sides", _TWO_SIDES)
                if isinstance(value, str):
                    require_choice(value, "sides", _PACES)


@dataclass(frozen=True)
class _KeysSkipAPace:
    """A record that skips a key spelt as a pace before it checks the sides."""

    sides: _Pace | Mapping[_Side, _Pace | float]

    def __post_init__(self) -> None:
        if isinstance(self.sides, Mapping):
            for side, value in self.sides.items():
                if side in {"fast", "slow"}:
                    continue
                require_choice(side, "sides", _TWO_SIDES)
                if isinstance(value, str):
                    require_choice(value, "sides", _PACES)
        else:
            require_choice(self.sides, "sides", _PACES)


@dataclass(frozen=True)
class _Unhooked:
    """A record with no ``__post_init__``: the ``__init__`` written for it
    calls none.
    """

    pace: _Pace = "fast"


class _CheckedTooLate(_Unhooked):
    """A class that is no record over one that has no ``__post_init__``: the
    one it writes never runs.
    """

    def __post_init__(self) -> None:
        require_choice(self.pace, "pace", _PACES)


@dataclass(frozen=True)
class _Hooking:
    """A record whose ``__init__`` calls ``self.__post_init__``."""

    pace: _Pace = "fast"

    def __post_init__(self) -> None:
        pass


class _CheckedInTime(_Hooking):
    """A class that is no record over one whose ``__init__`` calls
    ``self.__post_init__``: its own runs.
    """

    def __post_init__(self) -> None:
        require_choice(self.pace, "pace", _PACES)


@dataclass(frozen=True)
class _Checking:
    """A record whose ``__post_init__`` checks its pace."""

    pace: _Pace = "fast"

    def __post_init__(self) -> None:
        require_choice(self.pace, "pace", _PACES)


@dataclass(frozen=True)
class _Delegating(_Checking):
    """A record whose own ``__init__`` hands its value to the one
    ``@dataclass`` wrote for ``_Checking``, which calls ``__post_init__``.
    """

    def __init__(self, pace: _Pace = "fast") -> None:
        super().__init__(pace)


class _PlainDelegating(_Checking):
    """A class that is no record whose ``__init__`` hands its value on."""

    def __init__(self, pace: _Pace = "fast") -> None:
        super().__init__(pace)


class _NamedDelegating(_Checking):
    """A class whose ``__init__`` calls a base's ``__init__`` by its name."""

    def __init__(self, pace: _Pace = "fast") -> None:
        _Checking.__init__(self, pace)


class _DelegatedTooLate(_Unhooked):
    """A class whose ``__init__`` hands its value to one that calls no
    ``__post_init__``: the one it writes never runs.
    """

    def __init__(self, pace: _Pace = "fast") -> None:
        super().__init__(pace)

    def __post_init__(self) -> None:
        require_choice(self.pace, "pace", _PACES)


class _Unhanded(_Checking):
    """A class whose ``__init__`` stores the value itself and hands nothing
    on: the check of the record under it never runs.
    """

    def __init__(self, pace: _Pace = "fast") -> None:
        object.__setattr__(self, "pace", pace)


def test_a_record_runs_a_post_init_only_when_its_init_calls_one() -> None:
    """The ``__init__`` a call runs, here the one ``@dataclass`` writes for the
    first record of the order, calls ``self.__post_init__`` only when that
    record had one when it was written: ``_CheckedTooLate`` never runs the
    check it writes, so a misspelt pace is never refused, and
    ``_CheckedInTime`` runs its own. One written by hand runs what the
    ``__init__`` it hands its values on to runs, through ``super()`` or by
    the base's name: ``_Delegating`` and its two plain forms run the check
    of ``_Checking``, ``_DelegatedTooLate`` hands them to one that runs
    none, and ``_Unhanded`` hands them to none.

    The first ``__post_init__`` of the order was read as the one that runs,
    so a check that never runs passed the choice as checked; then only an
    ``__init__`` that names ``__post_init__`` itself was read as running
    one, so a choice ``_Delegating`` checks was reported as never checked.
    """
    assert ccl._post_init(_CheckedTooLate) is None
    assert ccl._post_init(_Unhooked) is None
    assert ccl._post_init(_CheckedInTime) is inspect.unwrap(
        vars(_CheckedInTime)["__post_init__"]
    )
    with pytest.raises(ValueError, match="pace"):
        _CheckedInTime("medium")  # type: ignore[arg-type]
    unchecked = _CheckedTooLate("medium")  # type: ignore[arg-type]
    assert vars(unchecked)["pace"] == "medium"
    check = inspect.unwrap(vars(_Checking)["__post_init__"])
    pace = "Literal['fast', 'slow']"
    for runs in (_Delegating, _PlainDelegating, _NamedDelegating):
        found = ccl._post_init(runs)
        assert found is check, runs
        assert ccl._choice_verdict(found, "pace", pace, field=True) is None
        with pytest.raises(ValueError, match="pace"):
            runs("medium")  # type: ignore[arg-type]
    for skipped in (_DelegatedTooLate, _Unhanded):
        assert ccl._post_init(skipped) is None, skipped
        assert vars(skipped("medium"))["pace"] == "medium"  # type: ignore[arg-type]


class _PlainChecking(_Checking):
    """A class that is no record over one whose check runs."""


def _through_plain(pace: _Pace = "fast") -> _PlainChecking:
    """Hand a pace to a class that is no record over one that checks it."""
    return _PlainChecking(pace)


def _through_in_time(pace: _Pace = "fast") -> _CheckedInTime:
    """Hand a pace to a class that is no record and checks it itself."""
    return _CheckedInTime(pace)


def test_a_call_of_a_class_runs_the_init_its_order_gives() -> None:
    """A call of ``_PlainChecking``, which writes no ``__init__``, runs the
    one ``@dataclass`` wrote for ``_Checking``, and that one runs the check:
    the pace it is handed is checked. The hook it calls is the one the class
    called resolves: a call of ``_CheckedInTime`` runs the check it writes,
    not the empty one of ``_Hooking``, whose ``__init__`` it runs.

    The class's own ``__init__`` alone was read, so the call reached no
    constructor and the pace was reported as never checked.
    """
    call = ast.parse("_PlainChecking(pace)", mode="eval").body
    assert isinstance(call, ast.Call)
    namespace: dict[str, object] = {"_PlainChecking": _PlainChecking}
    assert ccl._callee(call, namespace, __name__) is vars(_Checking)["__init__"]
    pace = "Literal['fast', 'slow']"
    for through in (_through_plain, _through_in_time):
        assert ccl._choice_verdict(through, "pace", pace, field=False) is None
        with pytest.raises(ValueError, match="pace"):
            through("medium")  # type: ignore[arg-type]


class _Unchecking:
    """A class whose ``__init__`` checks nothing and hands nothing on."""

    def __init__(self) -> None:
        pass


class _NamedPastAnEarlierBase(_Unchecking, _Checking):
    """A class whose ``__init__`` calls by name the ``__init__`` of a base
    that comes after another base with one of its own in the order.
    """

    def __init__(self, pace: _Pace = "fast") -> None:
        _Checking.__init__(self, pace)


class _SuperPastAnEarlierBase(_Unchecking, _Checking):
    """A class whose ``__init__`` looks the next one up from after the base
    it names, with ``super(_Unchecking, self)``.
    """

    def __init__(self, pace: _Pace = "fast") -> None:
        super(_Unchecking, self).__init__(pace)


class _NamedAnUncheckingBase(_Checking, _Unchecking):
    """A class whose ``__init__`` calls by name the ``__init__`` of a base
    that calls no ``__post_init__``, though the next class of the order has
    one that does.
    """

    def __init__(self, pace: _Pace = "fast") -> None:
        _Unchecking.__init__(self)
        object.__setattr__(self, "pace", pace)


def test_an_init_handed_on_to_runs_the_one_its_call_names() -> None:
    """``_Checking.__init__(self, pace)`` runs the ``__init__`` ``_Checking``
    looks up, the one ``@dataclass`` wrote for it, which runs the check,
    though ``_Unchecking`` comes before it in the order of
    ``_NamedPastAnEarlierBase``; ``super(_Unchecking, self).__init__(pace)``
    runs the first one after ``_Unchecking``, the same. ``_Unchecking.__init__``
    calls none, though the class after ``_NamedAnUncheckingBase`` in its
    order, ``_Checking``, has one that does: its pace is never checked.

    Every ``__init__`` a hand-written one named was read as the one of the
    next class of the order that has one: ``_Unchecking``'s for the first
    two, so a pace they check was reported as never checked, and
    ``_Checking``'s for the third, so a pace it never checks passed.
    """
    check = inspect.unwrap(vars(_Checking)["__post_init__"])
    pace = "Literal['fast', 'slow']"
    for runs in (_NamedPastAnEarlierBase, _SuperPastAnEarlierBase):
        found = ccl._post_init(runs)
        assert found is check, runs
        assert ccl._choice_verdict(found, "pace", pace, field=True) is None
        with pytest.raises(ValueError, match="pace"):
            runs("medium")  # type: ignore[arg-type]
    assert ccl._post_init(_NamedAnUncheckingBase) is None
    assert vars(_NamedAnUncheckingBase("medium"))["pace"] == "medium"  # type: ignore[arg-type]


class _PaceChecker:
    """A class whose methods check the pace they are handed."""

    def check(self, pace: _Pace) -> None:
        require_choice(pace, "pace", _PACES)

    @classmethod
    def check_once(cls, pace: _Pace) -> None:
        require_choice(pace, "pace", _PACES)


class _ThroughTheClass(_PaceChecker):
    """A class that calls its base's methods through the base's name."""

    def run(self, pace: _Pace = "fast") -> None:
        _PaceChecker.check(self, pace)

    def run_once(self, pace: _Pace = "fast") -> None:
        _PaceChecker.check_once(pace)


def _through_a_named_init(pace: _Pace = "fast") -> _NamedPastAnEarlierBase:
    """Hand a pace to a class whose ``__init__`` hands it on by name."""
    return _NamedPastAnEarlierBase(pace)


def test_a_method_called_through_its_class_takes_the_instance_first() -> None:
    """``_PaceChecker.check(self, pace)`` hands ``self`` to the method's
    ``self`` and the pace to its ``pace``, which it checks, as
    ``_Checking.__init__(self, pace)`` hands the pace to the record's field;
    a class method called through its class, ``_PaceChecker.check_once(pace)``,
    is bound to it.

    A method's ``self`` was taken as filled by the call whatever named the
    method, so the pace was read as handed to the method's second parameter
    or to none, and reported as never checked.
    """
    pace = "Literal['fast', 'slow']"
    for through in (_ThroughTheClass.run, _ThroughTheClass.run_once):
        assert ccl._choice_verdict(through, "pace", pace, field=False) is None
        instance = _ThroughTheClass()
        with pytest.raises(ValueError, match="pace"):
            through(instance, "medium")  # type: ignore[arg-type]
    assert ccl._choice_verdict(_through_a_named_init, "pace", pace, field=False) is None
    with pytest.raises(ValueError, match="pace"):
        _through_a_named_init("medium")  # type: ignore[arg-type]


def _check_after_a_class(cls: object, pace: _Pace) -> None:
    """A function whose first parameter is called ``cls``: it takes the
    class a caller hands it first, and checks the pace after it.
    """
    require_choice(pace, "pace", _PACES)


def _hands_a_class_then_the_pace(pace: _Pace = "fast") -> None:
    """Hand the function a class, and the pace in its second place."""
    _check_after_a_class(int, pace)


def _hands_the_pace_first(pace: _Pace = "fast") -> None:
    """Hand the function the pace in its first place, where it takes a class."""
    _check_after_a_class(pace, "fast")


class _StaticPaceChecker:
    """A class whose static method takes a class first and checks the pace."""

    @staticmethod
    def check_for(cls: object, pace: _Pace) -> None:
        require_choice(pace, "pace", _PACES)

    def through_the_class(self, pace: _Pace = "fast") -> None:
        _StaticPaceChecker.check_for(type(self), pace)

    def on_self(self, pace: _Pace = "fast") -> None:
        self.check_for(type(self), pace)


def test_a_function_or_static_method_takes_what_it_is_handed_first() -> None:
    """A call fills no parameter of a function, or of a static method, by
    itself, whatever the parameter is called: ``_check_after_a_class(int,
    pace)`` hands ``int`` to ``cls`` and the pace to ``pace``, which it
    checks, and ``_check_after_a_class(pace, "fast")`` hands the pace to
    ``cls``, which nothing checks. ``_StaticPaceChecker.check_for`` takes
    what it is handed through its class and on ``self`` alike.

    A first parameter called ``cls`` or ``self`` was taken as filled by the
    call whatever the callee was, so the first argument was read as the
    pace: the pace a function checks was reported as never checked, and one
    it never checks passed.
    """
    pace = "Literal['fast', 'slow']"
    never = "never checked, so a misspelling passes"
    assert (
        ccl._choice_verdict(_hands_a_class_then_the_pace, "pace", pace, field=False)
        is None
    )
    with pytest.raises(ValueError, match="pace"):
        _hands_a_class_then_the_pace("medium")  # type: ignore[arg-type]
    assert (
        ccl._choice_verdict(_hands_the_pace_first, "pace", pace, field=False) == never
    )
    _hands_the_pace_first("medium")  # type: ignore[arg-type]
    instance = _StaticPaceChecker()
    for through in (_StaticPaceChecker.through_the_class, _StaticPaceChecker.on_self):
        assert ccl._choice_verdict(through, "pace", pace, field=False) is None
        with pytest.raises(ValueError, match="pace"):
            through(instance, "medium")  # type: ignore[arg-type]


#: A module whose function and static method take a class first and check
#: the pace after it, and one that calls them through the module and
#: through a field of ``self``.
_THROUGH_A_MODULE = {
    "_takes_a_class_first": """
        from phonometry._internal.validation import require_choice

        PACES = ("fast", "slow")


        def check_after(cls, pace):
            require_choice(pace, "pace", PACES)


        class StaticChecker:
            @staticmethod
            def check_for(cls, pace):
                require_choice(pace, "pace", PACES)
        """,
    "_hands_through_a_module": """
        from typing import Literal

        from phonometry import _takes_a_class_first as first

        Pace = Literal["fast", "slow"]


        def through_the_module(pace: Pace = "fast") -> None:
            first.check_after(int, pace)


        def the_pace_first(pace: Pace = "fast") -> None:
            first.check_after(pace, "fast")


        class Holder:
            checker: first.StaticChecker

            def __init__(self) -> None:
                self.checker = first.StaticChecker()

            def on_a_field(self, pace: Pace = "fast") -> None:
                self.checker.check_for(int, pace)
        """,
}


def test_a_function_through_its_module_or_a_static_method_on_a_field_takes_it_all(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``first.check_after(int, pace)`` runs a function of the module
    ``first``, which takes ``int`` as its ``cls`` and checks the pace after
    it, and ``self.checker.check_for(int, pace)`` a static method of the
    class the field ``checker`` is annotated with, which takes what it is
    handed the same way; ``first.check_after(pace, "fast")`` checks
    ``"fast"`` and never the pace.

    A call through a module, or on a field of ``self``, was read as filling
    a first parameter called ``cls`` itself whatever it ran, so ``int`` was
    read as the pace: the pace checked was reported as never checked, and
    the one never checked passed.
    """
    _plant_modules(tmp_path, monkeypatch, _THROUGH_A_MODULE)
    module = sys.modules["phonometry._hands_through_a_module"]
    pace = "Literal['fast', 'slow']"
    never = "never checked, so a misspelling passes"
    assert (
        ccl._choice_verdict(module.through_the_module, "pace", pace, field=False)
        is None
    )
    with pytest.raises(ValueError, match="pace"):
        module.through_the_module("medium")
    assert (
        ccl._choice_verdict(module.the_pace_first, "pace", pace, field=False) == never
    )
    module.the_pace_first("medium")
    on_a_field = module.Holder.on_a_field
    assert ccl._choice_verdict(on_a_field, "pace", pace, field=False) is None
    holder = module.Holder()
    with pytest.raises(ValueError, match="pace"):
        holder.on_a_field("medium")


def test_every_part_of_a_choice_of_several_parts_is_checked() -> None:
    """``Pace | Mapping[Side, Pace | float]`` takes a pace as one value, a side
    as each key and a pace as each value: a check of one part says nothing of
    the others, so a record passes only when each part reaches a check, the
    single name, the keys and the values each on every path. Each part is
    read against the options of its own ``Literal``: a key skipped because it
    is spelt as a pace is a misspelt side, not an option of the keys.
    """
    paces, sides = frozenset(_PACES), frozenset(_TWO_SIDES)
    assert ccl._branches(_TERMINATIONS) == {
        ccl._WHOLE: paces,
        ccl._ITEMS: sides,
        ccl._VALUES: paces,
    }
    assert ccl._branches("Literal['fast', 'slow'] | float") == {ccl._WHOLE: paces}

    def verdict(record: type) -> str | None:
        check = ccl._post_init(record)
        assert check is not None
        return ccl._part_verdict(check, "sides", _TERMINATIONS, field=True)

    assert verdict(_Terminations) is None
    assert verdict(_KeysUnchecked) == (
        "each item or key: never checked, so a misspelling passes"
    )
    assert verdict(_ValuesUnchecked) == (
        "each value: never checked, so a misspelling passes"
    )
    assert verdict(_SingleUnchecked) == (
        "the choice itself: never checked, so a misspelling passes"
    )
    skipped = verdict(_KeysSkipAPace)
    assert skipped is not None
    assert skipped.startswith("each item or key: ")
    # Read whole, the value meets no one check on every path, since the test
    # of its form sends each part down a path of its own: the whole reading
    # tells none of the four apart, so a choice of several parts is read
    # part by part, and only the record that checks every part passes.
    some_paths = "checked on some paths only, so a misspelling passes on the others"
    for record in (_Terminations, _KeysUnchecked, _ValuesUnchecked, _SingleUnchecked):
        check = ccl._post_init(record)
        assert check is not None
        assert (
            ccl._verdict(
                ccl._checks_of(check, "sides", field=True, collection=True, depth=0)
            )
            == some_paths
        )
        assert ccl._choice_verdict(check, "sides", _TERMINATIONS, field=True) == (
            verdict(record)
        )


def _one_pace_read_by_letter(paces: _Pace | Sequence[_Pace]) -> tuple[_Pace, ...]:
    given = paces if isinstance(paces, str) else paces
    return tuple(require_choice(pace, "paces", _PACES) for pace in given)


def test_a_single_choice_wrapped_as_one_item_is_checked_with_the_items() -> None:
    """``(paces,) if isinstance(paces, str) else paces`` holds a single pace as
    the one item the loop checks; read letter by letter it is not checked as
    the pace it is.
    """
    annotation = "Literal['fast', 'slow'] | Sequence[Literal['fast', 'slow']]"
    assert (
        ccl._part_verdict(_one_or_several_paces, "paces", annotation, field=False)
        is None
    )
    assert (
        ccl._part_verdict(_one_pace_read_by_letter, "paces", annotation, field=False)
        == "the choice itself: never checked, so a misspelling passes"
    )


#: The annotation of a single pace or a sequence of them.
_ONE_OR_SEVERAL_PACES = "Literal['fast', 'slow'] | Sequence[Literal['fast', 'slow']]"


def _one_or_several_paces_annotated(paces: _Pace | Sequence[_Pace]) -> list[_Pace]:
    chosen: tuple[_Pace, ...] = (paces,) if isinstance(paces, str) else tuple(paces)
    return [require_choice(pace, "paces", _PACES) for pace in chosen]


def test_a_single_choice_wrapped_in_an_annotated_local_is_checked() -> None:
    """``chosen: tuple[Pace, ...] = (paces,) if ...`` binds the one-item tuple
    as ``chosen = (paces,) if ...`` does, so the loop over it checks the
    single pace too.
    """
    assert (
        ccl._part_verdict(
            _one_or_several_paces_annotated,
            "paces",
            _ONE_OR_SEVERAL_PACES,
            field=False,
        )
        is None
    )


def _each_pace_checked(paces: Iterable[str]) -> list[_Pace]:
    return [require_choice(pace, "paces", _PACES) for pace in paces]


def _one_or_several_paces_handed_on(paces: _Pace | Sequence[_Pace]) -> list[_Pace]:
    chosen = (paces,) if isinstance(paces, str) else tuple(paces)
    return _each_pace_checked(chosen)


def _one_pace_handed_on_by_letter(paces: _Pace | Sequence[_Pace]) -> list[_Pace]:
    given = paces if isinstance(paces, str) else paces
    return _each_pace_checked(given)


def test_a_single_choice_wrapped_and_handed_on_is_checked_with_the_items() -> None:
    """A helper handed ``(paces,) if isinstance(paces, str) else tuple(paces)``
    checks each item it receives, the single pace among them; handed the
    pace itself, read letter by letter, it checks no pace.
    """
    assert (
        ccl._part_verdict(
            _one_or_several_paces_handed_on,
            "paces",
            _ONE_OR_SEVERAL_PACES,
            field=False,
        )
        is None
    )
    assert (
        ccl._part_verdict(
            _one_pace_handed_on_by_letter,
            "paces",
            _ONE_OR_SEVERAL_PACES,
            field=False,
        )
        == "the choice itself: never checked, so a misspelling passes"
    )


@dataclass(frozen=True)
class _ReturnsOnAPace:
    """A record that leaves early on a single pace, then checks every part."""

    sides: _Pace | Mapping[_Side, _Pace | float]

    def __post_init__(self) -> None:
        if self.sides == "fast":
            return
        if isinstance(self.sides, Mapping):
            for side, value in self.sides.items():
                require_choice(side, "sides", _TWO_SIDES)
                if isinstance(value, str):
                    require_choice(value, "sides", _PACES)
        else:
            require_choice(self.sides, "sides", _PACES)


def test_a_return_on_a_single_choice_skips_no_key() -> None:
    """``if sides == "fast": return`` leaves with a text, which holds no key
    and no value, so it skips the check of none; a key skipped because it is
    spelt as a pace is still a misspelt side (:class:`_KeysSkipAPace`).
    """
    check = ccl._post_init(_ReturnsOnAPace)
    assert check is not None
    assert ccl._part_verdict(check, "sides", _TERMINATIONS, field=True) is None
    skipping = ccl._post_init(_KeysSkipAPace)
    assert skipping is not None
    skipped = ccl._part_verdict(skipping, "sides", _TERMINATIONS, field=True)
    assert skipped is not None
    assert skipped.startswith("each item or key: ")


@dataclass(frozen=True)
class _MappingLeavesBeforeItsKeys:
    """A record that returns a mapping before the loop that checks its keys."""

    sides: _Pace | Mapping[_Side, _Pace | float]

    def __post_init__(self) -> None:
        if isinstance(self.sides, Mapping):
            for value in self.sides.values():
                if isinstance(value, str):
                    require_choice(value, "sides", _PACES)
            return
        require_choice(self.sides, "sides", _PACES)
        for side in self.sides:
            require_choice(side, "sides", _TWO_SIDES)


def test_a_test_of_the_form_keeps_the_paths_of_the_parts_it_holds() -> None:
    """``if isinstance(sides, Mapping): return`` leaves with no single pace,
    so the pace's check after it runs on every path that holds one, but it
    leaves with every key of the mapping, which the loop after it never
    reads; each part is held to the forms that hold it, the keys to the
    mapping.
    """
    check = ccl._post_init(_MappingLeavesBeforeItsKeys)
    assert check is not None
    assert ccl._part_verdict(check, "sides", _TERMINATIONS, field=True) == (
        "each item or key: checked on some paths only, so a misspelling passes "
        "on the others"
    )
    with pytest.raises(ValueError, match="'sides' must be one of"):
        _MappingLeavesBeforeItsKeys(sides="fsat")  # type: ignore[arg-type]
    # The misspelt side the guard names is built.
    misspelt = _MappingLeavesBeforeItsKeys(sides={"lfet": 1.0})  # type: ignore[dict-item]
    assert "lfet" in misspelt.sides
    assert ccl._forms(_TERMINATIONS, ccl._WHOLE, collection=True) == (str,)
    assert ccl._forms(_TERMINATIONS, ccl._ITEMS, collection=True) == (Mapping,)
    assert ccl._forms(_TERMINATIONS, ccl._VALUES, collection=True) == (Mapping,)
    assert ccl._forms(_ONE_OR_SEVERAL_PACES, None, collection=True) == (
        str,
        Sequence,
    )


def test_every_origin_of_a_collection_has_the_class_a_test_of_the_form_reads() -> None:
    """Each origin the guard reads as a collection or a mapping stands for a
    class an ``isinstance`` test is held to, so a new one cannot fall back to
    a form no test tells apart unnoticed.
    """
    assert set(ccl._ORIGINS) == ccl._COLLECTIONS | ccl._MAPPINGS


def _leaves_with_its_text(mode: _Pace | None) -> _Pace | None:
    if mode is not None:
        return mode
    require_choice(mode, "mode", _PACES)
    return None


def _leaves_on_a_text(mode: _Pace | float) -> _Pace | float:
    if isinstance(mode, str):
        return mode
    require_choice(mode, "mode", _PACES)
    return mode


def _checked_only_when_none(mode: _Pace | None) -> _Pace | None:
    if mode is None:
        require_choice(mode, "mode", _PACES)
    return mode


def _leaves_on_a_matched_text(mode: _Pace | None) -> _Pace | None:
    match mode:
        case str():
            return mode
    require_choice(mode, "mode", _PACES)
    return mode


def _leaves_when_it_holds_items(paces: Sequence[_Pace]) -> Sequence[_Pace]:
    if paces:
        return paces
    for pace in paces:
        require_choice(pace, "paces", _PACES)
    return paces


def _leaves_on_a_number(mode: _Pace | float) -> float:
    if isinstance(mode, float):
        return mode
    require_choice(mode, "mode", _PACES)
    return 0.0


def _leaves_on_anything_but_a_text(mode: _Pace | float) -> _Pace | float:
    if not isinstance(mode, str):
        return mode
    require_choice(mode, "mode", _PACES)
    return mode


def _checked_when_a_text(mode: _Pace | float) -> _Pace | float:
    if isinstance(mode, str):
        require_choice(mode, "mode", _PACES)
    return mode


def _leaves_on_a_matched_number(mode: _Pace | float) -> _Pace | float:
    match mode:
        case float() | None:
            return mode
    require_choice(mode, "mode", _PACES)
    return mode


def test_a_test_of_the_form_keeps_only_the_paths_that_hold_nothing() -> None:
    """The way a test of the form comes out decides: ``if mode is None:
    return`` and ``if not isinstance(mode, str): return`` leave with no text,
    while ``if mode is not None: return``, ``if isinstance(mode, str):
    return``, ``case str(): return`` and ``if paces: return`` leave with what
    the check reads, and ``if mode is None: require_choice(...)`` checks
    only the paths that hold no text.
    """
    some_paths = "checked on some paths only, so a misspelling passes on the others"
    paces = frozenset(_PACES)
    for leaky in (
        _leaves_with_its_text,
        _leaves_on_a_text,
        _checked_only_when_none,
        _leaves_on_a_matched_text,
    ):
        assert _verdict_of(leaky, "mode", options=paces) == some_paths, leaky
    assert (
        _verdict_of(_leaves_when_it_holds_items, "paces", collection=True) == some_paths
    )
    for tight in (
        _checked_after_its_own_early_return,
        _checked_behind_its_own_test,
        _leaves_on_a_number,
        _leaves_on_anything_but_a_text,
        _checked_when_a_text,
        _leaves_on_a_matched_number,
        _checked_after_none_is_matched,
    ):
        assert _verdict_of(tight, "mode", options=paces) is None, tight


def _leaves_untyped_on_anything_but_a_text(mode: _Pace) -> _Pace:
    if not isinstance(mode, str):
        return mode
    require_choice(mode, "mode", _PACES)
    return mode


def _leaves_untyped_on_none(mode: _Pace) -> _Pace | None:
    if mode is None:
        return None
    require_choice(mode, "mode", _PACES)
    return mode


def _leaves_untyped_on_a_matched_number(mode: _Pace) -> _Pace:
    match mode:
        case float() | None:
            return mode
    require_choice(mode, "mode", _PACES)
    return mode


def _checked_untyped_behind_none(mode: _Pace) -> _Pace:
    if mode is not None:
        require_choice(mode, "mode", _PACES)
    return mode


def test_a_choice_of_texts_alone_leaves_through_no_test_of_its_form() -> None:
    """A value that is not a text is refused with ``TypeError`` (rule A45).

    ``if not isinstance(mode, str): return mode`` before the check sends a
    number past it, and so do ``if mode is None: return``, ``case float() |
    None: return`` and a check behind ``if mode is not None``: each value
    that is no text leaves unrefused. That is a path that holds nothing to
    check only when the annotation lists a value that is no text, a number
    or ``None`` beside the ``Literal``; for a ``Literal`` of texts alone it
    is a path that skips the check.
    """
    some_paths = "checked on some paths only, so a misspelling passes on the others"
    texts = 'Literal["fast", "slow"]'
    for leaky in (
        _leaves_untyped_on_anything_but_a_text,
        _leaves_untyped_on_none,
        _leaves_untyped_on_a_matched_number,
        _checked_untyped_behind_none,
    ):
        assert ccl._choice_verdict(leaky, "mode", texts, field=False) == some_paths, (
            leaky
        )
        for beside in (f"{texts} | float", f"{texts} | None"):
            assert ccl._choice_verdict(leaky, "mode", beside, field=False) is None, (
                leaky,
                beside,
            )


class _Gait(enum.Enum):
    """A pace by its member, as ``RailRoughnessClass`` names a roughness."""

    FAST = "fast"
    SLOW = "slow"


def _member_or_checked_text(mode: object) -> str:
    return (
        mode.value if isinstance(mode, _Gait) else require_choice(mode, "mode", _PACES)
    )


def test_a_literal_of_enum_members_lists_a_value_that_is_no_text() -> None:
    """``Literal[_Gait.FAST] | Literal["fast"]`` takes a member of an
    ``Enum`` beside the text, as ``rail_roughness`` takes a
    ``RailRoughnessClass`` member or its letter.

    A member is no text, so the path a test of its form sends it down holds
    nothing ``require_choice`` reads, as the path of a number does beside
    ``Pace | float``. The guard read every ``Literal`` as one of texts alone
    and called that path one that skips the check. A ``Literal`` of texts
    alone keeps its verdict.
    """
    some_paths = "checked on some paths only, so a misspelling passes on the others"
    members = 'Literal[_Gait.FAST, _Gait.SLOW] | Literal["fast", "slow"]'
    assert ccl._lists_nontext(members)
    assert not ccl._lists_nontext('Literal["fast", "slow"]')
    assert (
        ccl._choice_verdict(_member_or_checked_text, "mode", members, field=False)
        is None
    )
    assert (
        ccl._choice_verdict(
            _member_or_checked_text, "mode", 'Literal["fast", "slow"]', field=False
        )
        == some_paths
    )


def _passes_none_by(mode: _Pace | None) -> None:
    if mode is None:
        return
    require_choice(mode, "mode", _PACES)


def _passes_anything_but_a_text_by(mode: object) -> object:
    if not isinstance(mode, str):
        return mode
    return require_choice(mode, "mode", _PACES)


def _hands_on_to_a_none_test(mode: _Pace) -> _Pace:
    _passes_none_by(mode)
    return mode


def _hands_on_to_a_form_test(mode: _Pace) -> _Pace:
    _passes_anything_but_a_text_by(mode)
    return mode


@dataclass(frozen=True)
class _ChecksThroughSelf:
    """A record whose ``__post_init__`` checks its pace in a method of its own,
    which leaves on ``None`` before the check.
    """

    mode: _Pace

    def __post_init__(self) -> None:
        self._check()

    def _check(self) -> None:
        if self.mode is None:
            return
        require_choice(self.mode, "mode", _PACES)


def test_a_choice_handed_on_whole_keeps_what_its_annotation_lists() -> None:
    """The helper a choice is handed to whole, and the method of the record
    that reads it back through ``self``, test its form as the caller's
    annotation lists it.

    ``if mode is None: return`` in the helper holds nothing to check only
    when the caller's annotation lists ``None``; for a ``Literal`` of texts
    alone it is a path that skips the check, so ``None`` leaves unrefused.
    The guard read the helper as if its caller had listed a value that is
    no text, and passed both.
    """
    some_paths = "checked on some paths only, so a misspelling passes on the others"
    texts = 'Literal["fast", "slow"]'
    for handing in (_hands_on_to_a_none_test, _hands_on_to_a_form_test):
        assert ccl._choice_verdict(handing, "mode", texts, field=False) == some_paths, (
            handing
        )
        for beside in (f"{texts} | float", f"{texts} | None"):
            assert ccl._choice_verdict(handing, "mode", beside, field=False) is None, (
                handing,
                beside,
            )
    check = ccl._post_init(_ChecksThroughSelf)
    assert check is not None
    assert ccl._choice_verdict(check, "mode", texts, field=True) == some_paths
    assert ccl._choice_verdict(check, "mode", f"{texts} | None", field=True) is None


def _a_method_namesake(mode: _Pace, checker: object) -> _Pace:
    checker.require_choice(mode, "mode", _PACES)  # type: ignore[attr-defined]
    return mode


def _an_imported_namesake(mode: _Pace) -> _Pace:
    from operator import truth as require_choice

    require_choice(mode)
    return mode


def _a_parameter_namesake(
    mode: _Pace, require_choice: Callable[..., object] = print
) -> _Pace:
    require_choice(mode, "mode", _PACES)
    return mode


def test_a_check_is_known_by_the_function_it_is_not_by_its_name() -> None:
    """A call counts as the shared check only when its name reaches it.

    A method of another object called ``require_choice``, a function
    imported under that name and a parameter of it check nothing, and the
    guard counted each as the check because of the last part of its name.
    """
    texts = 'Literal["fast", "slow"]'
    for namesake in (_a_method_namesake, _an_imported_namesake, _a_parameter_namesake):
        assert ccl._choice_verdict(namesake, "mode", texts, field=False) is not None, (
            namesake
        )
    assert ccl._choice_verdict(_validated, "mode", texts, field=False) is None


def _checked_beside_a_comprehension_namesake(mode: _Pace) -> str:
    require_choice(mode, "mode", _PACES)
    return [require_choice.lower() for require_choice in (mode,)][0]


def _checked_beside_a_nested_namesake(mode: _Pace) -> _Pace:
    require_choice(mode, "mode", _PACES)

    def inner() -> None:
        require_choice = print
        require_choice()

    inner()
    return mode


def _checked_beside_a_lambda_namesake(mode: _Pace) -> _Pace:
    require_choice(mode, "mode", _PACES)
    # ``:=`` in a lambda binds the name in the lambda's own scope, a local
    # nothing reads, which is the namesake this test needs.
    return (lambda: (require_choice := mode))()  # noqa: F841


def _checked_beside_a_nested_import(mode: _Pace) -> _Pace:
    def inner() -> None:
        from operator import truth as require_choice

        require_choice(1)

    require_choice(mode, "mode", _PACES)
    inner()
    return mode


def test_a_name_a_scope_inside_the_function_binds_hides_no_check() -> None:
    """A name bound inside a comprehension, a nested function or a lambda is theirs.

    The names the function binds itself were read from every node of it, so
    a comprehension's loop target, or a name a nested function or a lambda
    binds for itself, hid the genuine ``require_choice`` call beside it,
    and the checked choice was refused as never checked. So did a nested
    function that imports a namesake: its imports were read as the
    function's own.
    """
    texts = 'Literal["fast", "slow"]'
    for checked in (
        _checked_beside_a_comprehension_namesake,
        _checked_beside_a_nested_namesake,
        _checked_beside_a_lambda_namesake,
        _checked_beside_a_nested_import,
    ):
        assert ccl._choice_verdict(checked, "mode", texts, field=False) is None, checked


def _checked_through_a_module_imported_as(mode: _Pace) -> _Pace:
    import phonometry._internal.validation as checks

    checks.require_choice(mode, "mode", _PACES)
    return mode


def _checked_through_a_module_imported_whole(mode: _Pace) -> _Pace:
    import phonometry._internal.validation

    phonometry._internal.validation.require_choice(mode, "mode", _PACES)
    return mode


def test_a_check_reached_through_a_plain_import_is_a_check() -> None:
    """``import a.b as c`` inside the function binds ``c`` to the module, and
    ``import a.b`` binds ``a``: a call of the check through either is the
    check.

    The function's own imports were read from its ``from ... import``
    statements alone, so ``checks.require_choice(...)`` reached no function
    and the checked choice was refused as never checked; before the check
    was known by the function its name reaches, it passed by its name.
    """
    texts = 'Literal["fast", "slow"]'
    for checked in (
        _checked_through_a_module_imported_as,
        _checked_through_a_module_imported_whole,
    ):
        assert ccl._choice_verdict(checked, "mode", texts, field=False) is None, checked


def _checked_before_a_namesake_is_imported(mode: _Pace, *, again: bool) -> _Pace:
    from phonometry._internal.validation import require_choice

    checked = require_choice(mode, "mode", _PACES)
    if again:
        from operator import truth as require_choice

        require_choice(checked)
    return checked


def _checked_after_a_namesake_is_imported(mode: _Pace) -> _Pace:
    from operator import truth as require_choice

    require_choice(mode)
    from phonometry._internal.validation import require_choice

    return require_choice(mode, "mode", _PACES)


def test_a_check_is_read_through_the_import_that_stands_for_it_at_the_call() -> None:
    """Of two imports of one name in a function, a call reads the one it runs after.

    The imports of the function were read into one table, in no order of
    the source, so the namesake imported in the other branch, or before
    the check, stood for the check's name at every call, and the checked
    choice was refused as never checked.
    """
    texts = 'Literal["fast", "slow"]'
    for checked in (
        _checked_before_a_namesake_is_imported,
        _checked_after_a_namesake_is_imported,
    ):
        assert ccl._choice_verdict(checked, "mode", texts, field=False) is None, checked


def _handed_to_a_namesake_method(mode: str, registry: object) -> str:
    registry.require_choice(mode, "mode", _PACES)  # type: ignore[attr-defined]
    return mode


def _handed_to_the_check_by_another_name(mode: str) -> str:
    from phonometry._internal.validation import require_choice as pick

    return pick(mode, "mode", _PACES)


def test_a_text_is_a_closed_choice_by_the_check_its_call_reaches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``str`` parameter is a closed choice, typed ``str`` against the rule,
    when a shared check reaches it, read by the function its call reaches.

    ``registry.require_choice(mode, ...)`` calls a method of another object
    that only shares the name, and says nothing of ``mode``; the guard read
    the name alone and refused the parameter as a closed choice typed
    ``str``. The shared check called by another name still makes one.
    """
    functions = (_handed_to_a_namesake_method, _handed_to_the_check_by_another_name)
    monkeypatch.setattr(
        ccl,
        "_targets",
        lambda: iter(
            [(__name__, function.__qualname__, function) for function in functions]
        ),
    )
    evidence = {
        choice.qualname: choice.evidence
        for choice in ccl.string_choices()
        if choice.name == "mode"
    }
    assert evidence["_handed_to_a_namesake_method"] == ()
    assert evidence["_handed_to_the_check_by_another_name"]


def _spreads_annotated(x: list[float], mode: str) -> object:
    options: dict[str, str] = {"mode": mode}
    return time_weighting(x, 48000, **options)  # type: ignore[call-overload]


def _set_difference_annotated(sides: Sequence[str]) -> None:
    unknown: set[str] = set(sides) - set(_SIDES)
    if unknown:
        raise ValueError(sorted(unknown))


def _field_of_an_annotated_local(pace: _Pace) -> str:
    held: _Checked = _Checked(pace=pace)
    return held.pace


def test_an_annotated_local_is_read_as_a_plain_one() -> None:
    """``name: T = value`` binds *name* to *value* as ``name = value`` does: a
    dict spread into a call, what a collection holds beyond its options and a
    record a field is read off are read through either.
    """
    assert ccl.passed_on_evidence(_spreads_annotated, "mode") == [
        "handed to time_weighting(mode)"
    ]
    constants = ccl._module_constants(sys.modules[__name__])
    for function in (_set_difference, _set_difference_annotated):
        unlisted = ccl._unlisted_items(
            _tree(function), ccl._the_name("sides"), constants
        )
        assert list(unlisted) == ["unknown"], function.__name__
    tree = _tree(_field_of_an_annotated_local)
    assert isinstance(tree, ast.Module)
    reader = tree.body[0]
    read = next(
        node
        for node in ast.walk(reader)
        if isinstance(node, ast.Attribute) and node.attr == "pace"
    )
    assert ccl._attribute_source(read, reader, __name__) == ccl._Source(
        "literal", frozenset(_PACES)
    )


def test_a_stale_unchecked_entry_fails_and_a_needed_one_does_not(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An entry of ``UNCHECKED`` the walk still finds is kept; one it no
    longer finds is stale. The walk hands back every unchecked choice, the
    exempt ones too, so a needed entry is never mistaken for a stale one.
    """
    needed = ("phonometry.synthetic", "_never_checked", "mode")
    gone = ("phonometry.nowhere", "gone", "mode")
    monkeypatch.setitem(ccl.UNCHECKED, needed, "a reason that still applies")
    monkeypatch.setitem(ccl.UNCHECKED, gone, "a reason that no longer applies")
    walk = [ccl.Choice(*needed, "_Pace", ("never checked",))]
    stale = ccl._stale_unchecked(walk)
    assert needed not in stale
    assert gone in stale


@pytest.mark.whole_tree
def test_every_literal_choice_is_checked_on_every_path() -> None:
    """The package passes: every public ``Literal`` choice and every one a
    record a caller builds holds reaches a shared validator on every path,
    and no entry of ``UNCHECKED`` is stale (rule A45).
    """
    every = list(ccl.unchecked_choices())
    assert [
        choice
        for choice in every
        if (choice.module, choice.qualname, choice.name) not in ccl.UNCHECKED
    ] == []
    assert ccl._stale_unchecked(every) == []


#: A table of this module keyed by the options of ``_Pace`` but typed ``str``.
_PACE_LIMITS_TEXT: dict[str, float] = {"fast": 0.125, "slow": 1.0}
#: The same table keyed by the vocabulary.
_PACE_LIMITS: dict[_Pace, float] = {"fast": 0.125, "slow": 1.0}


def test_a_table_keyed_by_any_text_whose_keys_are_a_vocabulary_is_found() -> None:
    """A ``dict[str, ...]`` whose keys are the options of a ``Literal`` of its
    module is the vocabulary written twice; keyed by the ``Literal`` it is not.
    """
    text = list(
        ccl._keyed_by_text(
            _PACE_LIMITS_TEXT,
            ccl._annotation_node("dict[str, float]"),
            __name__,
            "",
            0,
        )
    )
    typed = list(
        ccl._keyed_by_text(
            _PACE_LIMITS,
            ccl._annotation_node("dict[_Pace, float]"),
            __name__,
            "",
            0,
        )
    )
    assert text == [("", frozenset({"fast", "slow"}))]
    assert typed == []


#: A table annotation spelled through an alias of this module.
_PaceTable = dict[str, float]


@dataclass(frozen=True)
class _PaceLimits:
    """A published record whose table field is keyed by any text."""

    limits: dict[str, float]


def _found(value: object, annotation: str | None) -> list[tuple[str, frozenset[str]]]:
    return list(
        ccl._keyed_by_text(
            value, ccl._annotation_node(annotation, __name__), __name__, "", 0
        )
    )


def test_a_table_is_read_through_its_alias_and_its_qualifier() -> None:
    """An alias of the module, ``Final`` around the type and a ``Sequence``
    of texts let any text in as surely as ``dict[str, ...]`` written out.
    """
    paces = frozenset({"fast", "slow"})
    assert _found(_PACE_LIMITS_TEXT, "_PaceTable") == [("", paces)]
    assert _found(_PACE_LIMITS_TEXT, "Final[dict[str, float]]") == [("", paces)]
    assert _found(_PACE_LIMITS, "Final[dict[_Pace, float]]") == []
    assert _found(_PACES, "Sequence[str]") == [("", paces)]
    assert _found(_PACES, "Final[tuple[str, ...]]") == [("", paces)]
    assert _found(_PACES, "Sequence[_Pace]") == []
    # An annotation that says nothing of the keys lets any text in.
    assert _found(_PACE_LIMITS_TEXT, "Any") == [("", paces)]


def test_each_part_of_a_tuple_key_and_each_field_of_a_record_is_read() -> None:
    """The parts of a key ``("fast", "dry")`` are a vocabulary each, and a
    published record's table fields are read through the record's own
    annotations.
    """
    table = {("fast", "dry"): 1.0, ("slow", "wet"): 2.0}
    assert _found(table, "dict[tuple[str, str], float]") == [
        ("[key]<0>", frozenset({"fast", "slow"})),
        ("[key]<1>", frozenset({"dry", "wet"})),
    ]
    assert _found(table, "dict[tuple[_Pace, str], float]") == [
        ("[key]<1>", frozenset({"dry", "wet"}))
    ]
    assert _found(_PaceLimits(limits=dict(_PACE_LIMITS_TEXT)), None) == [
        (".limits", frozenset({"fast", "slow"}))
    ]


def _pace_of(*, quick: bool) -> _Pace:
    return "fast" if quick else "slow"


def _pace_and_count(*, quick: bool) -> tuple[_Pace, int]:
    return _pace_of(quick=quick), 1


def _text_of(*, quick: bool) -> str:
    return "fast" if quick else "any text"


@dataclass(frozen=True)
class _Stride:
    """A record whose field is typed with the vocabulary."""

    pace: _Pace


def _filled_from_returns(*, quick: bool) -> tuple[object, ...]:
    def _stride() -> _Stride:
        return _Stride(pace=_pace_of(quick=quick))

    unpacked, _count = _pace_and_count(quick=quick)
    stride = _stride()
    return (_pace_of(quick=quick), unpacked, stride.pace, _text_of(quick=quick))


def test_a_value_handed_back_by_a_function_typed_with_a_literal_is_closed() -> None:
    """Guard (c) reads what fills a record field back to where it is written:
    a call to a function annotated to return a ``Literal``, an item unpacked
    from a ``tuple[...]`` such a helper returns, and a field of the record a
    nested function returns are the vocabulary; a function annotated ``str``
    hands back any text.
    """
    tree = _tree(_filled_from_returns)
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_filled_from_returns"
    )
    returned = next(
        node.value for node in ast.walk(function) if isinstance(node, ast.Return)
    )
    assert isinstance(returned, ast.Tuple)
    sources = [ccl._source(item, function, __name__, 0) for item in returned.elts]
    paces = frozenset({"fast", "slow"})
    assert sources[:3] == [ccl._Source("literal", paces)] * 3
    assert sources[3] == ccl._OPEN_SOURCE


def test_a_stale_open_table_entry_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exemption for a table the walk no longer flags cannot outlive its reason."""
    key = ("phonometry.nowhere", "GONE")
    monkeypatch.setitem(ccl.OPEN_TABLES, key, "a reason that no longer applies")
    needed = ("phonometry.synthetic", "TABLE")
    monkeypatch.setitem(ccl.OPEN_TABLES, needed, "a reason that still applies")
    walk = [ccl.Choice(*needed, "keys", "dict[str, float]", ("its keys",))]
    stale = ccl._stale_tables(walk)
    assert key in stale
    assert needed not in stale


@pytest.mark.whole_tree
def test_every_published_table_of_a_vocabulary_is_keyed_by_it() -> None:
    """The package passes: no published table keyed by any text holds the
    options of a vocabulary, and no entry of ``OPEN_TABLES`` is stale (rule A21).
    """
    tables = list(ccl.vocabulary_tables())
    assert [
        table
        for table in tables
        if (table.module, table.qualname) not in ccl.OPEN_TABLES
    ] == []
    assert ccl._stale_tables(tables) == []


def test_an_alias_or_import_in_any_block_at_the_top_is_the_module_s() -> None:
    """A ``match``, a ``try`` with ``except*``, a ``with`` and a loop run at
    import time; the statements of each of their blocks are the module's.

    Only the blocks of an ``if`` were read, so an alias or an import written
    in any other block was no alias of the module.
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
        """
    )
    statements = {
        ast.unparse(node) for node in ccl._module_statements(ast.parse(source).body)
    }
    assert {
        "IN_CASE = 0",
        "IN_CASE = 1",
        "IN_TRY = 1",
        "IN_WITH = 1",
        "IN_LOOP = 1",
        "from json import JSONEncoder as in_loop",
    } <= statements


def _a_kind_beside_a_comprehension(rows: list[str]) -> tuple[str, list[str]]:
    kind = "fast"
    names = [kind.upper() for kind in rows]
    return kind, names


def _a_kind_inside_a_comprehension(rows: list[str]) -> tuple[list[str], str]:
    kind = "fast"
    return [kind for kind in ("up", "down") if rows], kind


def _returned_items(tree: ast.AST) -> list[ast.expr]:
    returned = next(
        node.value for node in ast.walk(tree) if isinstance(node, ast.Return)
    )
    assert returned is not None
    return list(returned.elts) if isinstance(returned, ast.Tuple) else [returned]


def test_a_comprehension_s_variable_is_no_name_of_the_function_around_it() -> None:
    """Rule A21 reads what fills a record's text back to where it is bound:
    a comprehension's variable joined the function's name of the same
    spelling, so a kind always bound to one closed text read as open, and
    the field it fills escaped the rule. Inside the comprehension the name
    stands for the items it walks.
    """
    tree = _tree(_a_kind_beside_a_comprehension)
    function = ccl._function_in(tree)
    kind, _names = _returned_items(tree)
    assert ccl._source(kind, function, __name__, 0) == ccl._Source(
        "texts", frozenset({"fast"})
    )
    tree = _tree(_a_kind_inside_a_comprehension)
    function = ccl._function_in(tree)
    listed, kind = _returned_items(tree)
    assert isinstance(listed, ast.ListComp)
    assert ccl._source(listed.elt, function, __name__, 0) == ccl._Source(
        "texts", frozenset({"up", "down"})
    )
    assert ccl._source(kind, function, __name__, 0) == ccl._Source(
        "texts", frozenset({"fast"})
    )


def _a_mode_shadowed_by_a_comprehension(mode: str, rows: list[str]) -> int:
    return len([row for mode in rows for row in mode if mode == "fast"])


def _a_mode_shadowed_by_a_nested_parameter(mode: str) -> bool:
    def judge(mode: str) -> bool:
        return mode == "fast"

    return judge(mode.upper())


def _a_clean_up_shadowed_in_a_nested_function(mode: str) -> int:
    low = mode.lower()

    def judge(low: str) -> bool:
        return low == "fast"

    return len(low) + judge("x")


def _items_beside_a_comprehension(sides: Sequence[str], other: list[str]) -> int:
    for side in sides:
        print(side)
    return len([side for side in other if side == "top"])


def _values_beside_a_comprehension(levels: Mapping[str, str], other: list[str]) -> int:
    for value in levels.values():
        print(value)
    return len([value for value in other if value == "top"])


def _a_table_shadowed_by_a_comprehension(
    sides: Sequence[str], groups: list[list[str]]
) -> int:
    table = _SIDES
    return len([side for table in groups for side in sides if side in table]) + len(
        table
    )


@pytest.mark.parametrize(
    ("function", "name", "collection"),
    [
        (_a_table_shadowed_by_a_comprehension, "sides", True),
        (_a_mode_shadowed_by_a_comprehension, "mode", False),
        (_a_mode_shadowed_by_a_nested_parameter, "mode", False),
        (_a_clean_up_shadowed_in_a_nested_function, "mode", False),
        (_items_beside_a_comprehension, "sides", True),
    ],
)
def test_a_name_another_scope_binds_tells_nothing_of_the_parameter(
    function: Callable[..., object], name: str, *, collection: bool
) -> None:
    """A comprehension's variable, a nested function's parameter, or a loop's
    item of the same spelling as the parameter, a clean-up of it or one of
    its items, was read as that name, so a test of it against a text was
    taken for a test of the parameter.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    tree = _tree(function)
    found = ccl.code_evidence(
        tree,
        ccl._the_name(name, tree),
        constants,
        collection=collection,
        module_name=__name__,
    )
    assert found == []


def test_a_value_another_scope_binds_tells_nothing_of_the_mapping() -> None:
    """Each value of a mapping is read under its loop's name only where the
    loop binds it, not under a comprehension's variable of that spelling.
    """
    tree = _tree(_values_beside_a_comprehension)
    target = ccl._the_name("levels")
    assert ccl._value_names(tree, target) == {
        ("value", ccl._function_in(tree)),
    }


class _ReceiverNamedOtherwise:
    """A class whose ``__init__`` calls its receiver ``instance``."""

    def __init__(instance, pace: _Pace = "fast") -> None:  # noqa: N805
        require_choice(pace, "pace", _PACES)
        instance.pace = pace


def _through_a_receiver_named_otherwise(
    pace: _Pace = "fast",
) -> _ReceiverNamedOtherwise:
    """Hand a pace to a class whose ``__init__`` names its receiver otherwise."""
    return _ReceiverNamedOtherwise(pace)


def test_a_receiver_is_dropped_whatever_it_is_called() -> None:
    """A call of a class fills the first parameter of the ``__init__`` it
    runs itself, whatever it is called: ``_ReceiverNamedOtherwise(pace)``
    hands the pace to ``pace``, which the ``__init__`` checks.

    The receiver was dropped only when it was called ``self`` or ``cls``,
    so the pace was read as handed to ``instance`` and reported as never
    checked.
    """
    pace = "Literal['fast', 'slow']"
    assert (
        ccl._choice_verdict(
            _through_a_receiver_named_otherwise, "pace", pace, field=False
        )
        is None
    )
    with pytest.raises(ValueError, match="pace"):
        _through_a_receiver_named_otherwise("medium")  # type: ignore[arg-type]


class _ChecksThroughItsClass:
    """A class whose class method and ``__new__`` call a plain method on the
    class they hold, which takes the call's first argument as its instance.
    """

    def check(self, pace: _Pace = "fast") -> None:
        """Check the pace this method is handed."""
        require_choice(pace, "pace", _PACES)

    @classmethod
    def build(cls, pace: _Pace = "fast") -> None:
        """Hand the pace to ``check`` as its instance."""
        cls.check(pace)  # type: ignore[arg-type]

    @classmethod
    def build_held(cls, holder: object, pace: _Pace = "fast") -> None:
        """Hand ``holder`` as the instance, and the pace to ``check``."""
        cls.check(holder, pace)  # type: ignore[arg-type]

    def __new__(cls, pace: _Pace = "fast") -> _ChecksThroughItsClass:
        """Hand the pace to ``check`` as its instance."""
        cls.check(pace)  # type: ignore[arg-type]
        return super().__new__(cls)


def _through_a_class_method(pace: _Pace = "fast") -> None:
    """Hand a pace to a class method that loses it."""
    _ChecksThroughItsClass.build(pace)


def _through_a_class_method_held(pace: _Pace = "fast") -> None:
    """Hand a pace to a class method that checks it."""
    _ChecksThroughItsClass.build_held(None, pace)


def _through_new(pace: _Pace = "fast") -> _ChecksThroughItsClass:
    """Hand a pace to a ``__new__`` that loses it."""
    return _ChecksThroughItsClass.__new__(_ChecksThroughItsClass, pace)


def test_a_plain_method_called_on_the_class_takes_the_call_s_first_argument() -> None:
    """In a class method, and in ``__new__``, ``cls`` is the class, so
    ``cls.check(pace)`` calls a plain ``check`` through its class: the pace
    is its instance and it checks its default, while
    ``cls.check(holder, pace)`` checks the pace. The run agrees.

    ``cls`` was read as an instance, as ``self`` is, so ``cls.check(pace)``
    was read as checking the pace and ``cls.check(holder, pace)`` as never
    checking it.
    """
    pace = "Literal['fast', 'slow']"
    for lost in (_through_a_class_method, _through_new):
        assert ccl._choice_verdict(lost, "pace", pace, field=False) is not None
        lost("medium")  # type: ignore[arg-type]
    assert (
        ccl._choice_verdict(_through_a_class_method_held, "pace", pace, field=False)
        is None
    )
    with pytest.raises(ValueError, match="pace"):
        _through_a_class_method_held("medium")  # type: ignore[arg-type]


@dataclass
class _ChecksInItsInit:
    """A record whose ``__init__``, written by hand, checks the pace itself."""

    pace: _Pace = "fast"

    def __init__(self, pace: _Pace = "fast") -> None:
        require_choice(pace, "pace", _PACES)
        self.pace = pace


class _PlainOverChecks(_ChecksInItsInit):
    """A class that is no record over one that checks in its ``__init__``."""


def _through_an_inherited_init(pace: _Pace = "fast") -> _PlainOverChecks:
    """Hand a pace to a class that runs its base's hand-written ``__init__``."""
    return _PlainOverChecks(pace)


@dataclass
class _QuietHook:
    """A record whose hook checks nothing."""

    pace: _Pace = "fast"

    def __post_init__(self) -> None:
        """Check nothing."""


@dataclass
class _NamesItsHook(_QuietHook):
    """A record whose ``__init__`` runs the base's hook by its class's name,
    past a hook of its own that checks the pace and never runs.
    """

    def __init__(self, pace: _Pace = "fast") -> None:
        self.pace = pace
        _QuietHook.__post_init__(self)

    def __post_init__(self) -> None:
        require_choice(self.pace, "pace", _PACES)


def _through_a_named_hook(pace: _Pace = "fast") -> _NamesItsHook:
    """Hand a pace to a record whose ``__init__`` names the hook it runs."""
    return _NamesItsHook(pace)


def test_a_hand_written_init_is_read_and_runs_the_hook_it_names() -> None:
    """``_PlainOverChecks(pace)`` runs the ``__init__`` its base writes by
    hand, which checks the pace as a function does; ``_NamesItsHook(pace)``
    runs ``_QuietHook.__post_init__``, which its ``__init__`` names through
    the class, and never the hook of its own that checks.

    A record's ``__init__`` was read only through the hook it runs, so the
    pace ``_ChecksInItsInit.__init__`` checks was reported as never checked;
    and the hook was looked up through the record's own order, so the check
    that never runs was credited.
    """
    pace = "Literal['fast', 'slow']"
    assert (
        ccl._choice_verdict(_through_an_inherited_init, "pace", pace, field=False)
        is None
    )
    with pytest.raises(ValueError, match="pace"):
        _through_an_inherited_init("medium")  # type: ignore[arg-type]
    assert ccl._post_init(_NamesItsHook) is inspect.unwrap(
        vars(_QuietHook)["__post_init__"]
    )
    assert (
        ccl._choice_verdict(_through_a_named_hook, "pace", pace, field=False)
        is not None
    )
    assert _through_a_named_hook("medium").pace == "medium"  # type: ignore[arg-type]


def test_the_callers_of_a_private_method_are_the_calls_that_reach_it(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``self._helper("a")`` in ``First`` and ``First._helper(First(), "c")``
    reach ``First._helper``; ``Second``'s own ``_helper``, of the same name,
    takes the open text its callers hand, and is no caller of ``First``'s.

    Every call of a method of that name was read as a caller, so the open
    text ``Second`` hands its own ``_helper`` made ``First._helper``'s
    ``kind`` open.
    """
    source = (
        "class First:\n"
        "    def _helper(self, kind):\n"
        "        return kind\n\n"
        "    def a(self, text):\n"
        "        return self._helper('a')\n\n"
        "class Second:\n"
        "    def _helper(self, kind):\n"
        "        return kind\n\n"
        "    def b(self, text):\n"
        "        return self._helper(text)\n\n"
        "def c(text):\n"
        "    return First._helper(First(), 'c')\n\n"
        "def d(text):\n"
        "    return Second._helper(Second(), text)\n"
    )
    _plant_modules(tmp_path, monkeypatch, {"_two_helpers": source})
    tree = ast.parse(source)
    first, second, c, d = tree.body
    assert isinstance(first, ast.ClassDef)
    assert isinstance(second, ast.ClassDef)
    first_helper, a = first.body
    second_helper, b = second.body
    module = "phonometry._two_helpers"
    owners = {
        id(first_helper): "First",
        id(a): "First",
        id(second_helper): "Second",
        id(b): "Second",
    }
    sites: list[tuple[str, ast.AST | None, ast.Call]] = []
    for caller in (a, b, c, d):
        assert isinstance(caller, ast.FunctionDef)
        assert isinstance(caller.body[0], ast.Return)
        site = caller.body[0].value
        assert isinstance(site, ast.Call)
        sites.append((module, caller, site))
    monkeypatch.setattr(ccl, "_construction_sites", lambda: {"_helper": tuple(sites)})
    monkeypatch.setattr(ccl, "_METHOD_OWNERS", owners)
    assert isinstance(first_helper, ast.FunctionDef)
    assert ccl._callers_source(first_helper, "kind", module, 0) == ccl._Source(
        "texts", frozenset({"a", "c"})
    )


def test_a_helper_s_receiver_is_known_by_its_binding_at_every_caller(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first parameter of a private method is its receiver whatever it
    is called, so ``self._helper("a")`` hands ``"a"`` to ``kind`` of
    ``_helper(this, kind)``; and ``cls`` in a class method is the class, so
    ``cls._helper(text, "b")`` hands ``text`` to ``this`` and ``"b"`` to
    ``kind``. Every caller hands ``kind`` a fixed text.

    The receiver was known by the name ``self`` or ``cls``: ``"a"`` was
    read as handed to ``this``, so ``kind`` was read as handed nothing and
    came back open; and ``cls`` was read as an instance, so ``text`` was
    read as handed to ``kind``.
    """
    source = (
        "class Maker:\n"
        "    def _helper(this, kind):\n"
        "        return kind\n\n"
        "    def a(self, text):\n"
        "        return self._helper('a')\n\n"
        "    @classmethod\n"
        "    def b(cls, text):\n"
        "        return cls._helper(text, 'b')\n"
    )
    _plant_modules(tmp_path, monkeypatch, {"_bound_helpers": source})
    tree = ast.parse(source)
    (maker,) = tree.body
    assert isinstance(maker, ast.ClassDef)
    helper, a, b = maker.body
    module = "phonometry._bound_helpers"
    owners = {id(helper): "Maker", id(a): "Maker", id(b): "Maker"}
    sites: list[tuple[str, ast.AST | None, ast.Call]] = []
    for caller in (a, b):
        assert isinstance(caller, ast.FunctionDef)
        assert isinstance(caller.body[0], ast.Return)
        site = caller.body[0].value
        assert isinstance(site, ast.Call)
        sites.append((module, caller, site))
    monkeypatch.setattr(ccl, "_construction_sites", lambda: {"_helper": tuple(sites)})
    monkeypatch.setattr(ccl, "_METHOD_OWNERS", owners)
    assert isinstance(helper, ast.FunctionDef)
    assert ccl._callers_source(helper, "kind", module, 0) == ccl._Source(
        "texts", frozenset({"a", "b"})
    )


def test_a_call_on_self_reaches_the_method_a_class_over_the_caller_holds(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``self._helper(text)`` in ``Base.a`` runs what the class of the
    instance holds: on a ``Sub``, ``Sub``'s own ``_helper``, and on a
    ``Mixed``, the ``_helper`` it takes from ``Mixin``. Both take the open
    text ``a`` hands, beside the fixed texts their own callers hand.

    A call on ``self`` was read as reaching only what the caller's class
    holds, ``Base``'s ``_helper`` or none, so ``Sub._helper`` and
    ``Mixin._helper`` were read as taking fixed texts alone.
    """
    source = (
        "class Base:\n"
        "    def _helper(self, kind):\n"
        "        return kind\n\n"
        "    def a(self, text):\n"
        "        return self._helper(text)\n\n"
        "class Sub(Base):\n"
        "    def _helper(self, kind):\n"
        "        return kind\n\n"
        "    def b(self, text):\n"
        "        return self._helper('b')\n\n"
        "class Abstract:\n"
        "    def c(self, text):\n"
        "        return self._helper(text)\n\n"
        "class Mixin:\n"
        "    def _helper(self, kind):\n"
        "        return kind\n\n"
        "    def d(self, text):\n"
        "        return self._helper('d')\n\n"
        "class Mixed(Abstract, Mixin):\n"
        "    pass\n"
    )
    _plant_modules(tmp_path, monkeypatch, {"_overriding_helpers": source})
    tree = ast.parse(source)
    base, sub, abstract, mixin, _mixed = tree.body
    assert isinstance(base, ast.ClassDef)
    assert isinstance(sub, ast.ClassDef)
    assert isinstance(abstract, ast.ClassDef)
    assert isinstance(mixin, ast.ClassDef)
    base_helper, a = base.body
    sub_helper, b = sub.body
    (c,) = abstract.body
    mixin_helper, d = mixin.body
    module = "phonometry._overriding_helpers"
    owners = {
        id(base_helper): "Base",
        id(a): "Base",
        id(sub_helper): "Sub",
        id(b): "Sub",
        id(c): "Abstract",
        id(mixin_helper): "Mixin",
        id(d): "Mixin",
    }
    sites: list[tuple[str, ast.AST | None, ast.Call]] = []
    for caller in (a, b, c, d):
        assert isinstance(caller, ast.FunctionDef)
        assert isinstance(caller.body[0], ast.Return)
        site = caller.body[0].value
        assert isinstance(site, ast.Call)
        sites.append((module, caller, site))
    monkeypatch.setattr(ccl, "_construction_sites", lambda: {"_helper": tuple(sites)})
    monkeypatch.setattr(ccl, "_METHOD_OWNERS", owners)
    for helper in (sub_helper, mixin_helper):
        assert isinstance(helper, ast.FunctionDef)
        assert ccl._callers_source(helper, "kind", module, 0) == ccl._OPEN_SOURCE


@dataclass
class _ChecksItsPace:
    """A record whose hook checks the pace."""

    pace: _Pace = "fast"

    def __post_init__(self) -> None:
        require_choice(self.pace, "pace", _PACES)


@dataclass(init=False)
class _HookOnOneBranch(_ChecksItsPace):
    """A record whose ``__init__`` runs the hook on one branch alone."""

    def __init__(self, pace: _Pace = "fast", *, check: bool = False) -> None:
        self.pace = pace
        if check:
            self.__post_init__()


@dataclass(init=False)
class _HookNamedOnly(_ChecksItsPace):
    """A record whose ``__init__`` looks the hook up and never calls it."""

    def __init__(self, pace: _Pace = "fast") -> None:
        self.pace = pace
        self.hook = self.__post_init__


@dataclass(init=False)
class _HookSwallowed(_ChecksItsPace):
    """A record whose ``__init__`` calls the hook in a block that swallows
    its refusal.
    """

    def __init__(self, pace: _Pace = "fast") -> None:
        self.pace = pace
        with contextlib.suppress(ValueError):
            self.__post_init__()


@dataclass(init=False)
class _BuildsAnother(_ChecksItsPace):
    """A record whose ``__init__`` hands the pace to the base's ``__init__``
    for another instance, whose hook checks nothing.
    """

    def __init__(self, pace: _Pace = "fast") -> None:
        other = object.__new__(_QuietHook)
        _ChecksItsPace.__init__(other, pace)  # type: ignore[arg-type]
        self.pace = pace


@dataclass(init=False)
class _CallsItsHook(_ChecksItsPace):
    """A record whose ``__init__`` calls the hook on every path."""

    def __init__(self, pace: _Pace = "fast") -> None:
        self.pace = pace
        self.__post_init__()


@dataclass(init=False)
class _CallsPastItself(_ChecksItsPace):
    """A record whose ``__init__`` calls the base's hook through ``super()``."""

    def __init__(self, pace: _Pace = "fast") -> None:
        self.pace = pace
        super().__post_init__()


@dataclass(init=False)
class _HandsItselfOn(_ChecksItsPace):
    """A record whose ``__init__`` hands ``self`` to the base's."""

    def __init__(self, pace: _Pace = "fast") -> None:
        _ChecksItsPace.__init__(self, pace)


@pytest.mark.parametrize(
    ("record", "runs"),
    [
        (_HookOnOneBranch, False),
        (_HookNamedOnly, False),
        (_HookSwallowed, False),
        (_BuildsAnother, False),
        (_CallsItsHook, True),
        (_CallsPastItself, True),
        (_HandsItselfOn, True),
    ],
    ids=[
        "one-branch",
        "named-only",
        "swallowed",
        "another-instance",
        "called",
        "called-past-itself",
        "handed-on",
    ],
)
def test_a_hand_written_init_runs_the_hook_it_calls_on_self_on_every_path(
    record: type[_ChecksItsPace], *, runs: bool
) -> None:
    """An ``__init__`` written by hand runs ``__post_init__`` on ``self``
    when it calls ``self.__post_init__()``, or hands ``self`` to an
    ``__init__`` that does, on every path a call that returns takes; the
    run agrees: only those refuse a pace the hook does not take.

    Any mention of ``__post_init__`` in its code was read as a call, so a
    hook called on one branch, or only looked up, was credited with its
    check, and so was one called in a ``with`` block that swallows its
    refusal; and any ``Base.__init__(...)`` was read as a hand-off, so one
    that builds another instance credited the check to ``self``.
    """
    assert ccl._runs_a_post_init(record) is runs
    if runs:
        with pytest.raises(ValueError, match="pace"):
            record("medium")  # type: ignore[arg-type]
    else:
        assert record("medium").pace == "medium"  # type: ignore[arg-type]


# -- Rule D24: a Literal lists no value every call refuses -------------------

_Gear = Literal["low", "high", "reverse"]
_Axle = Literal["front", "rear"]
#: The gears with a ratio of their own; ``"reverse"`` has none here.
_GEAR_RATIOS = MappingProxyType({"low": 3.0, "high": 1.0})
#: The ratio of each gear on each axle it drives.
_PAIRED_RATIOS = MappingProxyType({("low", "front"): 3.0, ("high", "rear"): 1.0})
#: ``(teeth, ratio)`` of every gear, the ratio ``None`` for one that has none.
_GEAR_ROWS: Mapping[str, tuple[int, float | None]] = MappingProxyType(
    {"low": (12, 3.0), "high": (36, 1.0), "reverse": (10, None)}
)


class _GearMember(enum.Enum):
    LOW = "low"
    HIGH = "high"


def _ratio_by_check(gear: _Gear) -> float:
    return _GEAR_RATIOS[require_choice(gear, "gear", tuple(_GEAR_RATIOS))]


def _ratio_by_membership(gear: _Gear) -> float:
    if isinstance(gear, str) and gear not in _GEAR_RATIOS:
        msg = f"gear {gear!r} has no ratio"
        raise ValueError(msg)
    return 1.0


def _ratio_by_lookup(gear: _Gear) -> float:
    return _GEAR_RATIOS[gear]


def _ratio_handed_on(gear: _Gear, load: float) -> float:
    return load * _ratio_by_check(gear)


def _gear_row(gear: object) -> tuple[int, float | None]:
    name = require_choice(gear, "gear", tuple(_GEAR_ROWS))
    return _GEAR_ROWS[name]


def _ratio_through_a_row(gear: _Gear) -> float:
    _, ratio = _gear_row(gear)
    if ratio is None:
        msg = f"gear {gear!r} has no ratio"
        raise ValueError(msg)
    return ratio


def _ratio_by_member(gear: _Gear) -> _GearMember:
    return _GearMember(gear)


def _ratio_by_pair(gear: _Gear, axle: _Axle) -> float:
    return _PAIRED_RATIOS[(gear, axle)]


@dataclass(frozen=True)
class _Gearbox:
    gear: _Gear

    def __post_init__(self) -> None:
        require_choice(self.gear, "gear", ("low", "high"))


def _gearbox_of(gear: _Gear) -> _Gearbox:
    return _Gearbox(gear=gear)


def _ratio_beside_another(gear: _Gear, *, towing: bool) -> float:
    if towing and gear == "reverse":
        msg = "no towing in reverse"
        raise ValueError(msg)
    return 1.0


def _ratio_in_a_later_link(gear: _Gear, load: float) -> bool:
    return 0 < load < _GEAR_RATIOS[gear]


def _ratio_tested_in_a_later_link(gear: _Gear, level: float) -> float:
    if 0 <= level < _GEAR_RATIOS[gear]:
        return 1.0
    return 0.0


def _ratio_in_the_first_link(gear: _Gear, load: float, limit: float) -> bool:
    return _GEAR_RATIOS[gear] < load < limit


def _ratio_behind_links_that_hold(gear: _Gear) -> bool:
    return 0 < 1 < _GEAR_RATIOS[gear]


def _ratio_on_one_branch(gear: _Gear, *, towing: bool) -> float:
    if towing:
        return _GEAR_RATIOS[gear]
    return 1.0


def _ratio_caught(gear: _Gear) -> float:
    try:
        return _GEAR_RATIOS[gear]
    except KeyError:
        return 0.0


def _ratio_after_an_early_return(gear: _Gear) -> float:
    if gear == "reverse":
        return -1.0
    return _GEAR_RATIOS[gear]


def _ratio_in_a_loop(gear: _Gear, loads: Sequence[float]) -> float:
    total = 0.0
    for load in loads:
        total += load * _GEAR_RATIOS[gear]
    return total


def _first_load_or_ratio(gear: _Gear, loads: Sequence[float]) -> float:
    for load in loads:
        return load
    return _GEAR_RATIOS[gear]


def _ratio_unless_a_load_stops_short(gear: _Gear, loads: Sequence[float]) -> float:
    total = 0.0
    for load in loads:
        if load > 0:
            total += load
        else:
            return total
    return total * _GEAR_RATIOS[gear]


def _refusal(function: Callable[..., object], name: str, value: object) -> str | None:
    return ccl._always_refused(function, name, value, field=False)


@pytest.mark.parametrize(
    ("function", "evidence"),
    [
        (_ratio_by_check, "require_choice refuses it"),
        (_ratio_by_membership, "raises where isinstance(gear, str)"),
        (_ratio_by_lookup, "_GEAR_RATIOS has no key 'reverse'"),
        (_ratio_handed_on, "handed to _ratio_by_check, require_choice"),
        (_ratio_through_a_row, "raises where ratio is None"),
        (_ratio_by_member, "_GearMember has no member of value 'reverse'"),
        (_ratio_by_pair, "_PAIRED_RATIOS has no key ('reverse', ?)"),
        (_gearbox_of, "handed to _Gearbox.__post_init__, require_choice"),
        (_ratio_in_the_first_link, "_GEAR_RATIOS has no key 'reverse'"),
        (_ratio_behind_links_that_hold, "_GEAR_RATIOS has no key 'reverse'"),
    ],
    ids=[
        "shared-check",
        "membership",
        "table",
        "handed-on",
        "row-a-helper-hands-back",
        "enum",
        "no-key-holds-it",
        "record",
        "first-link",
        "later-link-behind-links-that-hold",
    ],
)
def test_a_value_every_call_refuses_is_named(
    function: Callable[..., object], evidence: str
) -> None:
    """A value the call refuses whatever else it is handed, at a shared
    check, a membership test that raises, a fixed table, an ``Enum``, a
    table keyed by tuples none of which holds it in its place, a function
    or a record it is handed to, or a test of what a helper hands back for
    it (the ``j3 is None`` of the junction with no straight section), is
    named with the refusal; the values the call takes are not. A lookup in
    the first link of a chained comparison runs whenever the comparison
    does, and so does one in a later link behind links that always hold.
    """
    reason = _refusal(function, "gear", "reverse")
    assert reason is not None
    assert evidence in reason
    assert _refusal(function, "gear", "low") is None


def test_a_value_refused_beside_another_argument_is_a_combination() -> None:
    """A refusal joined with a test of another argument, one in a later link
    of a chained comparison that runs only when a link testing another
    argument holds, one on a branch another argument picks, and a tuple key
    some key holds the value in, are combinations the ``Literal`` cannot
    say: none is a refusal of the value.

    Every link of a chained comparison was read as running, so the lookup of
    ``0 < load < _GEAR_RATIOS[gear]`` refused ``"reverse"``, though Python
    skips it whenever the load is not positive.
    """
    assert _refusal(_ratio_beside_another, "gear", "reverse") is None
    assert _refusal(_ratio_in_a_later_link, "gear", "reverse") is None
    assert _refusal(_ratio_tested_in_a_later_link, "gear", "reverse") is None
    assert _refusal(_ratio_on_one_branch, "gear", "reverse") is None
    assert _refusal(_ratio_by_pair, "gear", "high") is None
    assert _refusal(_ratio_in_a_loop, "gear", "reverse") is None


def test_a_refusal_a_handler_catches_or_a_return_skips_is_none() -> None:
    """A lookup whose ``KeyError`` a handler turns into a value, one an
    earlier ``return`` keeps the value from, and one after a loop that may
    return before it, take the value.

    The walk looked for the loop's ``return`` in each statement of its body
    as in a scope of its own, which it entered by that statement's body
    alone: a ``return`` written straight in the loop, or in the ``else`` of
    a test in it, went unseen, and the lookup after the loop refused
    ``"reverse"``, though a call with a load returns first.
    """
    assert _refusal(_ratio_caught, "gear", "reverse") is None
    assert _refusal(_ratio_after_an_early_return, "gear", "reverse") is None
    assert _refusal(_first_load_or_ratio, "gear", "reverse") is None
    assert _refusal(_ratio_unless_a_load_stops_short, "gear", "reverse") is None


@pytest.mark.parametrize(
    "source",
    [
        "return 1.0",
        "if load:\n    pass\nelse:\n    return 1.0",
        "try:\n    pass\nexcept KeyError:\n    return 1.0",
        "try:\n    pass\nfinally:\n    return 1.0",
        "while load:\n    pass\nelse:\n    return 1.0",
        "with open(path):\n    return 1.0",
        "match load:\n    case 0:\n        return 1.0",
    ],
    ids=["straight", "else", "handler", "finally", "loop-else", "with", "case"],
)
def test_a_return_is_found_wherever_the_statements_hold_it(source: str) -> None:
    """A ``return`` of the function's own is found in the statements that
    hold it, written straight among them or in any branch of one: the walk
    reads a loop that may return, and a ``finally`` that returns, by it.
    """
    assert ccl._returns_in(ast.parse(source).body)


def test_a_return_of_a_function_or_class_written_inside_is_not_one() -> None:
    """The ``return`` of a function or a class written among the statements
    ends a call of that function, not of the one the walk reads.
    """
    source = "def inner():\n    return 1.0\nclass Inner:\n    def f(self):\n        return 1.0"
    assert not ccl._returns_in(ast.parse(source).body)


def test_a_return_in_finally_takes_the_value(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ``return`` written straight in ``finally`` swallows the lookup's
    ``KeyError``, so the call takes the value; one written in a test of it
    was the only one the walk saw.
    """
    source = """
        from types import MappingProxyType

        _RATIOS = MappingProxyType({"low": 3.0})

        def ratio(gear):
            try:
                return _RATIOS[gear]
            finally:
                return 0.0
        """
    with warnings.catch_warnings():
        # Python 3.14 warns at a return in finally (PEP 765), which is the
        # shape planted here.
        warnings.simplefilter("ignore", SyntaxWarning)
        _plant_modules(tmp_path, monkeypatch, {"_ratio_in_finally": source})
    ratio = sys.modules["phonometry._ratio_in_finally"].ratio
    assert ratio("reverse") == 0.0
    assert _refusal(ratio, "gear", "reverse") is None


def test_each_value_the_literal_lists_is_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The walk reads the ``Literal`` of each parameter through its alias and
    reports each value every call refuses, the record's field included, and
    no parameter whose values every call may take.
    """
    targets = [
        (__name__, "_ratio_by_check", _ratio_by_check),
        (__name__, "_ratio_beside_another", _ratio_beside_another),
        (__name__, "_Gearbox", _Gearbox),
    ]
    monkeypatch.setattr(ccl, "_targets", lambda: iter(targets))
    found = {(choice.qualname, choice.name): choice for choice in ccl.refused_choices()}
    assert sorted(found) == [("_Gearbox", "gear"), ("_ratio_by_check", "gear")]
    assert [
        evidence.split(":")[0] for evidence in found["_Gearbox", "gear"].evidence
    ] == ["'reverse'"]


@pytest.mark.parametrize(
    ("function", "name", "refused", "taken"),
    [
        (
            vibration.straight_transmission_coefficient,
            "junction",
            ("T2", "L"),
            ("X", "T1"),
        ),
        (environment.rail_roughness, "roughness", ("N", "B"), ("E", "M")),
        (
            building.improvement_octave_bands,
            "quantity",
            ("LI", "LI,norm"),
            ("ΔL", "Rs"),
        ),
        (emission.measurement_positions, "surface", ("box",), ("hemisphere",)),
        (
            vibration.construction_guide_values,
            "area",
            ("sensitive",),
            ("industrial", "residential"),
        ),
    ],
    ids=[
        "junction",
        "rail-roughness",
        "octave-quantity",
        "surface",
        "construction-area",
    ],
)
def test_the_values_a_narrowed_choice_dropped_are_the_ones_its_call_refuses(
    function: Callable[..., object],
    name: str,
    refused: tuple[str, ...],
    taken: tuple[str, ...],
) -> None:
    """Each choice the package narrowed to the values its call takes still
    refuses the ones it dropped, whatever the other arguments are, and the
    guard reads it so: the same function with its old, wider annotation
    fails the walk.
    """
    for value in refused:
        assert _refusal(function, name, value) is not None, value
    for value in taken:
        assert _refusal(function, name, value) is None, value


@pytest.mark.parametrize(
    ("function", "name", "value"),
    [
        (vibration.junction_transmission, "junction", "T2"),
        (io.write, "subtype", "PCM_32"),
        (vibration.guide_values, "area", "sensitive"),
    ],
    ids=["corner-only-junction", "subtype-beside-flac", "area-of-table-1"],
)
def test_a_value_the_package_refuses_only_beside_another_argument_passes(
    function: Callable[..., object], name: str, value: str
) -> None:
    """``junction_transmission`` takes the ``"T2"`` it reads no straight
    section of, ``io.write`` refuses ``"PCM_32"`` beside a FLAC file alone,
    and ``guide_values`` takes the sensitive area Table 2 has no row for.
    """
    assert _refusal(function, name, value) is None


@pytest.mark.whole_tree
def test_no_literal_lists_a_value_every_call_refuses() -> None:
    """The package passes: every value a public ``Literal`` choice lists is
    one some call takes (rule D24).
    """
    assert list(ccl.refused_choices()) == []
