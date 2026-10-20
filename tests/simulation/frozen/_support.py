#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Verbatim copies of what the frozen engines read, frozen with them.

The engines in this package are the FDTD engines as they stood before they
learned to run on other array backends. They read these helpers, so the
helpers are frozen too: a later change to a validation helper must not move
the numbers the frozen engines give. Deleted with the frozen engines once
the golden digests replace them.
"""

from __future__ import annotations

import dataclasses
import functools
import math
import weakref
from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast, overload

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Callable

    from numpy.typing import ArrayLike, DTypeLike, NDArray


class RichDisplay:
    """Stand-in for the library's notebook display mixin: display only, no numbers."""


# From src/phonometry/_internal/validation.py.


def is_scalar(value: object) -> bool:
    """True when *value* has no axes: one number, not an array holding one.

    :func:`float` is not this test, although guards through the tree used it
    as one. Whether it refuses a one-element array depends on numpy: 2.4 raises
    ``TypeError``, while 2.0 to 2.3 convert ``np.array([54.0])`` to ``54.0``
    with no more than a ``DeprecationWarning``. A guard that left the refusal to
    :func:`float` therefore accepted a per-band array on one install and
    refused it on the next. The rank answers the same on every numpy.

    A ragged nested sequence, to which numpy can give no rank, has axes as far
    as this is concerned.

    :param value: The value to test, of any type.
    :return: ``True`` when ``value`` has rank 0, ``False`` otherwise.
    """
    try:
        return int(np.ndim(cast("ArrayLike", value))) == 0
    except ValueError:
        return False


def holds_text(value: object) -> bool:
    """True when *value* is text, or an array that holds text.

    A ``str`` or ``bytes``, a numpy array of a string dtype, or an object
    array with a ``str`` or ``bytes`` element. Text is the wrong type where a
    number belongs, whatever it reads as: :func:`float` and ``np.asarray(...,
    dtype=float)`` parse it, which is what they are for, but a guard is not a
    parser, and ``math.sqrt("4")`` and ``np.sqrt("4")`` refuse it with
    :class:`TypeError` as a numerical function does.

    :param value: The value to test, of any type.
    :return: Whether *value* is or holds text.
    """
    if isinstance(value, (str, bytes)):
        return True
    if not isinstance(value, np.ndarray):
        return False
    kind = value.dtype.kind
    if kind in "SU":
        return True
    return kind == "O" and any(isinstance(item, (str, bytes)) for item in value.flat)


def require_real(value: object, msg: str) -> float:
    """*value* as a ``float``, or a refusal worded *msg* when it is not one number.

    The coercion a guard means when it hands a caller's value to
    :func:`float` and renames the failure: the rank is asked first, through
    :func:`is_scalar`, so that a one-element array is refused on every numpy
    rather than only on those where :func:`float` happens to refuse it.

    The refusal keeps the class the mistake has. An array, ``None``, a text
    (whether or not it reads as a number, see :func:`holds_text`) or any other
    object :func:`float` cannot take is the wrong type, and is refused with
    :class:`TypeError`; a number too large for a float is a value of the
    right type, and is refused with :class:`ValueError`.

    :param value: The caller's value, of any type.
    :param msg: The refusal, worded by the guard that owns the parameter.
    :return: ``float(value)``.
    :raises TypeError: with *msg*, for an array of any shape, a text, or
        anything whose type :func:`float` refuses.
    :raises ValueError: with *msg*, for a number :func:`float` cannot hold.
    """
    if not is_scalar(value) or holds_text(value):
        raise TypeError(msg)
    try:
        return float(cast("float", value))
    except TypeError:
        raise TypeError(msg) from None
    except (ValueError, OverflowError):
        raise ValueError(msg) from None


def require_scalar(value: object, name: str) -> None:
    """Refuse an array or a text before a scalar guard reads it as one number.

    Every scalar guard opens with this. The guards test their value through
    :func:`float` or :mod:`math`, which converts it the same way, and so
    inherit the numpy dependence :func:`is_scalar` describes: a one-element
    array would be read as its element on numpy 2.0 to 2.3 and refused with an
    anonymous ``TypeError`` from 2.4 on. :func:`float` would also parse a
    text, ``"20"`` into a number and ``"fifty"`` into an anonymous
    ``ValueError``.

    An array or a text where one number is asked for is the wrong type, so it
    is refused with :class:`TypeError`, the class numpy 2.4 gives ``float()``
    of an array and ``math.sqrt`` gives a text. ``None`` passes, for the
    guards of an optional parameter to settle.

    :param value: The caller's value, of any type.
    :param name: Parameter name used in the error message.
    :raises TypeError: for an array of any shape, a ragged sequence included,
        or a text.
    """
    if not is_scalar(value):
        msg = f"'{name}' must be one number, not an array."
        raise TypeError(msg)
    if holds_text(value):
        msg = f"'{name}' must be one number, not a text."
        raise TypeError(msg)


