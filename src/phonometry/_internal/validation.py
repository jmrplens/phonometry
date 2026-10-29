#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Shared input-validation helpers (private).

Seeded by the library audit: modules used to hand-roll the same checks with
diverging NaN semantics and error-message styles. New code should validate
through these helpers; existing modules migrate as they are touched.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Set
from typing import TYPE_CHECKING, Any, TypeGuard, cast

import numpy as np

from .frozen import owned_members

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import ArrayLike, NDArray

    from .types import BandFraction, ReportEngine


def is_positive(value: float) -> bool:
    """True only for a value strictly above zero. NaN answers ``False``.

    The guards through the tree are written ``if not is_positive(x)`` rather
    than ``if x <= 0.0`` because the two are not the same test. A NaN compares
    False against everything, so ``x <= 0.0`` lets it through and
    ``not is_positive(x)`` refuses it, which is the behaviour those guards were
    given the day a NaN geometry got past the plain form and came out in the
    result. Naming the predicate keeps that reasoning in one place instead of
    leaving an inverted comparison at every site for a reader to re-derive.

    Infinity is a separate question: it is strictly above zero and passes here,
    so a caller that also has to refuse it says so by name.

    :param value: The value to test.
    :return: ``True`` when ``value > 0``, ``False`` for zero, a negative value
        and NaN.
    """
    return value > 0.0


def is_at_most(value: float, limit: float) -> bool:
    """True when ``value`` is at or below ``limit``. NaN answers ``False``.

    The companion of :func:`is_positive` for an upper bound, and it exists for
    the same reason: ``not is_at_most(x, limit)`` treats a NaN as a value that
    failed to qualify, which is what a criterion that cannot be evaluated
    should do.

    :param value: The value to test.
    :param limit: The upper bound, inclusive.
    :return: ``True`` when ``value <= limit``, ``False`` above it and for NaN.
    """
    return value <= limit


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


def refuse_text(value: object, msg: str) -> None:
    """Refuse a text, or a sequence or array that holds one, with *msg*.

    For the conversions that parse what they are given (``np.asarray(x,
    dtype=complex)`` reads ``"1"`` as ``1+0j``) where a number belongs: see
    :func:`holds_text`. A ragged nesting is left to the conversion that
    follows, which refuses it on its own terms.

    :param value: The caller's value, of any type.
    :param msg: The refusal, worded by the guard that owns the parameter.
    :raises TypeError: with *msg*, for a text or anything that holds one.
    """
    if isinstance(value, np.ndarray):
        found = holds_text(value)
    elif isinstance(value, (str, bytes)):
        found = True
    else:
        try:
            found = holds_text(np.asarray(value, dtype=object))
        except ValueError:
            return
    if found:
        raise TypeError(msg)


def holds_complex(value: object) -> bool:
    """True when *value* is a complex number, or an array that holds one.

    A Python ``complex``, a NumPy complex scalar, a NumPy array of a complex
    dtype, or an object array with a complex element. NumPy reads a complex
    value as a real one with no more than a ``ComplexWarning``:
    ``float(np.complex128(343 + 50j))`` is ``343.0``, and so is each element
    of ``np.asarray(z, dtype=np.float64)``, so a guard that converts first
    checks a medium, a level or a rate the caller never gave. A complex value
    where a real one belongs is the wrong type, as a text is.

    :param value: The value to test, of any type.
    :return: Whether *value* is or holds a complex number.
    """
    if isinstance(value, complex | np.complexfloating):
        return True
    if not isinstance(value, np.ndarray):
        return False
    kind = value.dtype.kind
    if kind == "c":
        return True
    return kind == "O" and any(
        isinstance(item, complex | np.complexfloating) for item in value.flat
    )


def refuse_complex(value: object, msg: str) -> None:
    """Refuse a complex number, or a sequence or array that holds one, with *msg*.

    For the conversions that read a complex value as its real part
    (``np.asarray(z, dtype=np.float64)``, ``float(np.complex128(z))``) where a
    real number belongs: see :func:`holds_complex`. A sequence is read as
    the objects it holds, so a list of NumPy complex numbers is found as an
    array of them is. A ragged nesting is left to the conversion that
    follows, which refuses it on its own terms.

    :param value: The caller's value, of any type.
    :param msg: The refusal, worded by the guard that owns the parameter.
    :raises TypeError: with *msg*, for a complex number or anything that holds
        one.
    """
    if isinstance(value, np.ndarray | complex | np.complexfloating):
        found = holds_complex(value)
    elif isinstance(value, str | bytes):
        found = False
    else:
        try:
            found = holds_complex(np.asarray(value, dtype=object))
        except ValueError:
            return
    if found:
        raise TypeError(msg)
def refuse_text_beside_choice(
    value: object, name: str, options: tuple[str, ...]
) -> None:
    """Refuse a text that would reach the numbers of a choice beside numbers.

    A parameter that takes one of a few words or numbers reads a ``str`` as
    the choice and anything else as the numbers. A ``bytes`` or a
    ``bytearray`` (``b"rigid"``), or a text inside a sequence or an array
    (``["400"]``, ``np.array("400")``), is no ``str``, and so it reached the
    conversion of the numbers, which parses it (``np.asarray(["400"],
    dtype=complex)`` is ``400+0j``), reads a ``bytearray`` as the codes of
    its characters, or fails with an error that names no parameter. It is
    the wrong type whatever it reads as, so it is refused before the numbers
    are read; a ``str`` is the choice, and is checked as one by the caller.

    :param value: The caller's value, one that is not a ``str``.
    :param name: The parameter's name, for the message.
    :param options: The words the parameter offers.
    :raises TypeError: if *value* is a ``bytes`` or a ``bytearray``, or a
        sequence or an array that holds a text.
    """
    msg = f"'{name}' must be one of {options} as a str, or numbers, not text."
    if isinstance(value, bytearray):
        raise TypeError(msg)
    refuse_text(value, msg)


