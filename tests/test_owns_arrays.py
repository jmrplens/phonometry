#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every public record keeps a read-only copy of its own of the arrays it holds.

``phonometry._internal.frozen.OwnsArrays`` makes the copy when the record is
built, so it holds whoever builds the record: a function of the library, or a
caller who writes ``SomeResult(levels=levels, ...)`` by hand. The first
half of this file fixes what the mechanism does, on records written for the
purpose, the arrays a factory hands over without a copy included, and that
the largest simulation results are not held twice while they are built; the
second builds public records of the library by hand with an
array the caller can still write into, writes into it, and checks that the
record did not move.
"""

from __future__ import annotations

import contextlib
import dataclasses
import importlib
import pickle
import pkgutil
import tracemalloc
import warnings
from collections import ChainMap, OrderedDict, defaultdict, deque
from collections.abc import Iterator, Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple, cast

import numpy as np
import pytest
from array_likes import ARRAY_LIKES
from numpy.lib.stride_tricks import sliding_window_view

import phonometry
from phonometry import io
from phonometry._internal import frozen
from phonometry._internal.frozen import OwnsArrays, read_only

if TYPE_CHECKING:
    from collections.abc import Callable

    from numpy.typing import ArrayLike

# ---------------------------------------------------------------------------
# The mechanism, on records written for the purpose
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class _Plain(OwnsArrays):
    levels: np.ndarray
    label: str = ""
    gain: float = 1.0


class _Pair(NamedTuple):
    frequencies: np.ndarray
    weight: float


@dataclasses.dataclass(frozen=True)
class _Containers(OwnsArrays):
    pair: tuple[np.ndarray, float]
    many: list[np.ndarray]
    columns: dict[str, np.ndarray]
    frozen_columns: MappingProxyType[str, np.ndarray]
    named: _Pair
    nested: tuple[tuple[str, np.ndarray], ...] = ()
    numbers: tuple[float, ...] = ()


@dataclasses.dataclass(frozen=True)
class _Validated(OwnsArrays):
    levels: np.ndarray
    doubled_db: np.ndarray = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        # The class's own hook runs on the record's copy, never the caller's.
        if self.levels.flags.writeable:
            msg = "the hook saw an array the caller can still write into"
            raise AssertionError(msg)
        object.__setattr__(self, "doubled_db", read_only(2.0 * self.levels))


@dataclasses.dataclass(frozen=True)
class _Sealing(OwnsArrays):
    levels: np.ndarray

    def __post_init__(self) -> None:
        # What the library's records do: read the field, seal what came back.
        object.__setattr__(
            self, "levels", read_only(np.asarray(self.levels, dtype=np.float64))
        )


@dataclasses.dataclass(frozen=True)
class _Unsealed(OwnsArrays):
    levels: np.ndarray
    centred_db: np.ndarray = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        # Stored writeable on purpose: the record copies it after the hook.
        object.__setattr__(self, "centred_db", self.levels - 1.0)


@dataclasses.dataclass(frozen=True)
class _Inherits(_Validated):
    extra_db: np.ndarray = dataclasses.field(default_factory=lambda: np.zeros(2))


@dataclasses.dataclass(frozen=True)
class _CallsSuper(_Validated):
    seen: list[object] = dataclasses.field(default_factory=list)

    def __post_init__(self) -> None:
        self.seen.append(self.levels)
        super().__post_init__()


class _Hooked:
    def __post_init__(self) -> None:
        pass


@dataclasses.dataclass(frozen=True)
class _WithInitVar(OwnsArrays):
    levels: np.ndarray
    offset_db: dataclasses.InitVar[np.ndarray]
    shifted_db: np.ndarray = dataclasses.field(init=False)

    def __post_init__(self, offset_db: np.ndarray) -> None:
        # Seals the argument it keeps, as a hook does with an array of its own.
        object.__setattr__(self, "shifted_db", read_only(offset_db))


class _CallerMapping(Mapping[str, np.ndarray]):
    """A mapping of the caller's own, neither a dict nor a proxy of one."""

    def __init__(self, items: dict[str, np.ndarray]) -> None:
        self._items = items

    def __getitem__(self, key: str) -> np.ndarray:
        return self._items[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)


def _mixin_listed_first() -> type:
    class Wrong(OwnsArrays, _Hooked):
        pass

    return Wrong


def _writeable(values: list[float]) -> np.ndarray:
    array = np.array(values)
    assert array.flags.writeable
    return array


def test_the_record_keeps_a_read_only_copy_and_the_caller_keeps_writing() -> None:
    levels = _writeable([60.0, 61.0, 62.0])
    record = _Plain(levels=levels, label="hand", gain=2.0)
    levels[0] = 0.0
    np.testing.assert_array_equal(record.levels, [60.0, 61.0, 62.0])
    assert not np.shares_memory(record.levels, levels)
    assert not record.levels.flags.writeable
    assert levels.flags.writeable
    assert (record.label, record.gain) == ("hand", 2.0)


def test_a_view_of_the_caller_s_array_is_copied_too() -> None:
    grid = _writeable([1.0, 2.0, 3.0, 4.0]).reshape(2, 2)
    record = _Plain(levels=grid[:, 0])
    grid[:, 0] = -1.0
    np.testing.assert_array_equal(record.levels, [1.0, 3.0])
    assert record.levels.flags.c_contiguous


def test_a_read_only_array_of_the_caller_is_copied_as_well() -> None:
    """A read-only flag is the caller's to set back, so it is no promise."""
    levels = _writeable([1.0, 2.0])
    levels.flags.writeable = False
    record = _Plain(levels=levels)
    assert not np.shares_memory(record.levels, levels)
    levels.flags.writeable = True
    levels[0] = 9.0
    assert record.levels[0] == 1.0