def _one_number(value: object, name: str) -> float:
    """*value* as a ``float``, refused by name when it is not one number.

    What every shared scalar guard reads first. The rank is asked before the
    conversion (an array is refused on every numpy), a text is refused
    whatever it reads as (``"1000"`` as much as ``"fifty"``: a guard is not a
    parser), and what :func:`float` cannot take is refused with the
    parameter's name instead of the anonymous ``TypeError`` :mod:`math` would
    raise on it.

    :param value: The caller's value, of any type.
    :param name: Parameter name used in the error message.
    :return: ``float(value)``.
    :raises TypeError: for an array, a text, or anything whose type
        :func:`float` refuses.
    :raises ValueError: for a number too large for a float.
    """
    require_scalar(value, name)
    return require_real(value, f"'{name}' must be a number, got {value!r}.")


def require_positive(value: float, name: str) -> float:
    """Require a positive finite number (rejects NaN and infinities).

    :param value: The value to validate.
    :param name: Parameter name used in the error message.
    :return: The validated value as a ``float``.
    :raises TypeError: for a ``value`` that is an array, a text, or something
        else that is not a number.
    :raises ValueError: for a non-finite or non-positive value.
    """
    number = _one_number(value, name)
    if not math.isfinite(number) or number <= 0.0:
        msg = f"'{name}' must be positive."
        raise ValueError(msg)
    return number


def require_count(value: object, name: str, *, at_least: int | None = 1) -> int:
    """Require a whole number of things, at least *at_least*.

    An ``int`` or a numpy integer, or a float that is whole, such as 3.0;
    never a bool, a string, an array or a non-finite number. What is not a
    number at all is the wrong type and is refused with :class:`TypeError`;
    a number that is not whole, not finite or below *at_least* is the right
    type with the wrong value, and is refused with :class:`ValueError`.

    :param value: The value to validate.
    :param name: Parameter name used in the error message.
    :param at_least: The smallest count accepted, 1 by default; ``None`` for
        a whole number with no lower bound, such as a grid index whose range
        the caller checks against the grid.
    :return: The validated value as an ``int``.
    :raises TypeError: for a bool, a text, an array or anything else that is
        not a number.
    :raises ValueError: for a number that is not a whole number at or above
        *at_least*.
    """
    if isinstance(value, bool) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        msg = f"'{name}' must be a whole number, got {value!r}."
        raise TypeError(msg)
    floor = -math.inf if at_least is None else at_least
    if isinstance(value, (int, np.integer)):
        # Whole by its type, and read as an int: float() of one past 1e308
        # would overflow before the bound could name it.
        whole = int(value)
        if whole < floor:
            msg = (
                f"'{name}' must be a whole number, at least {at_least}, got {value!r}."
            )
            raise ValueError(msg)
        return whole
    number = float(value)
    if not math.isfinite(number) or not number.is_integer() or number < floor:
        least = "" if at_least is None else f", at least {at_least}"
        msg = f"'{name}' must be a whole number{least}, got {value!r}."
        raise ValueError(msg)
    return int(number)


# From src/phonometry/_internal/frozen.py.


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


#: The arrays a function of the library has handed to the record it is
#: building, by identity, until a record keeps one. Weak, so an array that
#: never reaches a record leaves no trace here.
_HANDED_OVER: weakref.WeakValueDictionary[int, np.ndarray] = (
    weakref.WeakValueDictionary()
)


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
    and the record answers for its own arrays. An array passed through
    :func:`handed_over` is the one exception: it is sealed, not copied.
    """
    if isinstance(value, np.ndarray):
        return _owned_array(value, always=always)
    if isinstance(value, tuple | list):
        return _owned_sequence(value, always=always)
    if isinstance(value, Mapping):
        return _owned_mapping(value, always=always)
    return value


def _owned_array(value: np.ndarray, *, always: bool) -> np.ndarray:
    """*value*, or a read-only C-ordered copy of it when one is due.

    An array passed through :func:`handed_over` is sealed as it is instead.
    """
    adopted = _adopted(value)
    if adopted is not None:
        return adopted
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
    holds is replaced by a read-only copy (or, handed over, sealed as it
    is), so the class validates and normalises the record's own arrays:
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
    (also inside a tuple, a list or a mapping) is replaced by a copy that
    refuses in-place writes, before the class's own ``__post_init__`` runs;
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


_COMPOSED.add(OwnsArrays.__post_init__)