def require_real(value: object, msg: str) -> float:
    """*value* as a ``float``, or a refusal worded *msg* when it is not one number.

    The coercion a guard means when it hands a caller's value to
    :func:`float` and renames the failure: the rank is asked first, through
    :func:`is_scalar`, so that a one-element array is refused on every numpy
    rather than only on those where :func:`float` happens to refuse it.

    The refusal keeps the class the mistake has. An array, ``None``, a text
    (whether or not it reads as a number, see :func:`holds_text`), a complex
    number or any other object :func:`float` cannot take is the wrong type,
    and is refused with :class:`TypeError`; a number too large for a float
    is a value of the right type, and is refused with :class:`ValueError`.
    A complex value is refused whatever its kind: :func:`float` refuses a
    Python ``complex``, but takes the real part of a numpy one
    (``np.complex128``, ``np.complex64``, a zero-dimensional complex array)
    with no more than a ``ComplexWarning`` (:func:`holds_complex`), and the
    value passed as the number it is not.

    :param value: The caller's value, of any type.
    :param msg: The refusal, worded by the guard that owns the parameter.
    :return: ``float(value)``.
    :raises TypeError: with *msg*, for an array of any shape, a text, a
        complex value, or anything whose type :func:`float` refuses.
    :raises ValueError: with *msg*, for a number :func:`float` cannot hold.
    """
    if not is_scalar(value) or holds_text(value) or holds_complex(value):
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


#: Absolute zero, in degrees Celsius. The bound on a temperature that has to be
#: a temperature. It is not the same number as the ``-273`` that several ISO 3740
#: clauses print inside their own ``sqrt(273 + theta)``: those guards protect the
#: pole of the formula the clause states, which sits 0,15 degC higher, and they
#: stay where they are.
ABSOLUTE_ZERO_C = -273.15


def require_above_absolute_zero(value: float, name: str) -> float:
    """Require a finite temperature in degrees Celsius above absolute zero.

    The one bound a temperature always has. A model may state a narrower domain
    for itself, and that is a warning rather than a refusal, because a fit past
    its validated range is still arithmetic; a temperature at or below absolute
    zero is not a state at all, and the arithmetic below one is not wrong so much as
    meaningless. Left unguarded it does not raise, it returns: a sea-water sound
    speed comes back at -31 457 m/s, and an absorption at -300 degC comes back
    at a plausible-looking 0,495 dB/km.

    :param value: The temperature to validate, in degrees Celsius.
    :param name: Parameter name used in the error message.
    :return: The validated temperature as a ``float``.
    :raises TypeError: for a ``value`` that is an array, a text, or something
        else that is not a number.
    :raises ValueError: for a non-finite temperature, or one at or below
        -273,15 degC.
    """
    number = _one_number(value, name)
    if not math.isfinite(number) or number <= ABSOLUTE_ZERO_C:
        msg = f"'{name}' must be finite and above -273.15 degC."
        raise ValueError(msg)
    return number


def require_above_absolute_zero_array(x: ArrayLike, name: str) -> np.ndarray:
    """Require every temperature in ``x`` to be finite and above absolute zero.

    The array companion of :func:`require_above_absolute_zero`. A profile is
    where this bites hardest: one element at or below absolute zero among a
    hundred good ones still poisons the whole returned array, and the caller has no
    reason to look at any single element of it.

    :param x: Temperatures, in degrees Celsius.
    :param name: Parameter name used in the error message.
    :return: The temperatures as a ``float64`` array.
    :raises ValueError: if any element is non-finite or at or below
        -273,15 degC.
    """
    values = _as_float64(x, name)
    if not np.all(np.isfinite(values)) or np.any(values <= ABSOLUTE_ZERO_C):
        # Phrased so it reads for a single value and for a column alike: the
        # same helper serves 'temperature' and 'temperatures'.
        msg = f"'{name}' must be finite and above -273.15 degC."
        raise ValueError(msg)
    return values


def require_non_negative(value: float, name: str) -> float:
    """Require a non-negative finite number (rejects NaN and infinities).

    :param value: The value to validate.
    :param name: Parameter name used in the error message.
    :return: The validated value as a ``float``.
    :raises TypeError: for a ``value`` that is an array, a text, or something
        else that is not a number.
    :raises ValueError: for a non-finite or negative value.
    """
    number = _one_number(value, name)
    if not math.isfinite(number) or number < 0.0:
        msg = f"'{name}' must be non-negative."
        raise ValueError(msg)
    return number


def require_finite(value: float, name: str) -> float:
    """Require a finite number, of any sign (rejects NaN and infinities).

    The scalar sibling of :func:`require_finite_array`, for the levels a
    caller may pass one at a time: a level is a level whatever its sign, and
    an array of them is already refused when it is not finite, so a scalar
    that slips through as ``nan`` would be the one hole left.

    :param value: The value to validate.
    :param name: Parameter name used in the error message.
    :return: The validated value as a ``float``.
    :raises TypeError: for a ``value`` that is an array, a text, or something
        else that is not a number.
    :raises ValueError: for a non-finite value.
    """
    number = _one_number(value, name)
    if not math.isfinite(number):
        msg = f"'{name}' must be finite."
        raise ValueError(msg)
    return number


def require_fraction(value: float, name: str) -> float:
    """Require a finite fraction in ``[0, 1)``.

    :param value: The value to validate.
    :param name: Parameter name used in the error message.
    :return: The validated value as a ``float``.
    :raises TypeError: for a ``value`` that is an array, a text, or something
        else that is not a number.
    :raises ValueError: for a non-finite value, or one outside ``[0, 1)``.
    """
    number = _one_number(value, name)
    if not math.isfinite(number) or number < 0.0 or number >= 1.0:
        msg = f"'{name}' must be in the range [0, 1)."
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