def test_arrays_inside_containers_are_copied_and_the_rest_is_kept() -> None:
    a, b, c = _writeable([1.0]), _writeable([2.0]), _writeable([3.0])
    numbers = (1.0, 2.0)
    record = _Containers(
        pair=(a, 5.0),
        many=[b],
        columns={"c": c},
        frozen_columns=MappingProxyType({"a": a}),
        named=_Pair(b, 0.5),
        nested=(("c", c),),
        numbers=numbers,
    )
    for array in (a, b, c):
        array[0] = 0.0
    assert record.pair[0][0] == 1.0
    assert record.pair[1] == 5.0
    assert record.many[0][0] == 2.0
    assert record.columns["c"][0] == 3.0
    assert isinstance(record.frozen_columns, MappingProxyType)
    assert record.frozen_columns["a"][0] == 1.0
    assert isinstance(record.named, _Pair)
    assert record.named.frequencies[0] == 2.0
    assert record.nested[0][1][0] == 3.0
    # A tuple that holds no array comes back as it went in.
    assert record.numbers is numbers


@pytest.mark.parametrize(
    "kind",
    [
        OrderedDict,
        lambda items: defaultdict(float, items),
        ChainMap,
        _CallerMapping,
    ],
    ids=["OrderedDict", "defaultdict", "ChainMap", "own Mapping"],
)
def test_arrays_inside_any_mapping_are_copied(
    kind: Callable[[dict[str, np.ndarray]], Mapping[str, np.ndarray]],
) -> None:
    """Not only a dict: any mapping is rebuilt, as a plain dict, around copies."""
    mine = _writeable([1.0, 2.0])
    given = kind({"c": mine})
    record = _Containers(
        pair=(np.zeros(1), 0.0),
        many=[],
        columns=given,  # type: ignore[arg-type]
        frozen_columns=MappingProxyType({}),
        named=_Pair(np.zeros(1), 0.0),
    )
    assert mine.flags.writeable
    assert not np.shares_memory(record.columns["c"], mine)
    assert not record.columns["c"].flags.writeable
    assert record.columns is not given
    mine[0] = 99.0
    assert record.columns["c"][0] == 1.0


def test_a_mapping_with_no_array_comes_back_as_it_went_in() -> None:
    given = OrderedDict(a=1.0)
    record = _Containers(
        pair=(np.zeros(1), 0.0),
        many=[],
        columns=given,  # type: ignore[arg-type]
        frozen_columns=MappingProxyType({}),
        named=_Pair(np.zeros(1), 0.0),
    )
    assert record.columns is given


def _objects(*members: object) -> np.ndarray:
    """An array of objects holding *members* as they are, one per element."""
    held = np.empty(len(members), dtype=object)
    for index, member in enumerate(members):
        held[index] = member
    return held


def test_arrays_inside_an_array_of_objects_are_copied() -> None:
    """Copying an array of objects copies its references, so each array in it is copied too.

    The record's copy of the outer array held the caller's own arrays: the
    caller's writes reached the record, and a hook that sealed a member
    sealed the caller's array.
    """
    first, second = _writeable([1.0, 2.0]), _writeable([3.0, 4.0, 5.0])
    given = _objects(first, second, "label").reshape(3, 1)
    record = _Plain(levels=given)
    assert record.levels.shape == (3, 1)
    assert not record.levels.flags.writeable
    for kept, mine in zip(record.levels[:2, 0], (first, second), strict=True):
        assert not np.shares_memory(kept, mine)
        assert not kept.flags.writeable
        assert mine.flags.writeable
    assert record.levels[2, 0] == "label"
    first[0] = 99.0
    assert record.levels[0, 0][0] == 1.0
    assert given[0, 0] is first


def _sealed_by_the_caller(values: list[float]) -> np.ndarray:
    array = _writeable(values)
    array.flags.writeable = False
    return array


@pytest.mark.parametrize(
    "holder",
    [deque, iter],
    ids=["deque", "generator"],
)
def test_the_arrays_a_record_takes_out_of_any_sequence_are_its_own(
    holder: Callable[[list[np.ndarray]], object],
) -> None:
    """A deque or a generator is no container the record goes through when it copies.

    So a record that holds the members of one as a tuple copies each array
    itself. Kept as it came, a writeable array was only copied by the check
    after the hook, and a read-only one of the caller's, whose flag the
    caller can set back, stayed the caller's.
    """
    writeable = _writeable([1.0, 2.0])
    sealed = _sealed_by_the_caller([3.0, 4.0])
    record = phonometry.filters.OctaveFilterResult(
        levels=None,
        frequencies=(500.0, 1000.0),
        bands=holder([writeable, sealed]),  # type: ignore[arg-type]
    )
    assert isinstance(record.bands, tuple)
    for kept, mine in zip(record.bands, (writeable, sealed), strict=True):
        assert isinstance(kept, np.ndarray)
        assert not np.shares_memory(kept, mine)
        assert not kept.flags.writeable
    assert writeable.flags.writeable
    sealed.flags.writeable = True
    sealed[0] = 99.0
    assert record.bands[1][0] == 3.0


def test_owned_members_hands_back_what_the_record_copied_as_it_is() -> None:
    """A tuple's, a list's or an array's members are the record's copies by then."""
    mine = _writeable([1.0, 2.0])
    assert frozen.owned_members((mine, 1.0))[0] is mine
    assert frozen.owned_members([mine])[0] is mine
    grid = _writeable([1.0, 2.0, 3.0, 4.0]).reshape(2, 2)
    assert np.shares_memory(frozen.owned_members(grid)[0], grid)
    assert frozen.owned_members(deque([mine]))[0] is not mine
    assert frozen.owned_members(deque(["a", 1.0])) == ("a", 1.0)


