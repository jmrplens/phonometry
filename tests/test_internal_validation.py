#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the shared construction guards (``phonometry._internal.validation``).

Every result type in the library reaches these three helpers, so their coverage
used to be entirely indirect: a change of semantics here could leave a hundred
classes quietly wrong and the suite green. What is pinned below is the part
that is easy to get wrong and impossible to see from a call site, above all the
two kinds of field numpy answers badly for.

A **grid handed in as nested lists** is as two-dimensional as the array it would
become. Taking it for one axis refuses a correct grid and, worse, lets a list
carrying an extra axis walk past the very pin that exists to stop one.

A **sequence whose entries are arrays** is one axis of entries, whatever each
entry holds. A filter bank keeps one set of second-order sections per band and
the sets need not be the same length; asking numpy to stack them either raises
about an inhomogeneous shape or, when the orders happen to agree, invents an
axis nobody meant. Both have to answer the same, or a bank would be accepted or
refused according to a coincidence between its bands.
"""

from __future__ import annotations

import math
import warnings
from collections import deque
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

from phonometry._internal.validation import (
    arrays_of,
    check_engine,
    complex_array,
    floats_of,
    holds_text,
    indices_of,
    is_integer,
    pair_of_arrays,
    real_array,
    refuse_text,
    refuse_text_beside_choice,
    require_1d_signal,
    require_above_absolute_zero,
    require_above_absolute_zero_array,
    require_count,
    require_equal_shapes,
    require_finite,
    require_finite_array,
    require_finite_fields,
    require_fraction,
    require_non_negative,
    require_per_band,
    require_positive,
    require_positive_array,
    require_ranks,
    require_real,
    require_same_length,
    require_same_shape,
    require_scalar,
)


@dataclass(frozen=True)
class _Result:
    """A stand-in for the result types, so the helpers are tested directly."""

    first: object = None
    second: object = None
    third: object = None


#: A filter bank whose bands carry filters of different orders: the ragged case
#: numpy cannot stack at all.
_RAGGED_BANK = (np.zeros((2, 6)), np.zeros((3, 6)))

#: The same bank where the orders happen to agree. Numpy *can* stack this one,
#: into a (2, 2, 6) array, which is the coincidence the guards must ignore.
_UNIFORM_BANK = (np.zeros((2, 6)), np.zeros((2, 6)))


@pytest.mark.parametrize(
    ("label", "bank"), [("ragged", _RAGGED_BANK), ("uniform", _UNIFORM_BANK)]
)
def test_a_bank_of_per_band_filters_is_one_axis_of_entries(
    label: str, bank: tuple[np.ndarray, ...]
) -> None:
    """Both banks are one axis of two entries, and neither reaches numpy raw.

    The uniform bank is the trap: stacking it succeeds and reports three axes,
    so a bank would be refused or accepted according to whether its bands
    happened to carry filters of the same order.
    """
    result = _Result(first=np.zeros(2), second=bank)
    require_ranks(result, second=1)
    require_same_length(result, "first", "second", axis="band")


def test_a_bank_is_measured_the_same_whichever_field_comes_first() -> None:
    """Argument order decides nothing.

    The scalar shortcut reads the fields in the order given, so a ragged entry
    listed first used to reach ``np.ndim`` before anything had established that
    it could not be stacked, and numpy answered about an inhomogeneous shape in
    its own words, naming neither the field nor the result.
    """
    result = _Result(first=np.zeros(2), second=_RAGGED_BANK)
    require_same_length(result, "first", "second", axis="band")
    require_same_length(result, "second", "first", axis="band")


def test_a_grid_of_nested_lists_carries_the_axes_it_looks_like() -> None:
    """Nested lists are measured, not taken for a single axis."""
    grid = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    require_ranks(_Result(first=grid), first=2)


def test_a_nested_list_cannot_smuggle_an_extra_axis_past_a_one_axis_pin() -> None:
    """The hole the rank pin exists to close, in the form that used to slip.

    A ``(bands, 2)`` list satisfies every count on its first axis, so only the
    rank sees it.
    """
    result = _Result(first=[[60.0, 1.0], [61.0, 1.0]])
    with pytest.raises(ValueError, match="'first' must have one axis; got 2"):
        require_ranks(result, first=1)


def test_a_missing_axis_is_refused_and_not_described_as_an_extra_one() -> None:
    """A bare number where an axis was asked for is the opposite failure.

    It is refused too, and the message has to say which way round it went: a
    value short of an axis is spread over bands it was never measured on, and
    telling the reader an extra axis reached the reader would send them looking
    for the wrong bug.
    """
    result = _Result(first=np.float64(80.0), second=np.zeros(3))
    with pytest.raises(ValueError, match="'first' must have one axis; got 0") as caught:
        require_ranks(result, first=1, second=1)
    assert "never measured on" in str(caught.value)


def test_a_result_of_bare_numbers_is_passed_over_whole() -> None:
    """Several entry points take one frequency and answer in bare numbers.

    That is not an extra axis, it is no axis. The exemption is all or nothing:
    the test below pins the other half.
    """
    result = _Result(first=np.float64(1.0), second=np.float64(2.0))
    require_ranks(result, first=1, second=1)
    require_same_length(result, "first", "second")


def test_a_lone_number_beside_a_spectrum_is_still_refused() -> None:
    """The boundary of the exemption, and the reason it is all or nothing.

    Waiving the rank field by field would leave a scalar sitting beside real
    spectra wherever no length check happens to cover that field, and several
    fields in the library are pinned against an extra axis without being pinned
    against a missing one.
    """
    result = _Result(first=np.float64(1.0), second=np.zeros(4))
    with pytest.raises(ValueError, match="'first' must have one axis; got 0"):
        require_ranks(result, first=1, second=1)


def test_none_is_an_absent_quantity_rather_than_a_disagreement() -> None:
    result = _Result(first=np.zeros(3), second=None)
    require_ranks(result, first=1, second=1)
    require_same_length(result, "first", "second")
    require_same_shape(result, "first", "second")


def test_same_shape_refuses_two_grids_that_agree_on_one_axis_only() -> None:
    """What a length check cannot see.

    Two grids of equal height agree on the only axis a count reads and disagree
    about every value in them.
    """
    result = _Result(first=np.zeros((3, 2)), second=np.zeros((3, 4)))
    require_same_length(result, "first", "second")
    with pytest.raises(ValueError, match="'second'.* must all have the same shape"):
        require_same_shape(result, "first", "second", quantity="cell")


def test_same_shape_accepts_the_grid_the_library_produces() -> None:
    """A quantity derived elementwise keeps the shape it was derived from."""
    grid = np.zeros((3, 2))
    require_same_shape(_Result(first=grid, second=grid.copy()), "first", "second")


def test_an_axis_other_than_the_first_is_counted_where_it_lives() -> None:
    """``(name, i)`` reads axis ``i``, which is how a grid pins both of its."""
    result = _Result(first=np.zeros(2), second=np.zeros(5), third=np.zeros((2, 5)))
    require_same_length(result, "first", ("third", 0), axis="grid row")
    require_same_length(result, "second", ("third", 1), axis="grid column")


def test_an_axis_that_does_not_exist_is_named_rather_than_indexed() -> None:
    result = _Result(first=np.zeros(2), third=np.zeros(2))
    with pytest.raises(ValueError, match="'third' must have an axis 1"):
        require_same_length(result, "first", ("third", 1), axis="grid column")


def test_the_message_names_the_result_the_fields_and_the_counts() -> None:
    """What the readers could not say, and the whole point of checking here.

    Matplotlib reports two shapes, a table loop reports an index and a size,
    and neither names the field or the type it came from.
    """
    result = _Result(first=np.zeros(16), second=np.zeros(17))
    with pytest.raises(ValueError, match=r"'first' \(16\)") as caught:
        require_same_length(result, "first", "second", axis="band")
    message = str(caught.value)
    assert "_Result" in message
    assert "'first' (16)" in message
    assert "'second' (17)" in message
    assert "one value per band" in message


def test_equal_shapes_names_the_entry_point_and_every_shape() -> None:
    """The loose-arguments form, for a function validating what it was passed.

    There is no instance to read fields off, so the caller states the label and
    the shape. The owner is the name the caller typed, not the private
    validator it happened to reach.
    """
    with pytest.raises(
        ValueError, match="'y'.* must all have the same shape"
    ) as caught:
        require_equal_shapes("coherence", {"x": (3, 2), "y": (3, 4)}, "sample")
    message = str(caught.value)
    assert "coherence:" in message
    assert "'x' (3, 2)" in message
    assert "one value per sample" in message


def test_equal_shapes_is_quiet_when_they_agree() -> None:
    require_equal_shapes("coherence", {"x": (3, 2), "y": (3, 2)}, "sample")


def test_equal_shapes_sees_what_a_count_cannot() -> None:
    """Two grids of the same height agree on every count a length check reads."""
    require_equal_shapes("f", {"a": (3,), "b": (3,)})
    with pytest.raises(ValueError, match="'b'.* must all have the same shape"):
        require_equal_shapes("f", {"a": (3, 2), "b": (3, 4)})


def test_the_one_engine_there_is_passes_in_silence() -> None:
    check_engine("reportlab")


def test_an_unknown_engine_is_refused_by_name() -> None:
    """The single-choice gate every ``report`` entry point shares.

    ``"reportlab"`` is the only engine today; the parameter is the seam a
    second one would arrive through, and this one message is what every entry
    point rejects with until then.
    """
    with pytest.raises(ValueError, match="Unknown report engine 'weasyprint'"):
        check_engine("weasyprint")


@pytest.mark.parametrize(
    ("validator", "args"),
    [
        (require_positive_array, ()),
        (require_finite_array, ()),
        (require_per_band, (np.array([100.0, 200.0]), "frequencies")),
        (require_1d_signal, ()),
    ],
)
def test_garbage_input_is_refused_naming_the_parameter(
    validator: Callable[..., object], args: tuple[object, ...]
) -> None:
    """Every coercing validator names the parameter numpy could not convert.

    A tuple of strings used to escape as numpy's own "could not convert
    string to float" and an object as a bare TypeError, neither saying which
    parameter refused; the shared conversion now answers for all four
    validators in one voice.
    """
    # A text, an object and a mapping are all the wrong type: a guard is not
    # a parser, so a text is refused whatever it reads as.
    for garbage, words in (
        (("bad",), "numbers, not text"),
        (("1.0",), "numbers, not text"),
        (object(), "numeric"),
        ({"a": 1}, "numeric"),
    ):
        with pytest.raises(TypeError, match=f"'x' must be {words}"):
            validator(garbage, "x", *args)


@pytest.mark.parametrize(
    ("validator", "args"),
    [
        (require_positive_array, ()),
        (require_finite_array, ()),
        (require_per_band, (np.array([100.0, 200.0]), "frequencies")),
        (require_1d_signal, ()),
        (require_above_absolute_zero_array, ()),
    ],
)
@pytest.mark.parametrize(
    "complex_input",
    [[1 + 2j], np.array([1 + 2j]), np.complex128(1 + 2j)],
)
def test_a_complex_input_is_refused_rather_than_flattened(
    validator: Callable[..., object],
    args: tuple[object, ...],
    complex_input: object,
) -> None:
    """A complex array must not arrive as its real part.

    ``np.asarray(z, dtype=float64)`` does not fail on a complex array: it
    drops the imaginary part and emits a ``ComplexWarning``, which is a
    warning and not an error, so ``np.array([1 + 2j])`` used to reach the
    guards as ``[1.0]`` and satisfy every one of them. A *list* of complex
    numbers raised, because that path fails the conversion outright, so the
    two spellings of the same input disagreed with each other. A complex
    value where a real one belongs is the wrong type, so the refusal is a
    ``TypeError``.
    """
    with pytest.raises(TypeError, match="'x' must be real, not complex"):
        validator(complex_input, "x", *args)


@pytest.mark.parametrize(
    "guard",
    [
        require_positive,
        require_finite,
        require_non_negative,
        require_fraction,
        require_above_absolute_zero,
    ],
)
@pytest.mark.parametrize(
    "complex_number",
    [
        np.complex128(0.5 + 0.25j),
        np.complex64(0.5 + 0.25j),
        0.5 + 0.25j,
        np.array(0.5j),
    ],
    ids=["complex128", "complex64", "python", "zero-dimensional"],
)
def test_a_scalar_guard_refuses_a_complex_number(
    guard: Callable[[float, str], float], complex_number: object
) -> None:
    """A NumPy complex number is refused as a Python one is, not read as its real part.

    :func:`float` refuses ``0.5 + 0.25j`` and reads ``np.complex128(0.5 +
    0.25j)`` as ``0.5`` with no more than a ``ComplexWarning``, so every
    shared scalar guard took a NumPy complex number for the real number it
    was not. Each refuses it now, through :func:`require_real`.
    """
    with pytest.raises(TypeError, match="'x' must be a number"):
        guard(complex_number, "x")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="no complex here"):
        require_real(complex_number, "no complex here")


def test_an_array_of_objects_that_holds_a_bytearray_holds_text() -> None:
    """A ``bytearray`` element is parsed as a ``bytes`` one is, so it is text.

    numpy converts an element of an array of objects with :func:`float`,
    and ``float(bytearray(b"94"))`` is ``94.0``: the array guards read the
    array as ``[94.0, 0.5]``.
    """
    objects = _objects(bytearray(b"94"), bytearray(b"0.5"))
    assert holds_text(objects)
    with pytest.raises(TypeError, match="'x' must be numbers, not text"):
        require_finite_array(objects, "x")
    assert not holds_text(_objects(94.0, 0.5))


def test_an_array_of_objects_that_holds_a_complex_number_is_refused() -> None:
    """An object array is read item by item, and a NumPy complex item is refused.

    ``np.array([np.complex128(1 + 2j)], dtype=object)`` has no complex dtype
    to ask for, and its conversion to float64 keeps ``1.0``.
    """
    objects = np.array([1.0, np.complex128(1 + 2j)], dtype=object)
    with pytest.raises(TypeError, match="'x' must be real, not complex"):
        require_finite_array(objects, "x")


def test_a_record_of_arrays_or_numbers_refuses_a_complex_member() -> None:
    """A pair of arrays and a sequence of numbers each refuse a complex member."""
    with pytest.raises(TypeError, match="'curve' must be a pair .* of real numbers"):
        pair_of_arrays(([0.0, 90.0], np.array([0.0, 1j])), "curve", "(angles, levels)")
    with pytest.raises(TypeError, match="'curve' must be a pair .* of real numbers"):
        pair_of_arrays(
            ([0.0, 90.0], [np.complex128(1j), 0.0]), "curve", "(angles, levels)"
        )
    with pytest.raises(TypeError, match="'limits' must be"):
        floats_of((1.0, np.complex128(2 + 1j)), "limits", "a (low, high) pair")


@pytest.mark.parametrize(
    "texts",
    [["0.0", "90.0"], np.array(["0.0", "90.0"]), np.array(["0.0"], dtype=object)],
    ids=["list", "array", "objects"],
)
def test_a_pair_of_arrays_refuses_a_member_of_texts(texts: object) -> None:
    """A member written as texts is the wrong type, not the numbers it spells.

    ``np.array(["0.0", "90.0"], dtype=np.float64)`` parses the texts, so a
    curve whose angles were left as text was read as numbers.
    """
    with pytest.raises(
        TypeError, match="'curve' must be a pair .* of numbers, not text"
    ):
        pair_of_arrays((texts, [0.0, 1.0]), "curve", "(angles, levels)")


# ---------------------------------------------------------------------------
# The finite guard reads both axes of a complex field
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("bad", [complex(2.0, np.nan), complex(2.0, np.inf)])
def test_a_non_finite_imaginary_part_is_refused(bad: complex) -> None:
    """A complex field is undetermined when either of its axes is.

    Casting to ``float64`` to run the check discarded the imaginary part on
    the way in, so a value whose real part was intact passed whatever its
    phase held. The quantities read off such a field are exactly the ones
    that live on the discarded axis -- a magnitude, a loss factor -- and they
    took the ``NaN`` on as a measured number.
    """
    result = _Result(first=np.array([complex(1.0, 1.0), bad]))
    with pytest.raises(ValueError, match="'first' must contain only finite values"):
        require_finite_fields(result, "first")


@pytest.mark.parametrize("bad", [complex(2.0, np.nan), complex(2.0, np.inf)])
def test_a_lone_complex_scalar_is_measured_on_both_axes_too(bad: complex) -> None:
    """The nought-dimensional case takes the scalar wording, not the array one."""
    result = _Result(first=bad)
    with pytest.raises(ValueError, match="'first' must be finite"):
        require_finite_fields(result, "first")


@pytest.mark.parametrize("bad", [complex(2.0, np.nan), complex(2.0, np.inf)])
def test_an_array_of_objects_is_measured_on_both_axes_too(bad: complex) -> None:
    """A NumPy complex number held as an object is read whole, not as its real part.

    An array of objects has no complex dtype to ask for, and its conversion
    to ``float64`` kept the real part of ``np.complex128(2 + inf j)`` with no
    more than a ``ComplexWarning``, so the infinity passed the guard.
    """
    result = _Result(first=np.array([1.0, np.complex128(bad)], dtype=object))
    with pytest.raises(ValueError, match="'first' must contain only finite values"):
        require_finite_fields(result, "first")


def test_a_finite_complex_field_is_admitted_intact() -> None:
    """The guard must not complain about the phase it now reads.

    Numpy announced the discarded imaginary part as a ``ComplexWarning`` on
    every construction, valid data included; that warning was the tell, and
    a suite run under ``-W error`` would have caught the defect years sooner.
    Pin its absence, so the cast cannot come back unnoticed.
    """
    result = _Result(first=np.array([complex(1.0, 2.0), complex(3.0, -4.0)]))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        require_finite_fields(result, "first")


@pytest.mark.parametrize(
    ("label", "value"),
    [
        ("scalar", np.nan),
        ("array", np.array([1.0, np.inf])),
    ],
)
def test_the_real_wording_is_unchanged(label: str, value: object) -> None:
    """The messages a hundred result types already pin, said the same way.

    Only the complex branch is new; a real field must still reach the same
    two sentences, chosen by rank, with the owning type in front of them.
    """
    what = "be finite" if label == "scalar" else "contain only finite values"
    result = _Result(first=value)
    with pytest.raises(ValueError, match=rf"_Result: 'first' must {what}\."):
        require_finite_fields(result, "first")


def test_a_non_numeric_field_is_refused_naming_the_field() -> None:
    """Dropping the cast must not drop what the cast also refused.

    Coercion is what kept a string or an object out, and it answered for it
    badly: numpy's own "could not convert string to float" for the one and a
    bare ``TypeError``, not the documented ``ValueError``, for the other,
    neither naming the field nor the result it sits on.
    """
    # A text, read as a number or not, and an object are the wrong type.
    for garbage in ("abc", np.array(["a", "b"]), ("94.0",), object(), [object()]):
        result = _Result(first=garbage)
        with pytest.raises(TypeError, match="_Result: 'first' must be numeric"):
            require_finite_fields(result, "first")


def test_a_count_is_a_whole_number_and_nothing_else() -> None:
    """A count of storeys or harmonics: an int, a numpy integer or a whole
    float, never a bool, a string, an infinity or a fraction, and at least
    the minimum asked for.
    """
    assert require_count(3, "storeys") == 3
    assert require_count(3.0, "storeys") == 3
    assert require_count(np.int64(4), "storeys") == 4
    assert require_count(0, "storeys", at_least=0) == 0
    # What is not a number at all is the wrong type; a number that is not
    # whole, or is below the minimum, is the right type with a wrong value.
    for bad in (True, "3", None, [3]):
        with pytest.raises(TypeError, match="'storeys' must be a whole number"):
            require_count(bad, "storeys")
    for bad in (float("inf"), float("nan"), 2.9, 0, -1):
        with pytest.raises(
            ValueError, match="'storeys' must be a whole number, at least 1"
        ):
            require_count(bad, "storeys")


def test_an_integer_is_one_by_its_type() -> None:
    """``int()`` takes a fraction, a flag and a text as an integer; the test
    of one takes a Python or NumPy integer only.
    """
    for good in (0, -3, np.int8(2), np.uint64(7)):
        assert is_integer(good)
    for bad in (True, np.True_, 1.0, 1.5, "1", b"1", None, np.array(1), [1]):
        assert not is_integer(bad)


def test_indices_are_integers_in_a_sequence_or_a_one_dimensional_integer_array() -> (
    None
):
    """Each index is an integer by its type, in the order given; a text is
    not a sequence of its letters, and an array is one-dimensional and of an
    integer dtype.
    """
    assert indices_of([2, np.int64(0)], "rows") == (2, 0)
    assert indices_of(range(3), "rows") == (0, 1, 2)
    assert indices_of(np.array([1, 0], dtype=np.uint8), "rows") == (1, 0)
    assert indices_of((), "rows") == ()
    for bad in ([0.5], [1.0], [True], ["1"], [np.array(1)], [None]):
        with pytest.raises(TypeError, match="'rows' must hold integer indices"):
            indices_of(bad, "rows")
    for bad in ("01", b"01", bytearray(b"\x00\x01"), 3, None):
        with pytest.raises(TypeError, match="'rows' must be a sequence of integer"):
            indices_of(bad, "rows")
    for bad in (np.array(1), np.array([[0, 1]]), np.array([1.0]), np.array([True])):
        with pytest.raises(TypeError, match="'rows' must be integer indices"):
            indices_of(bad, "rows")


def _objects(*members: object) -> np.ndarray:
    """An array of objects holding *members* as they are, none spread over a row."""
    held = np.empty(len(members), dtype=object)
    for index, member in enumerate(members):
        held[index] = member
    return held


@pytest.mark.parametrize(
    "value",
    [
        b"rigid",
        np.bytes_(b"rigid"),
        bytearray(b"rigid"),
        ["400"],
        np.array("400"),
        [bytearray(b"400")],
        (400.0, bytearray(b"410")),
        [[bytearray(b"4")], [bytearray(b"4")]],
        deque([bytearray(b"400")]),
        _objects(bytearray(b"400"), 410.0),
        _objects([bytearray(b"400")]),
    ],
    ids=[
        "bytes",
        "numpy-bytes",
        "bytearray",
        "text-in-a-list",
        "zero-dimensional-text",
        "bytearray-in-a-list",
        "bytearray-in-a-tuple",
        "bytearray-nested",
        "bytearray-in-a-deque",
        "bytearray-in-an-array-of-objects",
        "bytearray-in-a-list-in-an-array-of-objects",
    ],
)
def test_a_text_beside_a_choice_is_refused_naming_the_options(value: object) -> None:
    """A text that is not a ``str`` is neither the choice nor its numbers.

    A ``bytearray`` inside a sequence was let through: numpy reads it as a
    row of the codes of its characters, so ``[bytearray(b"400")]`` reached
    the numbers as ``[[52, 48, 48]]``, and :func:`float` parses one inside
    an array of objects as the number it spells.
    """
    with pytest.raises(
        TypeError, match=r"'termination' must be one of \('rigid', 'free'\)"
    ):
        refuse_text_beside_choice(value, "termination", ("rigid", "free"))


@pytest.mark.parametrize(
    "value",
    [400.0, 400 + 10j, [400.0, 410.0], np.ones(3), None, object()],
    ids=["number", "complex", "numbers", "array", "none", "object"],
)
def test_what_holds_no_text_is_left_to_the_numbers(value: object) -> None:
    """Numbers pass, and so does what is no text: the conversion that follows refuses it."""
    refuse_text_beside_choice(value, "termination", ("rigid", "free"))


def _holding_itself() -> list[object]:
    """A list of a number and of itself."""
    held: list[object] = [400.0]
    held.append(held)
    return held


def _objects_holding_themselves(shape: tuple[int, ...]) -> np.ndarray:
    """An array of objects whose one member is the array itself."""
    held = np.empty(shape, dtype=object)
    held[(0,) * len(shape)] = held
    return held


def _nested(depth: int) -> object:
    """``400.0`` inside *depth* lists, one in the other."""
    value: object = 400.0
    for _ in range(depth):
        value = [value]
    return value


@pytest.mark.parametrize(
    "value",
    [
        _holding_itself(),
        [[_holding_itself()]],
        _objects_holding_themselves((1,)),
        _objects_holding_themselves(()),
        _objects(_holding_itself()),
        _nested(33),
    ],
    ids=[
        "list",
        "list-in-lists",
        "array-of-objects",
        "zero-dimensional-array-of-objects",
        "list-in-an-array-of-objects",
        "nested-33-deep",
    ],
)
def test_a_sequence_that_holds_itself_is_refused_naming_the_options(
    value: object,
) -> None:
    """A sequence nested deeper than any array holds no numbers, and the walk ends.

    The walk that looks for a ``bytearray`` went into every member of a
    sequence with no bound, so a list that holds itself took it on until
    Python's recursion limit raised a ``RecursionError``, which names no
    parameter, where the parameter refuses what is not its numbers by name.
    It goes no deeper than the 32 axes the text check after it can read.
    """
    with pytest.raises(
        TypeError,
        match=(
            r"'termination' must be one of \('rigid', 'free'\) as a str, or "
            "numbers, not a sequence nested more than 32 deep"
        ),
    ):
        refuse_text_beside_choice(value, "termination", ("rigid", "free"))


def test_numbers_as_deep_as_an_array_and_a_row_held_twice_pass() -> None:
    """32 axes is as deep as the text check reads, and a row held twice holds no cycle."""
    refuse_text_beside_choice(_nested(32), "termination", ("rigid", "free"))
    row = [400.0, 410.0]
    refuse_text_beside_choice([row, row], "termination", ("rigid", "free"))
    refuse_text_beside_choice(_objects(row, row), "termination", ("rigid", "free"))


@pytest.mark.parametrize(
    ("members", "message"),
    [
        ((["0", "1"], [0.0, 1.0]), "'polar' must be a pair .* of numbers, not text"),
        (
            ([1j, 2j], [0.0, 1.0]),
            "'polar' must be a pair .* of real numbers, not complex",
        ),
    ],
    ids=["text", "complex"],
)
def test_a_member_of_a_sequence_of_arrays_holds_numbers(
    members: tuple[object, object], message: str
) -> None:
    """A member was converted by numpy, which parsed a text and dropped an imaginary part."""
    with pytest.raises(TypeError, match=message):
        arrays_of(members, "polar", "a pair (angles_deg, relative_db) of two arrays", 2)


#: What iterating reads as members a caller did not mean: the codes of the
#: characters of a ``bytearray``, the keys of a mapping, and the members of a
#: set in no order.
_NO_SEQUENCES = {
    "bytearray": bytearray(b"ab"),
    "mapping": {0: [1.0], 1: [2.0]},
    "set": frozenset({1.0, 2.0}),
}


@pytest.mark.parametrize("value", _NO_SEQUENCES.values(), ids=_NO_SEQUENCES.keys())
def test_a_sequence_of_arrays_is_refused_whole_when_it_is_none(value: object) -> None:
    """A ``bytearray`` was read as one array per byte code, a mapping as its keys."""
    with pytest.raises(TypeError, match=r"'polar' must be a pair .*, not "):
        arrays_of(value, "polar", "a pair (angles_deg, relative_db) of two arrays", 2)


@pytest.mark.parametrize("value", _NO_SEQUENCES.values(), ids=_NO_SEQUENCES.keys())
def test_a_sequence_of_numbers_is_refused_whole_when_it_is_none(value: object) -> None:
    """``{i: 1.0 for i in range(8)}`` gave its keys 0 to 7 as the coefficients."""
    with pytest.raises(TypeError, match=r"'coefficients' must be eight numbers, not "):
        floats_of(value, "coefficients", "eight numbers")


@pytest.mark.parametrize(
    "value",
    [np.complex128(2.0 + 1.0j), np.complex64(2.0), np.array(2.0 + 1.0j), 2.0 + 1.0j],
    ids=["complex128", "complex64-real-valued", "zero-dimensional", "python"],
)
@pytest.mark.filterwarnings("error")
def test_one_number_is_refused_when_it_is_complex_of_any_kind(value: object) -> None:
    """``float()`` refuses a Python complex but keeps the real part of a numpy one.

    It did so with no more than a ``ComplexWarning``, and the guard returned
    the real part as the number.
    """
    with pytest.raises(TypeError, match="'x' must be real"):
        require_real(value, "'x' must be real")
    with pytest.raises(TypeError, match="'x' must be a number"):
        require_positive(value, "x")  # type: ignore[arg-type]


#: Whether a long double holds numbers a float does not: it does on x86-64
#: Linux (80 bits), and is a float on Windows and on macOS on Apple silicon.
_WIDE_LONG_DOUBLE = bool(np.finfo(np.longdouble).max > np.finfo(np.float64).max)

_ONLY_WITH_A_WIDE_LONG_DOUBLE = pytest.mark.skipif(
    not _WIDE_LONG_DOUBLE, reason="a long double is a float on this platform"
)

#: Finite numbers no float holds, by how a caller writes them, each built when
#: it is used: a long double is one only where it is wider than a float.
_BEYOND_A_FLOAT: dict[str, Callable[[], object]] = {
    "python integer": lambda: 10**400,
    "Fraction": lambda: Fraction(10**400, 3),
    "Decimal": lambda: Decimal("1e400"),
    "negative Decimal": lambda: Decimal("-1e400"),
    "long double": lambda: np.longdouble("1e400"),
    "negative long double": lambda: -np.longdouble("1e400"),
    "zero-dimensional long double array": lambda: np.array(np.longdouble("1e400")),
}


@pytest.mark.parametrize(
    "spelling",
    [
        pytest.param(
            spelling,
            marks=_ONLY_WITH_A_WIDE_LONG_DOUBLE if "long double" in spelling else (),
        )
        for spelling in _BEYOND_A_FLOAT
    ],
)
def test_one_number_no_float_holds_is_refused_whatever_its_type(spelling: str) -> None:
    """A finite number beyond a float's range is refused, as its docstring says.

    :func:`float` refuses a Python integer or a ``Fraction`` beyond its range
    with ``OverflowError``, which the reader turned into ``ValueError``, but
    reads a long double or a ``Decimal`` beyond it as an infinity, which the
    reader handed back as the number: a guard after it took an infinity the
    caller never gave, and one that admits an infinity kept it.
    """
    value = _BEYOND_A_FLOAT[spelling]()
    with pytest.raises(ValueError, match="'x' must be a number"):
        require_real(value, "'x' must be a number")
    with pytest.raises(ValueError, match="'limits' must be a pair"):
        floats_of([1.0, value], "limits", "a pair of numbers", 2)


@pytest.mark.parametrize(
    "value",
    [
        math.inf,
        -math.inf,
        np.float64(np.inf),
        Decimal("Infinity"),
        Decimal("-Infinity"),
        np.longdouble("inf"),
    ],
    ids=repr,
)
def test_an_infinity_the_caller_gives_is_read_as_that_infinity(value: object) -> None:
    """Only a finite number read as an infinity is refused; an infinity stays one."""
    read = require_real(value, "'x' must be a number")
    assert math.isinf(read)
    assert (read > 0) is bool(value > 0)  # type: ignore[operator]


#: A text that numpy does not see as one: a ``bytearray`` alone, inside a
#: list, beside numbers in a nested list, inside a list beside an array, and
#: in an array of objects.
_BYTEARRAYS = [
    bytearray(b"12"),
    [bytearray(b"12")],
    [[1.0, 2.0], bytearray(b"12")],
    (np.array([1.0]), [bytearray(b"9")]),
    np.array([bytearray(b"1"), 2.0], dtype=object),
]


@pytest.mark.parametrize(
    "value", _BYTEARRAYS, ids=["alone", "listed", "beside-numbers", "nested", "objects"]
)
def test_a_bytearray_among_numbers_is_refused_as_text(value: object) -> None:
    """numpy reads a ``bytearray`` as the codes of its characters.

    ``np.asarray([bytearray(b"12")], dtype=np.float64)`` is ``[[49.0, 50.0]]``,
    and beside numbers it is a row of them, so the shared readers took a
    text for two levels. It is refused as the text it is, by the readers of
    an array, by the text check every conversion that parses shares, and by
    the reader of a record's fields.
    """
    with pytest.raises(TypeError, match="'x' must be numbers, not text"):
        real_array(value, "x")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="'x' must be numbers, not text"):
        require_finite_array(value, "x")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="no text here"):
        refuse_text(value, "no text here")
    record = _Result(first=value)
    with pytest.raises(TypeError, match="'first' must be numeric, not text"):
        require_finite_fields(record, "first")


@pytest.mark.parametrize(
    "value",
    [[1 + 2j], [1.0, np.complex128(2j)], np.array([1.0, 2j]), np.complex64(1)],
    ids=["python", "numpy-in-a-list", "array", "numpy-scalar"],
)
@pytest.mark.filterwarnings("error")
def test_the_shared_reader_refuses_a_complex_value(value: object) -> None:
    """The real part of a complex value is a number the caller never gave."""
    with pytest.raises(TypeError, match="'levels' must be real, not complex"):
        real_array(value, "levels")  # type: ignore[arg-type]


def test_the_shared_reader_refuses_text_and_names_what_numpy_cannot_read() -> None:
    """A text is refused whatever it reads as, and numpy's anonymous refusals
    of an object or a ragged nesting are given the parameter's name.
    """
    with pytest.raises(TypeError, match="'levels' must be numbers, not text"):
        real_array(["94.0"], "levels")
    with pytest.raises(TypeError, match="'levels' must be numeric"):
        real_array([object()], "levels")
    with pytest.raises(ValueError, match="'levels' must be numeric"):
        real_array([[1.0], [1.0, 2.0]], "levels")
    looped: list[object] = [1.0]
    looped.append(looped)
    with pytest.raises(TypeError, match="nested more than 32 deep"):
        real_array(looped, "levels")  # type: ignore[arg-type]


def test_the_shared_reader_converts_numbers_as_numpy_does() -> None:
    """Numbers, ``None`` read as ``nan`` and the shape numpy gives them; an
    array already of floats comes back as itself unless a copy is asked for.
    """
    assert real_array([1, 2.5, np.float32(3.0)], "x").tolist() == [1.0, 2.5, 3.0]
    assert np.isnan(real_array(None, "x"))
    assert real_array([[1, 2], [3, 4]], "x").shape == (2, 2)
    given = np.array([1.0, 2.0])
    assert real_array(given, "x") is given
    copied = real_array(given, "x", copy=True)
    assert copied is not given
    np.testing.assert_array_equal(copied, given)


@pytest.mark.parametrize(
    "value",
    [
        ["1+2j"],
        "80",
        b"80",
        [bytearray(b"12")],
        [np.array([1.0 + 1j]), [bytearray(b"1")]],
        np.array(["0.5"]),
    ],
    ids=["text-in-list", "text", "bytes", "bytearray-in-list", "nested", "text-array"],
)
def test_the_complex_reader_refuses_text_by_name(value: object) -> None:
    """``np.asarray(x, dtype=np.complex128)`` parses a text and reads a
    ``bytearray`` as the codes of its characters; the reader refuses both.
    """
    with pytest.raises(TypeError, match="'reflection' must be numbers, not text"):
        complex_array(value, "reflection")  # type: ignore[arg-type]


def test_the_complex_reader_reads_numbers_of_every_kind() -> None:
    """A real number is a complex one with no imaginary part; an array of
    ``complex128`` comes back as itself unless a copy is asked for; numpy's
    anonymous refusals are given the parameter's name.
    """
    assert complex_array([1, 2.5, 1 + 2j], "z").tolist() == [1 + 0j, 2.5 + 0j, 1 + 2j]
    assert complex_array(np.float64(2.0), "z") == 2.0 + 0j
    assert complex_array([np.complex64(1j)], "z").dtype == np.complex128
    given = np.array([1.0 + 1j])
    assert complex_array(given, "z") is given
    copied = complex_array(given, "z", copy=True)
    assert copied is not given
    np.testing.assert_array_equal(copied, given)
    with pytest.raises(TypeError, match="'z' must be numeric"):
        complex_array([object()], "z")
    with pytest.raises(ValueError, match="'z' must be numeric"):
        complex_array([[1.0], [1.0, 2.0]], "z")


@pytest.mark.parametrize("reader", [real_array, complex_array], ids=["real", "complex"])
@pytest.mark.filterwarnings("ignore:the matrix subclass:PendingDeprecationWarning")
@pytest.mark.parametrize(
    "build",
    [
        lambda: np.matrix([[1.0, 2.0]]),
        lambda: np.matrix([[1, 2]]),
        lambda: np.ma.array([1.0, 2.0], mask=[False, True]),
    ],
    ids=["matrix", "integer-matrix", "masked"],
)
def test_a_subclass_of_an_array_is_read_as_the_plain_array_of_its_values(
    reader: Callable[..., np.ndarray], build: Callable[[], np.ndarray]
) -> None:
    """``astype`` keeps a subclass, whose ``**`` is a matrix power and whose
    reductions skip the masked values; both readers give the plain array
    ``np.asarray`` gives, a copy of it when one is asked for.
    """
    given = build()
    for copy in (False, True):
        read = reader(given, "x", copy=copy)
        assert type(read) is np.ndarray
        np.testing.assert_array_equal(read, np.asarray(given))
    assert not np.shares_memory(reader(given, "x", copy=True), given)


@pytest.mark.parametrize(
    "value",
    [np.complex128(2.0 + 1.0j), np.complex64(2.0), np.array(2.0j), 2.0 + 1.0j],
    ids=["complex128", "complex64-real-valued", "zero-dimensional", "python"],
)
def test_the_rank_check_of_every_scalar_guard_refuses_a_complex_number(
    value: object,
) -> None:
    """``require_scalar`` opens every scalar guard that reads its value through
    :func:`float`, which keeps the real part of a NumPy complex number.
    """
    with pytest.raises(TypeError, match="'x' must be a number, not a complex one"):
        require_scalar(value, "x")