def require_choice[T](value: object, name: str, options: tuple[T, ...]) -> T:
    """Require *value* to be one of *options*.

    Generic in the options, so a tuple typed with a ``Literal`` alias hands
    the checked value back as that alias: the caller narrows a ``str``
    without a ``cast`` of its own.

    A choice among names is a text: a value of another type (``period=5``,
    ``mode=None``) is the wrong type and is refused with :class:`TypeError`;
    a text that names none of the options is the right type with the wrong
    value, a :class:`ValueError`.

    :param value: The value to validate.
    :param name: Parameter name used in the error message.
    :param options: The accepted values.
    :return: The validated value.
    :raises TypeError: for a value that is not a text when every option is.
    :raises ValueError: for a value not in *options*.
    """
    if not isinstance(value, str) and all(
        isinstance(option, str) for option in options
    ):
        msg = f"'{name}' must be one of {options}, a text; got {value!r}."
        raise TypeError(msg)
    if value not in options:
        msg = f"'{name}' must be one of {options}; got {value!r}."
        raise ValueError(msg)
    return value


def require_aliased_choice(
    value: object, name: str, canonical: Iterable[str], aliases: Mapping[str, str]
) -> str:
    """Require *value* to name an option as written, and give its canonical
    spelling.

    *canonical* are the options a table prints and *aliases* the other
    spellings the ``Literal`` lists on purpose (``"docente"`` for
    ``"educational"``); the text is checked as the caller wrote it
    (:func:`require_choice`) and only then mapped, and an alias of an option
    the table does not hold is no option here.

    :param value: The value to validate.
    :param name: Parameter name used in the error message.
    :param canonical: The options the table prints.
    :param aliases: The listed spellings, each mapped to its option.
    :return: The canonical spelling of the option named.
    :raises TypeError: for a value that is not a text.
    :raises ValueError: for a text that names none of the options.
    """
    known = sorted(set(canonical))
    offered = (*known, *(alias for alias, to in aliases.items() if to in known))
    named = require_choice(value, name, offered)
    return aliases.get(named, named)


#: The two band sets a standard rates or tabulates: octaves and thirds.
_BAND_FRACTIONS = (1, 3)


def require_band_fraction(value: object, name: str) -> BandFraction:
    """Require *value* to name a band set: 1 (octave) or 3 (one-third octave).

    The integer is the denominator ``b`` of the IEC 61260-1 bandwidth
    designator ``1/b``, the ``fraction`` of
    :class:`~phonometry.filters.OctaveFilterBank`. ``True`` is refused
    although it compares equal to 1, and so is a float, so a band set is never
    read from a flag or a measured number.

    :param value: The value to validate.
    :param name: Parameter name used in the error message.
    :return: The validated band fraction.
    :raises TypeError: for a value that is not an integer: a word, a flag or
        a float.
    :raises ValueError: for an integer other than 1 and 3.
    """
    msg = f"'{name}' must be 1 (octave) or 3 (one-third octave); got {value!r}."
    if isinstance(value, bool) or not isinstance(value, int | np.integer):
        raise TypeError(msg)
    if int(value) not in _BAND_FRACTIONS:
        raise ValueError(msg)
    return cast("BandFraction", int(value))


def check_engine(engine: object) -> ReportEngine:
    """Require *engine* to name the one report engine there is.

    The counterpart of :func:`phonometry._i18n.check_language` for the
    ``engine`` parameter every ``report`` entry point takes. A single-choice
    check reads oddly until the choice is seen for what it is: ``"reportlab"``
    is the only engine today, and the parameter is the seam a second engine
    would arrive through. Gating it here keeps every entry point rejecting the
    same way, with one message to update when that day comes.

    :param engine: The requested report engine.
    :return: The engine, typed as the one choice there is.
    :raises TypeError: for a value that is not a text.
    :raises ValueError: for any text other than ``"reportlab"``.
    """
    if not isinstance(engine, str):
        msg = f"'engine' must be 'reportlab', a text; got {engine!r}."
        raise TypeError(msg)
    if engine == "reportlab":
        return "reportlab"
    msg = f"Unknown report engine {engine!r}; only 'reportlab' is supported."
    raise ValueError(msg)


#: The rank of a matrix of one row per position and one column per band.
_MATRIX_RANK = 2


def _as_float64(x: ArrayLike, name: str) -> np.ndarray:
    """Convert *x* to ``float64``, naming the parameter when numpy cannot.

    An unconvertible element would otherwise raise numpy's anonymous
    ``TypeError``, and a ragged list its anonymous ``ValueError``; both would
    escape the array guards below without saying which parameter refused.

    Two inputs numpy converts are refused rather than converted. A complex
    array: ``np.asarray(z, dtype=float64)`` drops the imaginary part with no
    more than a ``ComplexWarning``, so ``np.array([1 + 2j])`` would arrive at
    the guards below as ``[1.0]`` and pass every one of them, and an array
    of objects that holds a NumPy complex number would too
    (:func:`holds_complex`). And text:
    ``np.asarray(["94.0"], dtype=float64)`` parses it, so a column of readings
    left as text passed for numbers while one cell that reads as none raised
    a ``ValueError``; text is the wrong type where numbers belong whatever it
    reads as, refused here as :func:`require_real` refuses one text.

    :raises TypeError: for a complex array, text, or an element that is not a
        number.
    :raises ValueError: for a ragged nesting, to which numpy gives no shape.
    """
    try:
        array = np.asarray(x)
    except ValueError as exc:
        msg = f"'{name}' must be numeric."
        raise ValueError(msg) from exc
    if holds_complex(array):
        msg = f"'{name}' must be real, not complex."
        raise TypeError(msg)
    if holds_text(array):
        msg = f"'{name}' must be numbers, not text."
        raise TypeError(msg)
    try:
        return array.astype(np.float64, copy=False)
    except TypeError as exc:
        msg = f"'{name}' must be numeric."
        raise TypeError(msg) from exc
    except ValueError as exc:
        msg = f"'{name}' must be numeric."
        raise ValueError(msg) from exc