def test_a_read_only_copy_of_an_array_of_objects_holds_copies_of_its_arrays() -> None:
    """The copy a plain class keeps shares no array with the caller either."""
    mine = _writeable([1.0, 2.0])
    kept = frozen.read_only_copy(_objects(mine, "label"))
    assert not kept.flags.writeable
    assert not np.shares_memory(kept[0], mine)
    assert not kept[0].flags.writeable
    assert kept[1] == "label"
    assert mine.flags.writeable


def test_an_array_of_objects_comes_back_from_pickle_with_its_arrays_sealed() -> None:
    """``pickle`` hands every array back writeable, the ones an array of objects holds too."""
    record = _Plain(levels=_objects(_writeable([1.0]), _writeable([2.0, 3.0])))
    # The bytes are the ones made on this line, never read from elsewhere.
    back = pickle.loads(pickle.dumps(record))  # noqa: S301
    assert not back.levels.flags.writeable
    for member in back.levels:
        assert not member.flags.writeable


@pytest.mark.parametrize("kind", sorted(ARRAY_LIKES))
def test_an_array_like_is_held_as_a_copy_of_the_array_it_stands_for(
    kind: str,
) -> None:
    """Anything numpy reads as an array is read as one and copied before the hook.

    Held as it came, the hook's ``np.asarray`` of a column was the caller's
    own array, which ``read_only`` then sealed: the caller's next write
    raised, and the record kept the caller's memory. Of a ``memoryview`` or
    an object that publishes its memory, it was a new array over the
    caller's memory, and a hook that only checked the field left the record
    holding the caller's object.
    """
    mine = _writeable([1.0, 2.0, 3.0])
    seen: list[object] = []

    @dataclasses.dataclass(frozen=True)
    class Seen(_Sealing):
        def __post_init__(self) -> None:
            seen.append(self.levels)
            super().__post_init__()

    record = Seen(levels=ARRAY_LIKES[kind](mine))  # type: ignore[arg-type]
    assert isinstance(seen[0], np.ndarray)
    assert not seen[0].flags.writeable
    assert mine.flags.writeable
    assert not np.shares_memory(record.levels, mine)
    mine[0] = 9.0
    assert record.levels[0] == 1.0


@pytest.mark.parametrize("kind", sorted(ARRAY_LIKES))
def test_an_array_like_inside_a_container_or_an_init_var_is_copied(
    kind: str,
) -> None:
    """At any depth, and in the argument of an ``InitVar`` handed to the hook."""
    column = ARRAY_LIKES[kind]
    a, b, c = _writeable([1.0]), _writeable([2.0]), _writeable([3.0])
    record = _Containers(
        pair=(column(a), 5.0),  # type: ignore[arg-type]
        many=[column(b)],  # type: ignore[list-item]
        columns={"c": column(c)},  # type: ignore[dict-item]
        frozen_columns=MappingProxyType({}),
        named=_Pair(_writeable([0.0]), 0.5),
    )
    offset = _writeable([0.5])
    shifted = _WithInitVar(levels=_writeable([1.0]), offset_db=column(offset))  # type: ignore[arg-type]
    for kept, mine in (
        (record.pair[0], a),
        (record.many[0], b),
        (record.columns["c"], c),
        (shifted.shifted_db, offset),
    ):
        assert isinstance(kept, np.ndarray)
        assert not kept.flags.writeable
        assert mine.flags.writeable
        assert not np.shares_memory(kept, mine)


@pytest.mark.parametrize("kind", sorted(ARRAY_LIKES))
def test_a_read_only_copy_of_an_array_like_is_a_copy(kind: str) -> None:
    """``np.array`` hands ``copy=True`` on, which not every ``__array__`` honours.

    One older than the keyword drew a ``DeprecationWarning`` from NumPy, and
    one that ignores it handed back the caller's array, which was sealed.
    """
    mine = _writeable([1.0, 2.0])
    # An object that publishes its memory is an array to numpy, though
    # numpy's ArrayLike spells only __array__ and the buffer protocol.
    given = cast("ArrayLike", ARRAY_LIKES[kind](mine))
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        kept = frozen.read_only_copy(given)
    assert not kept.flags.writeable
    assert mine.flags.writeable
    assert not np.shares_memory(kept, mine)


def test_a_bytearray_is_held_as_the_bytes_it_spells() -> None:
    """A ``bytearray`` is a text, as a ``bytes`` is, and a frozen record holds it immutable.

    In a field that neither refuses nor converts it, and inside a container,
    it comes back as ``bytes``: never the caller's ``bytearray``, which the
    caller can still write into, nor an array of the codes of its
    characters.
    """
    label = bytearray(b"abc")
    member = bytearray(b"de")
    column = bytearray(b"fg")
    record = _Plain(levels=_writeable([1.0]), label=label)  # type: ignore[arg-type]
    held = _Containers(
        pair=(member, 5.0),  # type: ignore[arg-type]
        many=[],
        columns={"c": column},  # type: ignore[dict-item]
        frozen_columns=MappingProxyType({}),
        named=_Pair(_writeable([0.0]), 0.5),
    )
    for kept, mine in (
        (record.label, label),
        (held.pair[0], member),
        (held.columns["c"], column),
    ):
        assert type(kept) is bytes
        assert kept == bytes(mine)
        spelt = bytes(mine)
        mine[0] = ord("x")
        assert kept == spelt


def _texts(value: object) -> Iterator[bytes]:
    """Each ``bytes`` in *value*, or among its members or its mapping's values."""
    if isinstance(value, bytes):
        yield value
    elif isinstance(value, tuple | list):
        for member in value:
            yield from _texts(member)
    elif isinstance(value, Mapping):
        for member in value.values():
            yield from _texts(member)


