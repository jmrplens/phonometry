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
of the library or a caller writing the record by hand. An object that is not
such a record (a plain class, a private record) keeps an array it was handed
through :func:`read_only_copy`. ``scripts/check_array_aliasing.py`` holds the
package to both.
"""

from __future__ import annotations

import dataclasses
import functools
import weakref
from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, overload

import numpy as np

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

    :param array: The array, or anything ``np.array`` reads as one, that an
        object keeps from its arguments.
    :param dtype: The type to copy into; the array's own when omitted.
    :return: A new read-only array, or ``None``.
    """
    if array is None:
        return None
    return read_only(np.array(array, dtype=dtype))


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


def _owned(value: object, *, always: bool) -> object:
    """*value* with every array in it replaced by a read-only copy of its own.

    An array, and an array inside a tuple, a list or any mapping (to any
    depth), is copied; with *always* false only an array somebody can still
    write into is. The copy is C-ordered whatever the layout it was made
    from, so a record holds the same layout however it was built. The
    container is rebuilt around the copies only when something in it was
    copied, so a tuple of numbers or of records is handed back as it came: a
    named tuple as its own class, a
    :class:`~types.MappingProxyType` as one, and any other mapping (an
    ``OrderedDict``, a ``defaultdict``, a mapping of the caller's own) as a
    plain ``dict``, which never shares the caller's container. Anything else,
    a record included, is left as it is: a record held whole is composition,
    and the record answers for its own arrays.
    """
    if isinstance(value, np.ndarray):
        return _owned_array(value, always=always)
    if isinstance(value, tuple | list):
        return _owned_sequence(value, always=always)
    if isinstance(value, Mapping):
        return _owned_mapping(value, always=always)
    return value


def _owned_array(value: np.ndarray, *, always: bool) -> np.ndarray:
    """*value*, or a read-only C-ordered copy of it when one is due."""
    if always or not _sealed(value):
        return read_only(np.array(value, order="C"))
    return value


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
    holds is replaced by a read-only copy, so the class validates and
    normalises the record's own arrays: ``np.asarray(self.levels_db)`` is
    that copy, and ``read_only`` on it touches nobody else's array. After,
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


class OwnsArrays:
    """A frozen dataclass that keeps a read-only copy of its own of every array.

    Inherited by every public record of the library that can hold an array.
    Whoever builds the record, a function of the library or a caller writing
    ``SomeResult(levels_db=levels, ...)`` by hand, each array it is given
    (also inside a tuple, a list or a mapping) is replaced by a copy that
    refuses in-place writes, before the class's own ``__post_init__`` runs.
    The caller's array is never flagged, and nothing the caller does to it
    afterwards reaches the record. A record held in a field is left as it
    is, an :class:`~phonometry.io.Signal` included: that is composition, the
    held record answers for its own arrays, and a Signal's samples stay
    writeable as every Signal's do. A class that defines its own
    ``__post_init__``, or inherits one, keeps it: the copy is composed
    around it when the class is created, never in its place. The class goes
    last among the bases, so that a ``__post_init__`` of another base is the
    one composed.
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
    if isinstance(value, MappingProxyType):
        return dict(value)
    if isinstance(value, tuple) and any(isinstance(v, MappingProxyType) for v in value):
        return tuple(_thawed(v) for v in value)
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