def require_positive_array(x: ArrayLike, name: str) -> np.ndarray:
    """Coerce *x* to a 1-D float64 array of strictly positive, finite values.

    :param x: The input (scalar or 1-D array-like).
    :param name: Parameter name used in the error message.
    :return: The validated ``float64`` array (at least 1-D).
    :raises ValueError: for a non-numeric, empty, multi-dimensional,
        non-finite or non-positive input.
    """
    arr = np.atleast_1d(_as_float64(x, name))
    if arr.ndim != 1 or arr.size == 0:
        msg = f"'{name}' must be a non-empty 1-D array."
        raise ValueError(msg)
    if not np.all(np.isfinite(arr)):
        msg = f"'{name}' must be finite."
        raise ValueError(msg)
    if np.any(arr <= 0.0):
        msg = f"'{name}' must be strictly positive."
        raise ValueError(msg)
    return arr


def require_finite_array(x: ArrayLike, name: str) -> np.ndarray:
    """Coerce *x* to a non-empty 1-D float64 array of finite values.

    The sign-agnostic sibling of :func:`require_positive_array`, for the
    level-like quantities (dB values, corrections) that may legitimately be
    negative but never NaN.

    :param x: The input (scalar or 1-D array-like).
    :param name: Parameter name used in the error message.
    :return: The validated ``float64`` array (at least 1-D).
    :raises ValueError: for a non-numeric, empty, multi-dimensional or
        non-finite input.
    """
    arr = np.atleast_1d(_as_float64(x, name))
    if arr.ndim != 1 or arr.size == 0:
        msg = f"'{name}' must be a non-empty 1-D array."
        raise ValueError(msg)
    if not np.all(np.isfinite(arr)):
        msg = f"'{name}' must contain only finite values."
        raise ValueError(msg)
    return arr


def require_finite_matrix(x: ArrayLike, name: str) -> np.ndarray:
    """Coerce *x* to a non-empty 2-D float64 array of finite values.

    The two-dimensional sibling of :func:`require_finite_array`, for the level
    matrices a standard writes as one row per measurement position and one
    column per band. A single row may be given one-dimensionally and arrives
    as a matrix of one row.

    :param x: The input (1-D or 2-D array-like).
    :param name: Parameter name used in the error message.
    :return: The validated ``float64`` array, always 2-D.
    :raises ValueError: for a non-numeric, empty, ragged, higher-dimensional
        or non-finite input.
    """
    arr = np.atleast_2d(_as_float64(x, name))
    if arr.ndim != _MATRIX_RANK or arr.size == 0:
        msg = f"'{name}' must be a non-empty 2-D array, one row per position."
        raise ValueError(msg)
    if not np.all(np.isfinite(arr)):
        msg = f"'{name}' must contain only finite values."
        raise ValueError(msg)
    return arr


def require_axis_count(
    value: object, owner: str, name: str, axis: str = "band", *, rank: int | None
) -> int:
    """The number of entries along the first axis of *value*.

    ``len()``, not ``np.shape()``: the first axis of a tuple of per-band
    arrays is its length whatever the arrays hold, while ``np.shape`` would
    try to stack them and raise about an inhomogeneous shape for a bank whose
    bands carry filters of different orders.

    *rank* has no default and must be stated, because a count on its own says
    nothing about how many axes there are: an array of shape ``(bands, 2)``
    counts the right number of bands on its first axis and carries the second
    one onward untouched. Pass ``None`` only where the rank is pinned
    elsewhere, as :func:`require_ranks` does for a whole result at once.

    :param value: The field whose entries are counted.
    :param owner: Name of the type being checked, used in the error message.
    :param name: Field name used in the error message.
    :param axis: What the entries measure, singular, for the error message.
    :param rank: The number of axes the field must have, or ``None`` when that
        is checked elsewhere.
    :return: The number of entries.
    :raises TypeError: if *value* is a single number.
    :raises ValueError: if *value* has another rank.
    """
    if rank is not None:
        require_axis_rank(value, owner, name, rank)
    try:
        return len(value)  # type: ignore[arg-type]
    except TypeError:
        msg = f"{owner}: '{name}' must carry one value per {axis}, not a single number."
        raise TypeError(msg) from None


def _rank(value: object) -> int:
    """The number of axes a field carries, as the guards count them.

    One place, because three callers ask the same question and numpy answers
    it badly for two kinds of field the library really holds.

    A sequence whose entries are arrays is one axis of entries, whatever each
    entry holds. A filter bank keeps one set of second-order sections per band
    and the sets need not be the same length; stacking them either raises
    about an inhomogeneous shape or, when the orders happen to agree, invents
    an axis nobody meant. Both cases have to answer the same, or a bank would
    be accepted or refused according to a coincidence between its bands.

    Everything else is measured. A nested list is as two-dimensional as the
    array it would become, and calling it one axis would refuse a correctly
    shaped grid handed in as lists while letting a list with an extra axis
    walk past the pin that exists to stop one.
    """
    if isinstance(value, (tuple, list)) and any(
        isinstance(entry, np.ndarray) for entry in value
    ):
        return 1
    try:
        return int(np.ndim(cast("ArrayLike", value)))
    except ValueError:
        # Ragged in some other shape: numpy has no rank to give, and the
        # sequence is still one axis of whatever it holds.
        return 1