@dataclasses.dataclass(frozen=True)
class _RefusesText(OwnsArrays):
    first: object
    second: object = None

    def __post_init__(self) -> None:
        # Refuses a text as a check of the library does, naming its type and
        # quoting it.
        named = [
            f"{frozen.given_type(text)} {frozen.given_repr(text)}"
            for text in _texts((self.first, self.second))
        ]
        if named:
            raise TypeError(", ".join(named))


@dataclasses.dataclass(frozen=True)
class _HandsOn(OwnsArrays):
    text: object

    def __post_init__(self) -> None:
        # Builds a record of its own from what it holds, as a factory does.
        _RefusesText(self.text)


@pytest.mark.parametrize(
    ("first", "second", "refusal"),
    [
        (bytearray(b"ab"), None, "bytearray bytearray(b'ab')"),
        (b"ab", None, "bytes b'ab'"),
        ((bytearray(b"ab"), 1.0), None, "bytearray bytearray(b'ab')"),
        ({"k": bytearray(b"ab")}, None, "bytearray bytearray(b'ab')"),
        (bytearray(b"1"), None, "bytearray bytearray(b'1')"),
        (bytearray(), None, "bytearray bytearray(b'')"),
        (b"ab", bytearray(b"cd"), "bytes b'ab', bytearray bytearray(b'cd')"),
    ],
    ids=[
        "bytearray",
        "bytes",
        "member",
        "mapping-value",
        "one-byte",
        "empty",
        "bytes-beside-a-bytearray",
    ],
)
def test_a_refusal_names_a_bytearray_as_the_caller_gave_it(
    first: object, second: object, refusal: str
) -> None:
    """The checks read the ``bytes`` a ``bytearray`` spells, and name it as the caller wrote it.

    A refusal that named the type of what the checks read, or quoted it,
    said the caller gave a ``bytes``; the record still holds no
    ``bytearray``, and a ``bytes`` the caller gave is named as one.
    """
    with pytest.raises(TypeError) as refused:
        _RefusesText(first, second)
    assert str(refused.value) == refusal


@dataclasses.dataclass(frozen=True)
class _QuotesWhole(OwnsArrays):
    given: object

    def __post_init__(self) -> None:
        # Refuses what it holds whole, quoting it as a check of the library
        # quotes a value of the wrong type.
        raise TypeError(frozen.given_repr(self.given))


class _Two(NamedTuple):
    first: object
    second: object


def _objects(*members: object) -> np.ndarray:
    held = np.empty(len(members), dtype=object)
    for index, member in enumerate(members):
        held[index] = member
    return held


@pytest.mark.parametrize(
    ("given", "quoted"),
    [
        ([bytearray(b"ab"), 1.0], "[bytearray(b'ab'), 1.0]"),
        ((bytearray(b"ab"),), "(bytearray(b'ab'),)"),
        ({"k": bytearray(b"ab")}, "{'k': bytearray(b'ab')}"),
        (
            MappingProxyType({"k": bytearray(b"ab")}),
            "mappingproxy({'k': bytearray(b'ab')})",
        ),
        (
            OrderedDict(k=bytearray(b"ab")),
            "{'k': bytearray(b'ab')}",
        ),
        (_Two(bytearray(b"ab"), 1.0), "_Two(first=bytearray(b'ab'), second=1.0)"),
        (
            _objects(bytearray(b"ab"), 1.0),
            "array([bytearray(b'ab'), 1.0], dtype=object)",
        ),
        ({"k": (bytearray(b"ab"), 1.0)}, "{'k': (bytearray(b'ab'), 1.0)}"),
        (
            {"k": b"ab", "j": bytearray(b"cd")},
            "{'k': b'ab', 'j': bytearray(b'cd')}",
        ),
        ({"k": 1.0}, "{'k': 1.0}"),
    ],
    ids=[
        "list",
        "one-member-tuple",
        "mapping",
        "read-only-mapping",
        "mapping-of-another-class",
        "named-tuple",
        "array-of-objects",
        "nested",
        "bytes-beside-a-bytearray",
        "no-bytearray",
    ],
)
def test_a_refusal_quotes_a_container_with_the_bytearray_it_holds(
    given: object, quoted: str
) -> None:
    """A container quoted whole shows the caller's ``bytearray``, wherever the record holds one.

    The record holds a ``bytearray`` as the ``bytes`` it spells inside a
    mapping, a read-only mapping, a named tuple and an array of objects as
    inside a tuple or a list, and a refusal that quoted one of them whole
    quoted the ``bytes``: ``{'k': b'ab'}`` for the caller's
    ``{'k': bytearray(b'ab')}``. A mapping of another class is held, and
    quoted, as the plain ``dict`` the record keeps.
    """
    with pytest.raises(TypeError) as refused:
        _QuotesWhole(given)
    assert str(refused.value) == quoted


def test_a_record_built_by_the_checks_names_the_bytearray_too() -> None:
    """A record a hook builds from what it holds names the caller's ``bytearray`` as well."""
    with pytest.raises(TypeError, match=r"^bytearray bytearray\(b'ab'\)$"):
        _HandsOn(bytearray(b"ab"))


def test_the_bytes_a_record_holds_are_named_bytes_once_it_is_built() -> None:
    """The caller's type is known while the checks run, and only then."""
    record = _Plain(levels=_writeable([1.0]), label=bytearray(b"abc"))  # type: ignore[arg-type]
    assert type(record.label) is bytes
    assert frozen.given_type(record.label) == "bytes"
    assert frozen.given_repr(record.label) == "b'abc'"


