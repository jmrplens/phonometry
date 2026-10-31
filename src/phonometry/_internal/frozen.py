#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Read-only arrays for the tables and the results the library publishes (private).

A module-level array is shared by every caller that imports it, so an
in-place operation on it (``OCTAVE_BANDS *= 2``, or a function that writes
into the array it was handed) changes the table for the rest of the process,
silently. Every published array is therefore built through :func:`read_only`,
the array counterpart of wrapping a published dictionary in
:class:`types.MappingProxyType`.

A result has the opposite exposure. ``np.asarray`` hands back the caller's own
array when it is already of the asked type, so a result that keeps what it
was given shares memory with the caller, and changing the caller's array
afterwards changes the result. Every public record that can hold an array
therefore inherits :class:`OwnsArrays`, which replaces each array the record
is built with by a read-only copy of its own, whoever builds it: a function
of the library or a caller writing the record by hand. Any other object
numpy reads as an array (a column of a data frame, a labelled array, a
``memoryview``) counts as the array it stands for, since ``np.asarray`` of it
is the caller's own memory. An object that is not
such a record (a plain class, a private record) keeps an array it was handed
through :func:`read_only_copy`. ``scripts/check_array_aliasing.py`` holds the
package to both.

The one array a record keeps without copying is one a function of the
library built for it and passes through :func:`handed_over`: the frames of
a simulation, the field of a march, which nobody else can reach, so that a
result of several hundred megabytes is not held twice while it is built.
The check holds every such call to that.
"""

from __future__ import annotations

import dataclasses
import functools
import weakref
from collections.abc import Buffer, Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast, overload

import numpy as np

from .display import RichDisplay

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from numpy.typing import ArrayLike, DTypeLike, NDArray


def read_only[A: np.ndarray](array: A) -> A:
    """Return *array* with its ``writeable`` flag cleared.

    The array is not copied: the flag is cleared on the object itself, so the
    caller hands over a freshly built array and keeps no writeable reference
    to it. The array still owns its data, so a caller who sets the flag back
    on can write again; what this stops is the accident, an in-place operation
    nobody meant to aim at a shared table.

    Never hand it an array that came in as an argument: it would clear the
    flag on the caller's own array. :func:`read_only_copy` is for those.

    :param array: A newly built array that is about to be published.
    :return: The same array, which now refuses in-place writes.
    """
    array.flags.writeable = False
    return array


@overload
def read_only_copy(array: None, dtype: DTypeLike | None = None) -> None: ...


@overload
def read_only_copy(
    array: ArrayLike, dtype: DTypeLike | None = None
) -> NDArray[Any]: ...


def read_only_copy(
    array: ArrayLike | None, dtype: DTypeLike | None = None
) -> NDArray[Any] | None:
    """A copy of *array* that refuses in-place writes, for an object to keep.

    The copy is the object's own, so nothing the caller does to the array it
    passed reaches the object, and the flag is cleared on the copy, never on
    the caller's array. ``None``, an optional field left out, stays ``None``.

    A record that inherits :class:`OwnsArrays` makes this copy itself, so an
    array handed to one goes in as it is; this is for the objects that do
    not: a plain class that keeps an array to hand out later, a private
    record.

    An array of objects is copied member by member as well, as a record
    copies one: a copy of it alone would hold the caller's own arrays.

    Any other object numpy reads as an array (:func:`_stands_for_an_array`)
    is read as ``np.asarray`` reads it, and what comes back is copied:
    ``np.array`` would pass an ``__array__`` ``copy=True``, which an
    implementation older than NumPy 2 does not take (NumPy warns) and a
    careless one ignores, handing back the array it holds, which would then
    be sealed.

    :param array: The array, or anything ``np.array`` reads as one, that an
        object keeps from its arguments.
    :param dtype: The type to copy into; the array's own when omitted.
    :return: A new read-only array, or ``None``.
    """
    if array is None:
        return None
    if _stands_for_an_array(array):
        array = np.asarray(array, dtype=dtype)
    copied = np.array(array, dtype=dtype)
    if copied.dtype == object:
        return _owned_objects(copied, always=True)
    return read_only(copied)


def owned_members(value: Iterable[Any]) -> tuple[Any, ...]:
    """The members of a sequence a record holds, as a tuple, every array its own.

    For the ``__post_init__`` of a record that inherits :class:`OwnsArrays`,
    on one of its fields. A tuple, a list or an array the record was given
    is one it went through when it copied its arrays, so each array it
    holds, and each array-like (read as the array it stands for), is the
    record's own already and comes back as it is. Any other sequence (a
    deque, a generator) the record could not go through, so each array or
    array-like in it is still the caller's and is copied here, read-only: a
    record that keeps it, or seals it, never keeps or seals an array of the
    caller's.

    :param value: The field's value, any iterable.
    :return: Its members, as a tuple.
    :raises TypeError: if *value* is not iterable.
    """
    if isinstance(value, tuple | list | np.ndarray):
        return tuple(value)
    # A plain tuple comes back from _owned as a plain tuple.
    return cast("tuple[Any, ...]", _owned(tuple(value), always=True))


#: The arrays a function of the library has handed to the record it is
#: building, by identity, until a record keeps one. Weak, so an array that
#: never reaches a record leaves no trace here.
_HANDED_OVER: weakref.WeakValueDictionary[int, np.ndarray] = (
    weakref.WeakValueDictionary()
)


@overload
def handed_over(array: None) -> None: ...


@overload
def handed_over[A: np.ndarray](array: A) -> A: ...


def handed_over(array: np.ndarray | None) -> np.ndarray | None:
    """Let the record *array* is passed to keep it as it is, without a copy.

    A record that inherits :class:`OwnsArrays` copies every array it is
    built with, so a factory that builds a large array itself (the frames a
    simulation records, the field a march fills) would hold the result
    twice while the record is built. Passed through this function, the array
    becomes the record's own: it is sealed with :func:`read_only` instead of
    copied. That is only right for an array nobody else can reach, and
    ``scripts/check_array_aliasing.py`` holds every call to that: the call is
    an argument of the record the function returns, and its argument is a
    name bound once, to a new array (``np.zeros``, ``np.empty`` or
    ``np.ones``), that the function, or an undecorated helper of the package
    it is passed to, only ever writes into.

    The first record the array reaches keeps it; a second one copies it, as
    it does an array that does not own its memory or is not C-ordered.

    :param array: The new array, or ``None`` for an optional field left out.
    :return: The same array, or ``None``.
    """
    if array is not None:
        _HANDED_OVER[id(array)] = array
    return array


def _adopted(array: np.ndarray) -> np.ndarray | None:
    """*array* sealed as it is, if it was handed over, else ``None``.

    The mark is taken off as it is read, so only the first record the array
    reaches keeps it. An array that is a view of another's memory, or not
    C-ordered, is not kept (the record copies it all the same), so a record
    holds the same layout however it was built.
    """
    if _HANDED_OVER.pop(id(array), None) is not array:
        return None
    if not (array.flags.owndata and array.flags.c_contiguous):
        return None
    return read_only(array)


def _sealed(array: np.ndarray) -> bool:
    """Whether nobody can write into *array* through any name it has.

    It is read-only, and so is every array it is a view of: a read-only view
    of a writeable array still changes when the array under it does. The
    walk goes through what NumPy puts between a view and its array (the
    stand-in a strided view such as ``sliding_window_view`` keeps, a
    ``memoryview``), and memory it cannot vouch for (a ``bytearray``, a
    mapped file) counts as writeable; only ``bytes`` is known never to
    change.
    """
    current: object = array
    while current is not None:
        if isinstance(current, np.ndarray):
            if current.flags.writeable:
                return False
            current = current.base
        elif isinstance(current, memoryview):
            if not current.readonly:
                return False
            current = current.obj
        elif isinstance(current, bytes):
            return True
        elif hasattr(current, "__array_interface__") and hasattr(current, "base"):
            # numpy's DummyArray, which a strided view keeps as its base.
            current = current.base
        else:
            return False
    return True


#: The attributes through which numpy reads an object as an array, each
#: looked up on the object as numpy looks it up; the buffer protocol is the
#: fourth way in.
_ARRAY_PROTOCOLS = ("__array__", "__array_interface__", "__array_struct__")

#: The types of the values a record holds most, none of which is an array
#: or holds one, so a field of one is passed by at once. The type is
#: matched exactly: a subclass of one may read as an array, and goes the
#: long way.
_PLAIN_TYPES = frozenset({type(None), bool, int, float, complex, str, bytes})


def _stands_for_an_array(value: object) -> bool:
    """Whether numpy reads *value* as an array, other than an ndarray itself.

    A column of a data frame, a labelled array or a tensor (through
    ``__array__``), an object that publishes its memory (through
    ``__array_interface__`` or ``__array_struct__``), a ``memoryview``, an
    ``array.array`` or a ``bytearray`` (the buffer protocol):
    ``np.asarray`` of one is the caller's own memory, and of a column whose
    ``__array__`` hands back the array it holds, the caller's very array. A
    hook that sealed what ``np.asarray`` gave it sealed the caller's array,
    and a hook that only checked the object left the record holding it, and
    the caller's memory with it. ``bytes`` is a single text to numpy and
    never changes, a NumPy scalar is a number, never shared, and a record of
    the library (an :class:`~phonometry.io.Signal` included) is composition
    and answers for its own arrays; none of them counts.
    """
    if isinstance(value, np.ndarray | np.generic | bytes | RichDisplay):
        return False
    return isinstance(value, Buffer) or any(
        hasattr(value, name) for name in _ARRAY_PROTOCOLS
    )


def _owned(value: object, *, always: bool) -> object:
    """*value* with every array in it replaced by a read-only copy of its own.

    An array, and an array inside a tuple, a list, any mapping or an array
    of objects (to any depth), is copied; with *always* false only an array
    somebody can still write into is. Any other object numpy reads as an
    array (:func:`_stands_for_an_array`) is read as ``np.asarray`` reads it,
    the way the class's own hook would, and what comes back is copied,
    always: nothing tells whether the caller still holds it. The copy is C-ordered whatever the
    layout it was made from, so a record holds the same layout however it
    was built. The
    container is rebuilt around the copies only when something in it was
    copied, so a tuple of numbers or of records is handed back as it came: a
    named tuple as its own class, a
    :class:`~types.MappingProxyType` as one, and any other mapping (an
    ``OrderedDict``, a ``defaultdict``, a mapping of the caller's own) as a
    plain ``dict``, which never shares the caller's container. Anything else,
    a record included, is left as it is: a record held whole is composition,
    and the record answers for its own arrays. An array passed through
    :func:`handed_over` is the one exception: it is sealed, not copied.
    """
    if type(value) in _PLAIN_TYPES:
        return value
    if isinstance(value, np.ndarray):
        return _owned_array(value, always=always)
    if isinstance(value, tuple | list):
        return _owned_sequence(value, always=always)
    if isinstance(value, Mapping):
        return _owned_mapping(value, always=always)
    if _stands_for_an_array(value):
        return _owned_array(np.asarray(value), always=True)
    return value


def _owned_array(value: np.ndarray, *, always: bool) -> np.ndarray:
    """*value*, or a read-only C-ordered copy of it when one is due.

    An array passed through :func:`handed_over` is sealed as it is instead.
    """
    adopted = _adopted(value)
    if adopted is not None:
        return adopted
    if value.dtype == object:
        return _owned_objects(value, always=always)
    if always or not _sealed(value):
        return read_only(np.array(value, order="C"))
    return value


def _owned_objects(value: np.ndarray, *, always: bool) -> np.ndarray:
    """An array of objects, with every array it holds owned as a tuple's is.

    Copying an array of objects copies its references, not the objects, so
    the copy would still hold the caller's own arrays: a write by the caller
    would reach the record, and a hook that sealed a member would seal the
    caller's array. Each member goes through :func:`_owned` instead, and the
    array is rebuilt, C-ordered and read-only, around what comes back; with
    *always* false it is kept as it is when it is sealed and none of its
    members was copied.
    """
    members = [_owned(member, always=always) for member in value.flat]
    if (
        not always
        and _sealed(value)
        and all(new is old for new, old in zip(members, value.flat, strict=True))
    ):
        return value
    held = np.empty(value.shape, dtype=object)
    # One element at a time: an array assigned to a slice would be spread
    # over it instead of held whole.
    for index, member in zip(np.ndindex(value.shape), members, strict=True):
        held[index] = member
    return read_only(held)


def _owned_sequence(
    value: tuple[object, ...] | list[object], *, always: bool
) -> object:
    """*value* rebuilt around its owned items, or itself when none was copied."""
    items = [_owned(item, always=always) for item in value]
    if all(new is old for new, old in zip(items, value, strict=True)):
        return value
    if isinstance(value, list):
        return items
    make = getattr(type(value), "_make", None)
    return make(items) if make is not None else tuple(items)


def _owned_mapping(value: Mapping[object, object], *, always: bool) -> object:
    """*value* rebuilt around its owned values, or itself when none was copied."""
    pairs = {key: _owned(item, always=always) for key, item in value.items()}
    if all(pairs[key] is item for key, item in value.items()):
        return value
    return MappingProxyType(pairs) if isinstance(value, MappingProxyType) else pairs


#: The init fields and all the fields of each record class, read once.
_FIELDS: weakref.WeakKeyDictionary[type, tuple[tuple[str, ...], tuple[str, ...]]] = (
    weakref.WeakKeyDictionary()
)

_MISSING = object()

#: Every ``__post_init__`` that already copies, so that a subclass inheriting
#: one does not wrap it a second time.
_COMPOSED: weakref.WeakSet[Callable[..., None]] = weakref.WeakSet()


def _field_names(cls: type) -> tuple[tuple[str, ...], tuple[str, ...]]:
    names = _FIELDS.get(cls)
    if names is None:
        fields = dataclasses.fields(cls)
        names = (
            tuple(f.name for f in fields if f.init),
            tuple(f.name for f in fields),
        )
        _FIELDS[cls] = names
    return names


def _take_ownership(
    record: object, hook: Callable[..., None] | None, args: tuple[object, ...]
) -> None:
    """Copy the record's arrays, run its own ``__post_init__``, then seal.

    Before the class's own ``__post_init__`` runs, every array an init field
    holds, and every array-like numpy reads as one, is replaced by a
    read-only copy (or, handed over, sealed as it is), so the class
    validates and normalises the record's own arrays:
    ``np.asarray(self.levels)`` is that copy, and ``read_only`` on it
    touches nobody else's array. After,
    every field is looked at once more, and an array somebody can still
    write into, one the class built and stored without sealing it or one it
    took from elsewhere, is copied too.
    """
    init, every = _field_names(type(record))
    for name in init:
        value = getattr(record, name, _MISSING)
        kept = _owned(value, always=True)
        if kept is not value:
            object.__setattr__(record, name, kept)
    if hook is not None:
        hook(record, *(_owned(arg, always=True) for arg in args))
    for name in every:
        value = getattr(record, name, _MISSING)
        kept = _owned(value, always=False)
        if kept is not value:
            object.__setattr__(record, name, kept)


def _composed(hook: Callable[..., None]) -> Callable[..., None]:
    """The class's own ``__post_init__`` with the copy around it."""

    @functools.wraps(hook)
    def __post_init__(self: object, *args: object) -> None:
        if getattr(type(self), "__post_init__", None) is not __post_init__:
            # Reached through ``super().__post_init__()`` from a subclass
            # whose own composed hook is already copying.
            hook(self, *args)
            return
        _take_ownership(self, hook, args)

    _COMPOSED.add(__post_init__)
    return __post_init__


class OwnsArrays(RichDisplay):
    """A frozen dataclass that keeps a read-only copy of its own of every array.

    Inherited by every public record of the library that can hold an array.
    Whoever builds the record, a function of the library or a caller writing
    ``SomeResult(levels=levels, ...)`` by hand, each array it is given
    (also inside a tuple, a list, a mapping or an array of objects), and
    each other object numpy reads as an array (a column of a data frame, a
    ``memoryview``), is replaced by a copy that refuses in-place writes,
    before the class's own ``__post_init__`` runs;
    only an array a function of the library builds for it and passes
    through :func:`handed_over` is sealed and kept instead.
    The caller's array is never flagged, and nothing the caller does to it
    afterwards reaches the record. A record held in a field is left as it
    is, an :class:`~phonometry.io.Signal` included: that is composition, the
    held record answers for its own arrays, and a Signal's samples stay
    writeable as every Signal's do. A class that defines its own
    ``__post_init__``, or inherits one, keeps it: the copy is composed
    around it when the class is created, never in its place. The class goes
    last among the bases, so that a ``__post_init__`` of another base is the
    one composed. It extends :class:`~phonometry._internal.display.RichDisplay`,
    so a record that copies its arrays also shows itself as a table in a
    notebook.
    """

    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        hook = cls.__post_init__
        if hook in _COMPOSED:
            mro = cls.__mro__
            later = [
                base.__name__
                for base in mro[mro.index(OwnsArrays) + 1 :]
                if "__post_init__" in vars(base)
            ]
            if hook is OwnsArrays.__post_init__ and later:
                msg = (
                    f"{cls.__name__} lists OwnsArrays before {', '.join(later)}, "
                    "whose __post_init__ would never run; list OwnsArrays last"
                )
                raise TypeError(msg)
            return
        type.__setattr__(cls, "__post_init__", _composed(hook))

    def __post_init__(self) -> None:
        """Replace every array of the record by a read-only copy of its own."""
        if type(self).__post_init__ is not OwnsArrays.__post_init__:
            # Reached through ``super().__post_init__()`` from a subclass
            # whose own composed hook is already copying.
            return
        _take_ownership(self, None, ())

    def __setstate__(self, state: object) -> None:
        """Restore a pickled or deep-copied record with its arrays read-only again.

        ``pickle`` and ``copy.deepcopy`` rebuild a record from its fields
        without running ``__post_init__``, and NumPy hands every array back
        writeable, so a record that came back from a process pool or a cache
        held arrays anyone could write into. Each array is sealed again here,
        inside a tuple, a list, a mapping or an array of objects too, as the
        constructor seals it;
        a record held in a field answers for its own arrays, as it does when
        the record is built.

        :param state: The state ``object.__reduce_ex__`` gave: the instance
            dictionary, or a ``(dictionary, slots)`` pair.
        """
        dictionary, slots = state if isinstance(state, tuple) else (state, None)
        for part in (dictionary, slots):
            if not isinstance(part, Mapping):
                continue
            for name, value in part.items():
                object.__setattr__(self, name, _owned(value, always=False))


_COMPOSED.add(OwnsArrays.__post_init__)


def frozen_rows(rows: Iterable[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    """Read-only copies of the rows a result keeps, for a verdict read from them.

    A frozen dataclass stops a field from being rebound, not a dictionary in
    it from being edited, so a verdict read from its rows would follow a
    write into one of them after it was reached. Each row is copied, so the
    caller's dictionaries stay theirs, and wrapped in
    :class:`types.MappingProxyType`.

    :param rows: The rows, each a mapping.
    :return: A tuple of read-only copies.
    """
    return tuple(MappingProxyType(dict(row)) for row in rows)


def frozen_row(row: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    """A read-only copy of one row a result keeps, or ``None``."""
    return None if row is None else MappingProxyType(dict(row))


def _thawed(value: object) -> object:
    """*value* with every read-only mapping in it a plain dictionary, at any depth.

    A mapping held in a mapping, or in a tuple, is thawed too, so that a
    table of tables pickles as a whole; a named tuple, a record or an array
    is left as it is, since it pickles by itself.
    """
    if isinstance(value, MappingProxyType | dict):
        return {key: _thawed(item) for key, item in value.items()}
    if type(value) is tuple:
        return tuple(_thawed(item) for item in value)
    return value


def _rebuilt[T](cls: type[T], kwargs: dict[str, Any]) -> T:
    return cls(**kwargs)


def reduce_with_plain_rows(
    result: object,
) -> tuple[Any, tuple[type, dict[str, Any]]]:
    """``__reduce__`` for a dataclass result that keeps read-only rows.

    A :class:`types.MappingProxyType` can be neither pickled nor deep-copied,
    so the result travels as its fields with every row a plain dictionary,
    and its ``__post_init__`` freezes them again on arrival.

    :param result: A dataclass instance whose rows were frozen by
        :func:`frozen_rows` or :func:`frozen_row`.
    :return: The callable and arguments that rebuild it by keyword.
    """
    kwargs = {
        field.name: _thawed(getattr(result, field.name))
        for field in dataclasses.fields(result)  # type: ignore[arg-type]
        if field.init
    }
    return _rebuilt, (type(result), kwargs)