def require_axis_rank(value: object, owner: str, name: str, rank: int) -> None:
    """Require *value* to have exactly *rank* axes.

    Counting an axis is not enough on its own: an array of shape
    ``(paths, bands, 2)`` has the right number of paths on its first axis and
    the right number of bands on its second, so every count agrees and the
    extra axis travels on into whatever indexes the field next.

    The rank is measured, not assumed from the type. A nested list is as
    two-dimensional as the array it would become, and taking it for a single
    axis would be wrong twice over: it would refuse a correctly shaped grid
    handed in as lists, and it would let a list carrying an extra axis walk
    past the very pin that exists to stop one.

    A sequence of arrays escapes measurement, ragged or not: see :func:`_rank`,
    which is where all three callers ask this question so that they cannot
    drift apart.

    :param value: The field whose axes are counted.
    :param owner: Name of the type being checked, used in the error message.
    :param name: Field name used in the error message.
    :param rank: The number of axes the field must have.
    :raises ValueError: if *value* has a different number of axes.
    :raises TypeError: if ``rank`` is not a single number.
    """
    require_scalar(rank, "rank")
    actual = _rank(value)
    if actual != rank:
        axes = "one axis" if rank == 1 else f"{rank} axes"
        why = (
            "An extra axis passes every count and reaches the reader intact."
            if actual > rank
            else "A value short of an axis is spread over the ones it was "
            "never measured on."
        )
        msg = f"{owner}: '{name}' must have {axes}; got {actual}. {why}"
        raise ValueError(msg)


def require_present(owner: object, *fields: str) -> None:
    """Require each named field of *owner* to hold a value, not ``None``.

    A required field cannot be left out of the call, but ``None`` can still
    be passed for it, or put there with :func:`dataclasses.replace`. The
    shape and value guards skip ``None`` on purpose, since an optional
    quantity may be absent, so without this the record would build and
    fail later, in a report or a plot, with an error that names neither the
    field nor the record.

    :param owner: The instance whose fields are read.
    :param fields: Names of the fields that must not be ``None``.
    :raises TypeError: naming the record and the first field that holds
        ``None``.
    """
    for name in fields:
        if getattr(owner, name) is None:
            msg = f"{type(owner).__name__}: '{name}' is required and cannot be None."
            raise TypeError(msg)


def require_ranks(owner: object, **ranks: int) -> None:
    """Require each named field of *owner* to have the given number of axes.

    The companion of :func:`require_same_length`, which pins how long an axis
    is but not how many there are. ``None`` fields are skipped.

    A result whose every pinned field is a bare number is passed over whole.
    Several entry points take a single frequency and hand back nought-
    dimensional arrays throughout; that is not an extra axis, it is no axis.
    The exemption is all or nothing on purpose. Waiving it field by field
    would leave a lone scalar sitting beside real spectra wherever no length
    check happens to cover that field, and about ten fields here are pinned
    against an extra axis without being pinned against a missing one.

    :param owner: The instance whose fields are measured.
    :param ranks: Field name to the number of axes it must have.
    :raises ValueError: if a field has a different number of axes.
    """
    present = [
        (name, rank, value)
        for name, rank in ranks.items()
        if (value := getattr(owner, name)) is not None
    ]
    if all(_rank(value) == 0 for _, _, value in present):
        return
    for name, rank, value in present:
        require_axis_rank(value, type(owner).__name__, name, rank)


def require_equal_counts(
    owner: str, counts: Mapping[str, int], axis: str = "band"
) -> None:
    """Require every measured count to agree, naming each one that does not.

    The sibling of :func:`require_same_length` for the counts a caller has
    already measured: entries of a nested sequence, an axis picked out of a
    two-dimensional field, anything whose label is not a plain attribute name.

    The message lists every count it was given rather than picking out an odd
    one, because among peers no count is authoritative and a majority winner
    would be a guess. Where one quantity *is* authoritative, pass it and the
    single suspect: two entries make the shortest true message there is.

    :param owner: Name of the type being checked, used in the error message.
    :param counts: Label to count, in the order they should be reported.
    :param axis: What the counts measure, singular, for the error message.
    :raises ValueError: if two of the counts disagree.
    """
    if len(set(counts.values())) <= 1:
        return
    listed = ", ".join(f"'{label}' ({n})" for label, n in counts.items())
    msg = f"{owner}: {listed} must each carry one value per {axis}."
    raise ValueError(msg)


def require_same_length(
    owner: object, *fields: str | tuple[str, int], axis: str = "band"
) -> None:
    """Require the named fields of *owner* to share one length.

    Written for the ``__post_init__`` of a result dataclass, so that a result
    whose per-band arrays disagree cannot be built at all. Validating here
    rather than where the values are read covers the readers that do not
    exist yet, and both directions of the mistake: an array one short raises
    somewhere downstream, but an array one long is silently truncated by the
    table that prints it, under a total that summed the whole of it.

    A field may be given as ``"name"`` for a length along the first axis, or
    as ``("name", i)`` when the axis in question is not the first one, as it
    is not for a per-path-per-band array whose bands run along axis 1.

    ``None`` fields are skipped: an absent optional quantity is not a
    disagreement.

    A result whose every field is a bare number is left alone. Several entry
    points take a single frequency and hand back a result of nought-dimensional
    arrays, and there is no axis there to disagree about; only a mixture of
    scalars and arrays is a mistake, and that is what the count below reports.

    :param owner: The instance whose fields are compared.
    :param fields: Field names, or ``(name, axis_index)`` pairs.
    :param axis: What the lengths measure, singular, for the error message.
    :raises ValueError: if two of the fields disagree, or one is a scalar.
    """
    named = [(field if isinstance(field, tuple) else (field, 0)) for field in fields]
    present = [
        (name, index, value)
        for name, index in named
        if (value := getattr(owner, name)) is not None
    ]
    if all(_rank(value) == 0 for _, _, value in present):
        return
    counts: dict[str, int] = {}
    for name, index, value in present:
        if index == 0:
            counts[name] = require_axis_count(
                value, type(owner).__name__, name, axis, rank=None
            )
            continue
        shape = np.shape(value)
        if len(shape) <= index:
            msg = (
                f"{type(owner).__name__}: '{name}' must have an axis {index} "
                f"to carry one value per {axis}; got shape {shape}."
            )
            raise ValueError(msg)
        counts[f"{name} (axis {index})"] = shape[index]
    require_equal_counts(type(owner).__name__, counts, axis)