def test_every_copy_is_c_ordered_whatever_it_was_made_from() -> None:
    """A broadcast row and a transposed grid come out C-ordered, values kept."""
    row = _writeable([1.0, 2.0, 3.0])
    broadcast = np.broadcast_to(row, (4, 3))
    record = _Plain(levels=broadcast)
    assert record.levels.flags.c_contiguous
    np.testing.assert_array_equal(record.levels, broadcast)
    grid = _writeable([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]).reshape(2, 3)
    transposed = _Plain(levels=grid.T)
    assert transposed.levels.flags.c_contiguous
    np.testing.assert_array_equal(transposed.levels, grid.T)


def test_a_record_held_in_a_field_is_left_as_it_is() -> None:
    """Composition: the inner record answers for its own arrays."""

    @dataclasses.dataclass(frozen=True)
    class Outer(OwnsArrays):
        inner: _Plain
        steps: tuple[_Plain, ...]

    inner = _Plain(levels=_writeable([1.0]))
    outer = Outer(inner=inner, steps=(inner,))
    assert outer.inner is inner
    assert outer.steps[0] is inner


def test_the_argument_of_an_init_var_is_copied_before_the_hook() -> None:
    """The hook seals the argument it keeps; the caller's array keeps its flag."""
    offset = _writeable([0.5, 0.25])
    record = _WithInitVar(levels=_writeable([1.0, 2.0]), offset_db=offset)
    assert offset.flags.writeable
    assert not np.shares_memory(record.shifted_db, offset)
    offset[0] = 9.0
    assert record.shifted_db[0] == 0.5


def test_the_class_s_own_post_init_runs_on_the_copy() -> None:
    levels = _writeable([1.0, 2.0])
    record = _Validated(levels=levels)
    levels[:] = 0.0
    np.testing.assert_array_equal(record.doubled_db, [2.0, 4.0])
    assert not record.doubled_db.flags.writeable


def test_an_array_the_hook_left_writeable_is_copied_after_it() -> None:
    record = _Unsealed(levels=_writeable([3.0, 4.0]))
    assert not record.centred_db.flags.writeable
    np.testing.assert_array_equal(record.centred_db, [2.0, 3.0])


def test_a_read_only_view_of_an_array_someone_can_write_is_copied() -> None:
    owner = _writeable([1.0, 2.0, 3.0])

    @dataclasses.dataclass(frozen=True)
    class Borrowing(OwnsArrays):
        window: np.ndarray = dataclasses.field(init=False)

        def __post_init__(self) -> None:
            view = owner[1:]
            view.flags.writeable = False
            object.__setattr__(self, "window", view)

    record = Borrowing()
    owner[1] = -5.0
    np.testing.assert_array_equal(record.window, [2.0, 3.0])


def test_a_strided_view_of_an_array_someone_can_write_is_copied() -> None:
    """``sliding_window_view`` hides its array behind a stand-in; walked too."""
    owner = _writeable([1.0, 2.0, 3.0, 4.0])

    @dataclasses.dataclass(frozen=True)
    class Windows(OwnsArrays):
        frames: np.ndarray = dataclasses.field(init=False)

        def __post_init__(self) -> None:
            object.__setattr__(self, "frames", sliding_window_view(owner, 2))

    record = Windows()
    assert not np.shares_memory(record.frames, owner)
    owner[1] = -5.0
    assert record.frames[0, 1] == 2.0


def test_a_subclass_copies_its_own_fields_and_its_base_s() -> None:
    levels, extra = _writeable([1.0]), _writeable([7.0, 8.0])
    record = _Inherits(levels=levels, extra_db=extra)
    levels[0] = extra[0] = 0.0
    assert record.levels[0] == 1.0
    assert record.extra_db[0] == 7.0
    assert record.doubled_db[0] == 2.0


def test_a_hook_that_calls_super_copies_once() -> None:
    """``super().__post_init__()`` reaches the base's hook, not a second copy:
    the array the subclass's hook saw is the one the record keeps.
    """
    seen: list[object] = []
    record = _CallsSuper(levels=_writeable([1.0]), seen=seen)
    assert len(seen) == 1
    assert seen[0] is record.levels
    assert record.doubled_db[0] == 2.0


def test_listing_the_mixin_before_a_base_with_a_hook_is_refused() -> None:
    """The base's hook would never run, so the class is refused outright."""
    with pytest.raises(TypeError, match="list OwnsArrays last"):
        _mixin_listed_first()


def test_a_replaced_record_owns_what_it_was_given() -> None:
    record = _Plain(levels=_writeable([1.0]))
    levels = _writeable([5.0])
    replaced = dataclasses.replace(record, levels=levels)
    levels[0] = 0.0
    assert replaced.levels[0] == 5.0
    assert not np.shares_memory(replaced.levels, record.levels)


def test_none_and_numbers_go_through_untouched() -> None:
    @dataclasses.dataclass(frozen=True)
    class Optional(OwnsArrays):
        levels: np.ndarray | None = None
        level: float | np.ndarray = 0.0

    record = Optional()
    assert record.levels is None
    assert record.level == 0.0
    # A NumPy scalar hands numpy an array too, and stays the number it is.
    scalar = Optional(level=np.float64(2.0))
    assert type(scalar.level) is np.float64
    # Bytes are a buffer, which numpy reads as one text: they stay as they are.
    raw = Optional(level=b"\x00\x01")  # type: ignore[arg-type]
    assert raw.level == b"\x00\x01"


# ---------------------------------------------------------------------------
# An array handed over: kept as it is, sealed, never copied
# ---------------------------------------------------------------------------


def test_an_array_handed_over_is_kept_as_it_is_and_sealed() -> None:
    frames = np.zeros((4, 3))
    frames[1] = 2.0
    record = _Plain(levels=frozen.handed_over(frames))
    assert record.levels is frames
    assert not frames.flags.writeable
    with pytest.raises(ValueError, match="read-only"):
        frames[0, 0] = 1.0


