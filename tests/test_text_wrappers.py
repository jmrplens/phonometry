#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A text wrapped in a ``UserString`` is refused wherever the text is.

A text is a sequence of its characters, so a test that tells a pair or a list
of labels from a text by ``isinstance(x, str | bytes | bytearray)`` let a
``collections.UserString`` through, and the wrapper was measured, split or
read character by character: ``FDTD2D(shape=UserString("abc"))`` was a
``ValueError`` about its length where ``"abc"`` is a ``TypeError``, and
``combined_standard_uncertainty([UserString("12")])`` a ``TypeError`` about a
nesting more than 32 deep. Every such test now asks the one predicate of
``phonometry._internal.validation``, :func:`is_text`; this holds each public
entry that tells a text from a sequence to refusing the wrapper as it
refuses the text, by the parameter's name.
"""

from __future__ import annotations

from collections import UserString
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from phonometry import building, electroacoustics, filters, metrology, simulation
from phonometry._internal.validation import is_text

if TYPE_CHECKING:
    from collections.abc import Callable

#: Each public entry that tells a text from a sequence: what to call with the
#: text in its place, and the parameter whose name the refusal says.
_ENTRIES: dict[str, tuple[Callable[[Any], object], str]] = {
    "FDTD2D(shape)": (
        lambda text: simulation.FDTD2D(shape=text, dx=0.01, c=343.0),
        "shape",
    ),
    "combined_standard_uncertainty(contributions)": (
        lambda text: metrology.combined_standard_uncertainty([text]),
        "contributions",
    ),
    "loudest_corner(excluded)": (
        lambda text: building.loudest_corner([80.0, 81.0, 79.0, 82.0], excluded=text),
        "excluded",
    ),
    "FractionalOctaveBands(labels)": (
        lambda text: filters.FractionalOctaveBands(
            frequencies=np.array([1000.0]),
            lower_edges=np.array([891.0]),
            upper_edges=np.array([1122.0]),
            labels=text,
        ),
        "labels",
    ),
    "LoudspeakerRatings(frequency_range)": (
        lambda text: electroacoustics.LoudspeakerRatings(frequency_range=text),
        "frequency_range",
    ),
}


def _refusal(call: Callable[[], object]) -> BaseException:
    with pytest.raises((TypeError, ValueError)) as caught:
        call()
    return caught.value


@pytest.mark.parametrize("entry", sorted(_ENTRIES))
def test_a_wrapped_text_is_refused_as_the_text_is(entry: str) -> None:
    call, name = _ENTRIES[entry]
    plain = _refusal(lambda: call("abc"))
    wrapped = _refusal(lambda: call(UserString("abc")))
    assert type(wrapped) is type(plain), (entry, wrapped, plain)
    assert name in str(wrapped), (entry, wrapped)


@pytest.mark.parametrize(
    ("value", "text"),
    [
        ("12", True),
        (b"12", True),
        (bytearray(b"12"), True),
        (UserString("12"), True),
        (np.str_("12"), True),
        ((1, 2), False),
        ([1.0, 2.0], False),
        (memoryview(b"12"), False),
        (np.array([1.0, 2.0]), False),
    ],
)
def test_is_text_tells_a_text_and_its_wrapper_from_a_sequence(
    value: object, *, text: bool
) -> None:
    assert is_text(value) is text