def require_equal_shapes(
    owner: str, shapes: Mapping[str, tuple[int, ...]], quantity: str = "point"
) -> None:
    """Require every shape to agree, naming each one that does not.

    What :func:`require_equal_counts` is to :func:`require_same_length`, this
    is to :func:`require_same_shape`: the form for values a caller is holding
    loose, where there is no instance to read the fields off. An entry point
    validating two of its own arguments is the usual case.

    Shape rather than length, because two grids of the same height agree on
    every count and can still disagree about every value in them.

    :param owner: Name of the entry point, used in the error message. The one
        the caller typed, not the private validator it reached.
    :param shapes: Label to shape, in the order they should be reported.
    :param quantity: What one element is, singular, for the error message.
    :raises ValueError: if two of the shapes disagree.
    """
    if len(set(shapes.values())) <= 1:
        return
    listed = ", ".join(f"'{label}' {shape}" for label, shape in shapes.items())
    msg = f"{owner}: {listed} must all have the same shape, one value per {quantity}."
    raise ValueError(msg)


def require_same_shape(owner: object, *fields: str, quantity: str = "point") -> None:
    """Require the named fields of *owner* to have exactly the same shape.

    The stricter sibling of :func:`require_same_length`, for fields derived
    from one another elementwise rather than laid side by side along one axis.
    A propagation loss and the signal excess computed from it agree point for
    point, and the solver that produced them may well have returned a grid
    over depth and range, so pinning a single axis would be both too weak,
    two grids of the same height can disagree everywhere else, and too strong,
    since it would refuse the grid the library itself hands back.

    ``None`` fields are skipped, and so is a set of fields that are all bare
    numbers.

    :param owner: The instance whose fields are measured.
    :param fields: Field names that must share one shape.
    :param quantity: What one element is, used in the error message.
    :raises ValueError: if two present fields have different shapes.
    """
    present = [(name, getattr(owner, name)) for name in fields]
    present = [(name, value) for name, value in present if value is not None]
    if all(np.ndim(value) == 0 for _, value in present):
        return
    shapes = {name: np.shape(value) for name, value in present}
    require_equal_shapes(type(owner).__name__, shapes, quantity)


def _as_numeric_field(owner: object, name: str, value: object) -> np.ndarray:
    """A field of *owner* as an array, ``float64`` unless it is complex.

    An array of objects that holds a complex number is read as complex, so
    both axes are checked: read as ``float64``, NumPy would keep the real
    part of a NumPy complex number with no more than a ``ComplexWarning``.

    :raises TypeError: if the field is text or holds an element that is not a
        number.
    :raises ValueError: if the field is a ragged nesting.
    """
    try:
        array = np.asarray(value)
    except ValueError as exc:
        msg = f"{type(owner).__name__}: '{name}' must be numeric."
        raise ValueError(msg) from exc
    if holds_text(array):
        msg = f"{type(owner).__name__}: '{name}' must be numeric, not text."
        raise TypeError(msg)
    if array.dtype.kind == "c":
        return array
    try:
        return array.astype(np.complex128 if holds_complex(array) else np.float64)
    except TypeError as exc:
        msg = f"{type(owner).__name__}: '{name}' must be numeric."
        raise TypeError(msg) from exc
    except ValueError as exc:
        msg = f"{type(owner).__name__}: '{name}' must be numeric."
        raise ValueError(msg) from exc


def require_finite_fields(owner: object, *fields: str) -> None:
    """Require each named field of *owner* to carry only finite values.

    The value guard beside the shape guards of a result's ``__post_init__``,
    for the fields no producer can legitimately leave undetermined: a
    measurement surface area, a room volume, a single-number index. Where a
    quantity *is* legitimately undeterminable band by band, an ISO 9614 band
    of negative net power or an A-weighted total over no bands, it is marked
    as such by a flag and rendered as an em dash, and it must not be listed
    here.

    Shape guards alone do not cover this: a ``NaN`` has whatever shape it was
    stored in, so it passes every count and every rank, and reaches the fiche
    as the literal ``nan`` printed in an accredited table, or as a conversion
    error raised from inside a display rounder that names neither the field
    nor the result it belongs to.

    ``None`` fields are skipped: an absent optional quantity is not a
    non-finite one.

    A complex field is measured on both of its axes. Casting one to
    ``float64`` to run the check would drop the imaginary part on the way in,
    so a transfer stiffness whose damping term came back ``NaN`` beside an
    intact real part passed the guard untouched, and the phase quantities
    computed from it -- a magnitude, a loss factor -- carried the ``NaN``
    onward as though it had been measured. ``np.isfinite`` already reads a
    complex number as finite only when both components are, so the cast is
    made only for the fields that are not complex to begin with.

    That cast is also what refuses a field that is not numeric at all, and it
    is kept for the sake of it: an object array reaches ``np.isfinite`` as an
    anonymous ``TypeError`` raised from inside numpy, which names neither the
    field nor the result. Text is refused before it, whatever it reads as,
    since the cast would parse ``"94.0"`` into a number (:func:`holds_text`).

    :param owner: The instance whose fields are measured.
    :param fields: Field names that must be finite throughout.
    :raises TypeError: if a field is text or holds an element that is not a
        number.
    :raises ValueError: if a field carries a ``NaN`` or an infinity, or is a
        ragged nesting.
    """
    for name in fields:
        value = getattr(owner, name)
        if value is None:
            continue
        array = _as_numeric_field(owner, name, value)
        if np.all(np.isfinite(array)):
            continue
        what = "be finite" if array.ndim == 0 else "contain only finite values"
        msg = f"{type(owner).__name__}: '{name}' must {what}."
        raise ValueError(msg)