def test_only_the_first_record_keeps_an_array_handed_over() -> None:
    frames = frozen.handed_over(np.ones(5))
    first = _Plain(levels=frames)
    second = _Plain(levels=frames)
    assert first.levels is frames
    assert second.levels is not frames
    assert not np.shares_memory(first.levels, second.levels)


@pytest.mark.parametrize(
    "make",
    [
        lambda: np.zeros((6, 4))[:, 1],
        lambda: np.zeros((6, 4))[::2],
        lambda: np.zeros((6, 4))[1:3],
        lambda: np.asfortranarray(np.zeros((6, 4))),
    ],
    ids=["view-of-a-column", "strided-view", "contiguous-view", "fortran-ordered"],
)
def test_an_array_handed_over_that_is_a_view_or_not_c_ordered_is_copied(
    make: Callable[[], np.ndarray],
) -> None:
    """Only memory the array owns, C-ordered, is kept: a view would leave
    its base writeable behind the record, and every record holds the same
    layout however it was built. A view is turned down before it is sealed,
    C-ordered or not, so the caller's view keeps its ``writeable`` flag.
    """
    array = make()
    record = _Plain(levels=frozen.handed_over(array))
    assert not np.shares_memory(record.levels, array)
    assert record.levels.flags.c_contiguous
    assert array.flags.writeable


def test_handing_over_none_hands_over_nothing() -> None:
    assert frozen.handed_over(None) is None


def test_an_array_never_kept_leaves_no_mark() -> None:
    before = len(frozen._HANDED_OVER)
    frozen.handed_over(np.zeros(3))
    assert len(frozen._HANDED_OVER) == before


def test_an_array_not_handed_over_is_still_copied() -> None:
    frames = np.zeros(5)
    record = _Plain(levels=frames)
    assert record.levels is not frames
    assert frames.flags.writeable


def _fdtd() -> object:
    from phonometry import simulation

    sim = simulation.FDTD2D(343.0, 0.02, shape=(100, 100))
    return simulation.fdtd_simulation(
        simulation.FDTDRun(
            c=343.0,
            dx=0.02,
            duration_s=100 * sim.dt,
            sources=[simulation.GaussianPulse(ix=50, iy=50, half_width_s=2e-4)],
            shape=(100, 100),
            recording=simulation.FDTDRecording(probes=[(10, 10)], snapshot_every=1),
        )
    )


def _elastic_fdtd() -> object:
    from phonometry import simulation

    dx = 0.05
    c_p = 5900.0
    dt = 0.6 * dx / (c_p * np.sqrt(2.0))
    pulse = simulation.GaussianPulse(ix=0, iy=0, half_width_s=2e-4)
    return simulation.elastic_fdtd_simulation(
        simulation.ElasticRun(
            c_p=c_p,
            c_s=3200.0,
            dx=dx,
            duration_s=160 * dt,
            sources=[simulation.ExplosionSource(ix=50, iy=30, waveform=pulse.value)],
            rho=7850.0,
            shape=(60, 100),
            recording=simulation.ElasticRecording(probes=[(5, 5)], snapshot_every=1),
        )
    )


def _underwater_pe() -> object:
    from phonometry import underwater

    return underwater.parabolic_equation(
        200.0,
        [0.0, 100.0],
        [1500.0, 1500.0],
        source_depth=40.0,
        max_range=10_000.0,
        range_step=2.0,
        n_depth_points=256,
    )


def _atmospheric_pe() -> object:
    from phonometry import environment

    return environment.atmospheric_parabolic_equation(
        500.0,
        environment.linear_sound_speed_profile(0.1),
        source_height_m=2.0,
        flow_resistivity_pa_s_m2=50e3,
        max_range=1000.0,
        max_height_m=50.0,
    )


@contextlib.contextmanager
def _traced_peak() -> Iterator[list[int]]:
    """The peak memory traced inside the block, above what was traced at its start.

    A trace already running (``PYTHONTRACEMALLOC``) is kept: its peak is reset
    and its starting allocation taken off, and it is stopped only if the block
    started it. The peak is appended to the list the block receives.
    """
    started = not tracemalloc.is_tracing()
    if started:
        tracemalloc.start()
    tracemalloc.reset_peak()
    base = tracemalloc.get_traced_memory()[0]
    peak: list[int] = []
    try:
        yield peak
    finally:
        peak.append(tracemalloc.get_traced_memory()[1] - base)
        if started:
            tracemalloc.stop()


@pytest.mark.parametrize(
    "run",
    [_fdtd, _elastic_fdtd, _underwater_pe, _atmospheric_pe],
    ids=["fdtd", "elastic-fdtd", "underwater-pe", "atmospheric-pe"],
)
def test_a_simulation_result_is_not_held_twice_while_it_is_built(
    run: Callable[[], object],
) -> None:
    """The frames of a run and the field of a march are written into one
    array and handed to the record, which keeps that array: at no moment
    does the run hold a second copy of the result (a list of frames and
    their stack, or the record's copy of either), so the memory the run
    needs above the result it returns is the solver's alone.
    """
    run()  # load the lazily imported domain packages outside the measurement
    with _traced_peak() as traced:
        result = run()
    peak = traced[0]
    arrays = [
        value
        for field in dataclasses.fields(result)  # type: ignore[arg-type]
        if isinstance(value := getattr(result, field.name), np.ndarray)
    ]
    held = sum(array.nbytes for array in arrays)
    assert peak - held < held / 2, (peak, held)
    assert all(not array.flags.writeable for array in arrays)


def _fdtd_engine() -> object:
    from phonometry import simulation

    sim = simulation.FDTD2D(343.0, 0.02, shape=(100, 100))
    sim.add_source(simulation.GaussianPulse(ix=50, iy=50, half_width_s=2e-4))
    return sim