def is_class_designation(value: object, expected: Sequence[int]) -> bool:
    """Whether *value* is one of *expected* as a designation, not merely equal.

    A compliance class is a label rather than a measurement: a fiche prints it
    verbatim into ``Class 1`` and readers splice it into the
    ``margin_class1_db`` key they take the binding margin from. Equality with
    a class is therefore too weak a test. ``1.0`` labels a band ``Class 1.0``
    and builds ``margin_class1.0_db``, a key no band carries, and ``True`` is
    an ``int`` in Python and would label one ``Class True``. NumPy integers
    are admitted: they are the same designation and print as it.

    :param value: The candidate designation.
    :param expected: The classes the edition or standard defines.
    :return: ``True`` when *value* designates one of *expected*.
    """
    return is_integer(value) and int(value) in expected


def is_integer(value: object) -> TypeGuard[int | np.integer[Any]]:
    """Whether *value* is an integer by its type: an ``int`` or a NumPy
    integer, never a bool.

    ``int()`` is not this test: it takes ``1.5`` as 1, ``True`` as 1 and
    ``"1"`` as 1, so a value that reads an index, a designation or a count
    through it takes each of them as the integer it was never given.

    :param value: The value to test, of any type.
    :return: Whether *value* is a Python or NumPy integer and not a bool.
    """
    return isinstance(value, int | np.integer) and not isinstance(value, bool)


def indices_of(value: object, name: str) -> tuple[int, ...]:
    """The indices a sequence of integers, or an integer array of one
    dimension, holds, in their order.

    An index picks an item by its place, so each is an integer by its type
    (:func:`is_integer`); a fraction, a whole float, a flag or a text that
    spells one is refused rather than read through ``int()``, and a text is
    never read as a sequence of its letters.

    :param value: A sequence (a list, a tuple, a range) or any other
        iterable of Python or NumPy integers, or a one-dimensional array of
        an integer dtype.
    :param name: Parameter name used in the error message.
    :return: The indices, as Python integers.
    :raises TypeError: for a text, bytes, an array that has other than one
        dimension or is not of an integer dtype, a value that holds no
        items, or an item that is not an integer.
    """
    if isinstance(value, np.ndarray):
        if value.ndim != 1 or not np.issubdtype(value.dtype, np.integer):
            msg = (
                f"'{name}' must be integer indices; an array of them is one-"
                f"dimensional and of an integer dtype, got {value.ndim} "
                f"dimensions of {value.dtype}."
            )
            raise TypeError(msg)
        return tuple(int(item) for item in value)
    if isinstance(value, str | bytes) or not isinstance(value, Iterable):
        msg = f"'{name}' must be a sequence of integer indices, got {value!r}."
        raise TypeError(msg)
    items = tuple(value)
    for item in items:
        if not is_integer(item):
            msg = f"'{name}' must hold integer indices, got {item!r}."
            raise TypeError(msg)
    return tuple(int(item) for item in items)


def require_per_band(
    x: ArrayLike, name: str, bands: np.ndarray, bands_name: str
) -> np.ndarray:
    """Broadcast *x* over the band axis, saying whose length disagrees.

    A scalar applies to every band and an array of the band count is taken
    band by band. Nothing else is: broadcasting alone would also stretch a
    one-element array across every band, which is the shape a caller lands on
    by computing one value where the bands needed several, and the answer that
    comes back from repeating it looks perfectly ordinary.

    ``np.broadcast_to`` is left to do the stretching once the shape is known
    to be one of the two, because what it cannot do is name the culprit: it
    reports the two shapes it failed to reconcile, from inside its own C code,
    without saying which argument carried which.

    :param x: The per-band input (a scalar applies to every band).
    :param name: Parameter name used in the error message.
    :param bands: The band axis to match, already coerced and 1-D.
    :param bands_name: The caller's name for the band axis, quoted in the
        message. It has no default, so a message never names an axis the
        caller does not take (``frequency`` beside a ``frequencies``).
    :return: The broadcast ``float64`` array, of ``bands.shape``.
    :raises ValueError: if *x* is neither a scalar nor of ``bands``' length.
    """
    arr = _as_float64(x, name)
    if arr.ndim != 0 and arr.shape != bands.shape:
        msg = (
            f"'{name}' must be a scalar or carry one value per band "
            f"({bands.size} in '{bands_name}'); got shape {arr.shape}."
        )
        raise ValueError(msg)
    return np.broadcast_to(arr, bands.shape).astype(np.float64)


def require_1d_signal(x: ArrayLike, name: str) -> np.ndarray:
    """Coerce *x* to a float64 array and require a 1-D time series.

    Multichannel input is rejected rather than silently flattened (a raveled
    2-D signal concatenates the channels into one wrong series).

    :param x: The input signal.
    :param name: The caller's name for the parameter, quoted in the error
        message. It has no default, so a message never names a parameter the
        caller does not have.
    :return: The validated ``float64`` array.
    :raises ValueError: for a non-1-D input.
    """
    arr = _as_float64(x, name)
    if arr.ndim != 1:
        msg = (
            f"'{name}' must be a 1-D time series; got shape {arr.shape}. "
            "Process multichannel signals one channel at a time."
        )
        raise ValueError(msg)
    return arr


def _members_of(
    value: object, msg: str, *, owned: bool = False
) -> Sequence[object]:
    """The members of a sequence a record takes as one field, refused whole when it is none.

    Iterating gives something of many objects that are no sequence of
    members: a ``bytearray`` gives the codes of its characters, as a
    ``bytes`` does, a mapping gives its keys and a set its members in no
    order. Each is refused whole, as a text is (see :func:`holds_text`),
    rather than read as the members it gives.

    :param value: The caller's value, of any type.
    :param msg: The start of the refusal, worded by the caller.
    :param owned: Read the members through
        :func:`~phonometry._internal.frozen.owned_members`, for a record that
        seals the arrays it holds: an array a deque or a generator holds is
        copied, so the record never seals one of the caller's.
    :return: The members, in order.
    :raises TypeError: for a text in any form, a mapping, a set, or a value
        that is not a sequence at all.
    """
    refusal = f"{msg}, not {type(value).__name__}."
    if holds_text(value) or isinstance(value, bytearray | Mapping | Set):
        raise TypeError(refusal)
    try:
        if owned:
            return owned_members(cast("Iterable[object]", value))
        return list(cast("Iterable[object]", value))
    except TypeError:
        raise TypeError(refusal) from None


def arrays_of(
    value: object, name: str, members: str, n_members: int
) -> tuple[NDArray[np.float64], ...]:
    """The members of a sequence of a fixed count of arrays, each as ``float64``.

    A record that takes a curve as a pair (``(angles_deg, relative_db)``) or
    a grid as its axes (``(x, y, z)``) takes it as any sequence of them (a
    tuple, a list, an array of rows or of objects, a deque) and holds it as
    that many arrays, so it is unpacked here, once, when the record is
    built. The caller is a record that inherits ``OwnsArrays`` and seals
    each member with ``read_only``, so each has to be the record's own, and
    the members are read through
    :func:`~phonometry._internal.frozen.owned_members`: an array the record
    copied (in a tuple, a list or an array, an array of objects member by
    member), or read out of any other object numpy reads as an array (a
    column of a data frame, a ``memoryview``), comes back as itself when it
    is ``float64`` already, and one a
    deque or a generator holds is copied. A member that is no array, a list
    of numbers, is converted into a new one. A member is converted as
    :func:`_as_float64` converts, so a text among its numbers is refused,
    whatever it reads as, and not parsed into one.

    :param value: The sequence.
    :param name: The field's name, for the message.
    :param members: What the field holds, as the message spells it (``"a
        pair (angles_deg, relative_db) of two arrays"``).
    :param n_members: How many arrays it holds.
    :return: The members, each a ``float64`` array.
    :raises TypeError: if *value* is a text in any form (a ``bytearray``
        included), a mapping, a set or not a sequence at all, a member holds
        a complex number, a text or anything that is not a number, or
        *n_members* is not a number.
    :raises ValueError: if it holds other than *n_members* members, a member
        is a ragged nesting, or *n_members* is not a whole number of at least
        one.
    """
    expected = require_count(n_members, "n_members")
    msg = f"'{name}' must be {members}"
    items = _members_of(value, msg, owned=True)
    if len(items) != expected:
        msg += f", not {len(items)} of them."
        raise ValueError(msg)
    for item in items:
        refuse_complex(item, f"{msg} of real numbers, not complex ones.")
        refuse_text(item, f"{msg} of numbers, not text.")
    return tuple(_as_float64(cast("ArrayLike", item), name) for item in items)


def pair_of_arrays(
    value: object, name: str, members: str
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The two members of a pair, each as a ``float64`` array.

    :func:`arrays_of` with a count of two, typed as the pair it returns.

    :param value: The pair.
    :param name: The field's name, for the message.
    :param members: What the two members are, as the message spells them
        (``"(angles_deg, relative_db)"``).
    :return: The two members, each a ``float64`` array.
    :raises TypeError: if *value* is a text in any form, a mapping, a set or
        not a sequence at all, or a member holds a text, a complex value or
        anything that is not a number.
    :raises ValueError: if it holds other than two members, or a member is
        a ragged nesting.
    """
    first, second = arrays_of(value, name, f"a pair {members} of two arrays", 2)
    return first, second


def floats_of(
    value: object, name: str, members: str, n_members: int | None = None
) -> tuple[float, ...]:
    """The members of a sequence of numbers, each as a ``float``.

    A record that holds a few numbers as one field (a ``(low, high)`` range,
    the three risk thresholds of a sex, a set of observations) takes them as
    a tuple, a list or an array, and holds them as a tuple of floats, so they
    are unpacked here, once, when the record is built, and each refusal
    names the field. A text is refused whatever it reads as, as
    :func:`holds_text` has it, and so is a member that is not one number.
    A ``bytearray``, a mapping and a set are refused whole: iterating them
    gives the codes of the characters, the keys, and the members in no
    order, none of them the numbers a caller meant.

    :param value: The sequence.
    :param name: The field's name, for the message.
    :param members: What the field holds, as the message spells it (``"a
        (low, high) pair of two numbers"``).
    :param n_members: How many numbers it holds, or ``None`` for any count.
    :return: The numbers, each a ``float``.
    :raises TypeError: if *value* is a text in any form (a ``bytearray``
        included), a mapping, a set or not a sequence at all, a member is not
        one number (a text or a complex value included), or *n_members* is
        not a number.
    :raises ValueError: if it holds other than *n_members* members, a
        member is a number too large for a float, or *n_members* is not a
        whole number of at least one.
    """
    expected = None if n_members is None else require_count(n_members, "n_members")
    msg = f"'{name}' must be {members}"
    items = _members_of(value, msg)
    if expected is not None and len(items) != expected:
        msg += f", not {len(items)} of them."
        raise ValueError(msg)
    return tuple(
        require_real(item, f"{msg}; one member is {type(item).__name__}.")
        for item in items
    )


def pair_of_floats(value: object, name: str, members: str) -> tuple[float, float]:
    """The two members of a pair of numbers, each as a ``float``.

    :func:`floats_of` with a count of two, typed as the pair it returns.

    :param value: The pair.
    :param name: The field's name, for the message.
    :param members: What the two members are, as the message spells them
        (``"(low, high)"``).
    :return: The two numbers.
    :raises TypeError: if *value* is a text in any form, a mapping, a set or
        not a sequence at all, or a member is not one number.
    :raises ValueError: if it holds other than two members.
    """
    first, second = floats_of(value, name, f"a pair {members} of two numbers", 2)
    return first, second