def _elastic_fdtd_engine() -> object:
    from phonometry import simulation

    sim = simulation.ElasticFDTD2D(5900.0, 3200.0, 0.05, rho=7850.0, shape=(60, 100))
    pulse = simulation.GaussianPulse(ix=0, iy=0, half_width_s=2e-4)
    sim.add_source(simulation.ExplosionSource(ix=50, iy=30, waveform=pulse.value))
    return sim


@pytest.mark.parametrize(
    "engine",
    [_fdtd_engine, _elastic_fdtd_engine],
    ids=["fdtd", "elastic-fdtd"],
)
def test_a_run_writes_its_frames_into_one_array(
    engine: Callable[[], object],
) -> None:
    """``run()`` hands back the frames it records, and at no moment holds a
    second copy of them (a list of frames and their stack): the memory the
    march needs above the frames it returns is the solver's alone.
    """
    sim = engine()
    with _traced_peak() as traced:
        frames = sim.run(100, snapshot_every=1)  # type: ignore[attr-defined]
    peak = traced[0]
    assert frames.shape[0] == 101
    assert peak - frames.nbytes < frames.nbytes / 2, (peak, frames.nbytes)


# ---------------------------------------------------------------------------
# Every public record of the library
# ---------------------------------------------------------------------------


def _public_classes() -> list[type]:
    found: dict[int, type] = {}
    for module_info in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if any(part.startswith("_") for part in module_info.name.split(".")):
            continue
        module = importlib.import_module(module_info.name)
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name, None)
            if isinstance(obj, type):
                found[id(obj)] = obj
    return sorted(found.values(), key=lambda cls: f"{cls.__module__}.{cls.__name__}")


def test_every_public_record_that_copies_composes_its_own_hook() -> None:
    """The copy is wrapped around every class's ``__post_init__``, none lost.

    A class whose own hook replaced the composed one would build without
    copying; the composed hooks are the ones the mechanism registered.
    """
    records = [cls for cls in _public_classes() if issubclass(cls, OwnsArrays)]
    assert len(records) > 400
    lost = [
        cls.__name__ for cls in records if cls.__post_init__ not in frozen._COMPOSED
    ]
    assert lost == []
    assert all(dataclasses.is_dataclass(cls) for cls in records)


def _built_by_hand() -> dict[str, tuple[Callable[[np.ndarray], object], str]]:
    """Public records, each built from one writeable array, and the field
    that keeps it.
    """
    from phonometry import (
        aircraft,
        building,
        emission,
        environment,
        materials,
        noise_control,
        room,
        simulation,
    )

    return {
        "ANPNPDCurves": (
            lambda a: aircraft.ANPNPDCurves(
                aircraft_id="A",
                npd_id="N",
                metric="SEL",
                operation="D",
                power_parameter="lbf",
                powers=np.array([1.0, 2.0]),
                distances_m=a,
                levels=np.zeros((2, 3)),
            ),
            "distances_m",
        ),
        "EPNLResult": (
            lambda a: aircraft.EPNLResult(
                frequencies=a,
                times=np.arange(3.0),
                pnl=np.zeros(3),
                tone_correction=np.zeros(3),
                pnlt=np.zeros(3),
                pnltm=0.0,
                bandsharing_adjustment=0.0,
                duration_correction=0.0,
                epnl=0.0,
                band_limits=(0, 2),
            ),
            "frequencies",
        ),
        "WeightedRatingResult": (
            lambda a: building.WeightedRatingResult(
                rating=50,
                c=-1,
                ctr=-4,
                # 30 - 10, 30 - 20 and nothing at 30: the sum of the
                # unfavourable deviations of the measured curve given.
                unfavorable_sum=30.0,
                frequencies=np.array([500.0, 1000.0, 2000.0]),
                measured=a,
                shifted_reference=np.full(3, 30.0),
            ),
            "measured",
        ),
        "ImpulseResponseResult": (
            lambda a: room.ImpulseResponseResult(ir=a, fs=48000, method="farina"),
            "ir",
        ),
        "OpenPlanResult": (
            lambda a: room.OpenPlanResult(
                d2s=6.0, lp_as_4m=48.0, rd=5.0, rp=9.0, positions_m=a
            ),
            "positions_m",
        ),
        "DuctPathStage": (
            lambda a: noise_control.DuctPathStage(
                label="bend",
                code="B",
                attenuation=a,
                attenuated=np.zeros(3),
                self_noise=np.zeros(3),
                levels=np.zeros(3),
            ),
            "attenuation",
        ),
        "TransferMatrix": (
            lambda a: materials.TransferMatrix(
                t11=a, t12=np.ones(3), t21=np.ones(3), t22=np.ones(3)
            ),
            "t11",
        ),
        "MetadiffuserResult": (
            lambda a: materials.MetadiffuserResult(
                frequencies=a,
                reflection=np.ones(3, dtype=complex),
                absorption=np.zeros(3),
                well_absorption=np.zeros(3),
                wells=(None,),
                depth_m=0.1,
                period_m=0.1,
            ),
            "frequencies",
        ),
        "EmissionPressureResult": (
            lambda a: emission.EmissionPressureResult(
                level=a,
                measured_level=a,
                background_correction=0.0,
                local_correction=0.0,
                grade="engineering",
                background_margin_db=15.0,
                standard="ISO 11201",
            ),
            "level",
        ),
        "RailwayTrack": (
            lambda a: environment.RailwayTrack(
                rail_roughness=environment.WavelengthSpectrum(
                    wavelengths_mm=np.arange(1.0, 4.0), levels=np.zeros(3)
                ),
                track_transfer=a,
            ),
            "track_transfer",
        ),
        "FDTDResult": (
            lambda a: simulation.FDTDResult(
                times=np.arange(3.0),
                pressures=a.reshape(1, 3),
                probes=np.array([[0, 0]]),
                probe_positions=np.array([[0.0, 0.0]]),
                dx=0.01,
                dt=1e-5,
                shape=(4, 4),
                sources=(),
                snapshots=None,
                snapshot_times=None,
                obstacle_mask=None,
                snapshot_decimation=1,
                provenance=simulation.RunProvenance(
                    host=None,
                    device="cpu",
                    device_index=0,
                    dtype="float64",
                    numpy_version=np.__version__,
                    array_library=None,
                    cuda_runtime=None,
                    cuda_driver_api=None,
                    gpu=None,
                    package_sha256=None,
                ),
            ),
            "pressures",
        ),
    }


def _first_array(value: object) -> np.ndarray:
    if isinstance(value, tuple):
        value = value[0]
    assert isinstance(value, np.ndarray)
    return value


@pytest.mark.parametrize("name", sorted(_built_by_hand()))
def test_a_public_record_built_by_hand_does_not_follow_the_caller(name: str) -> None:
    build, field_name = _built_by_hand()[name]
    caller = _writeable([10.0, 20.0, 30.0])
    record = build(caller)
    kept = _first_array(getattr(record, field_name))
    before = kept.copy()
    caller[:] = -1.0
    np.testing.assert_array_equal(kept, before)
    assert not np.shares_memory(kept, caller)
    assert not kept.flags.writeable
    assert caller.flags.writeable


def _calibration_with(corrections: Mapping[str, np.ndarray]) -> dict[str, object]:
    """The two calibration records, each holding *corrections* as given."""
    from phonometry import metrology

    frequencies = np.array([250.0, 500.0, 1000.0])
    return {
        "ReciprocityCalibration": metrology.ReciprocityCalibration(
            frequencies=frequencies,
            sensitivity_v_per_pa=np.ones((3, 3)),
            products_v2_per_pa2=np.ones((3, 3)),
            field="pressure",
            method="three_microphones",
            corrections=corrections,
        ),
        "ComparisonCalibration": metrology.ComparisonCalibration(
            frequencies=frequencies,
            reference_sensitivity_level=np.full(3, -38.0),
            output_level_differences=np.zeros(3),
            pressure_level_difference=np.zeros(3),
            corrections=corrections,
            field="pressure",
            excitation="sequential",
        ),
    }


@pytest.mark.parametrize(
    "record_name", ["ReciprocityCalibration", "ComparisonCalibration"]
)
@pytest.mark.parametrize(
    "kind",
    [dict, OrderedDict, lambda items: defaultdict(float, items)],
    ids=["dict", "OrderedDict", "defaultdict"],
)
def test_a_calibration_built_by_hand_copies_the_corrections_of_any_mapping(
    record_name: str,
    kind: Callable[[dict[str, np.ndarray]], Mapping[str, np.ndarray]],
) -> None:
    mine = _writeable([0.1, 0.2, 0.3])
    record = _calibration_with(kind({"wave_motion": mine}))[record_name]
    kept = record.corrections["wave_motion"]  # type: ignore[attr-defined]
    assert mine.flags.writeable
    assert not np.shares_memory(kept, mine)
    mine[0] = 99.0
    assert kept[0] == pytest.approx(0.1)


def test_a_signal_a_record_is_handed_is_held_whole() -> None:
    """Composition: a record keeps a Signal as it keeps any record it is given.

    The Signal answers for its own samples, which it copied when it was built
    and keeps writeable, as every Signal does; the record makes no copy of
    it. A bare array in the same field is copied as any other.
    """
    from phonometry.signals import ResampledSignalResult

    def build(signal: object) -> ResampledSignalResult:
        return ResampledSignalResult(
            signal=signal,  # type: ignore[arg-type]
            fs=16000.0,
            original_fs=48000.0,
            up=1,
            down=3,
            filter_taps=np.ones(5),
            passband_edge_hz=7000.0,
            stopband_edge_hz=8000.0,
            stopband_attenuation=60.0,
            transition_width=0.1,
        )

    signal = io.Signal(np.zeros(8), fs=16000)
    held = build(signal)
    assert held.signal is signal
    assert held.signal.data.flags.writeable
    samples = _writeable([0.0, 1.0, 2.0])
    copied = build(samples)
    assert not np.shares_memory(copied.signal, samples)
    assert not copied.signal.flags.writeable  # type: ignore[union-attr]


def test_a_signal_a_function_returns_in_a_result_is_its_own() -> None:
    """The library builds the Signal it returns, so it shares nothing with
    the input; its samples stay writeable, as every Signal's do.
    """
    from phonometry import signals

    given = io.Signal(np.sin(np.arange(480) * 0.1), fs=48000)
    result = signals.resample_signal(given, fs_new=24000)
    assert isinstance(result.signal, io.Signal)
    assert not np.shares_memory(result.signal.data, given.data)
    assert result.signal.data.flags.writeable
    assert not result.filter_taps.flags.writeable


def test_a_signal_handed_to_an_array_field_keeps_its_samples_writeable() -> None:
    """A record that seals what ``np.asarray`` gives it never seals a Signal's
    own samples, multichannel included, and keeps a copy of its own.
    """
    from phonometry.environment.sources.rolling_stock_noise import (
        PassByMeasurement,
    )

    signal = io.Signal(np.ones((2, 4)), fs=48000)
    record = PassByMeasurement(
        times=signal,  # type: ignore[arg-type]
        levels=np.zeros(3),
        start_s=0.0,
        end_s=1.0,
        equivalent_level=0.0,
        max_level=0.0,
        front_level=0.0,
        rear_level=0.0,
        record_start_level=0.0,
        record_end_level=0.0,
    )
    assert signal.data.flags.writeable
    assert not np.shares_memory(record.times, signal.data)
    signal.data[0, 0] = 5.0
    assert record.times[0, 0] == 1.0
