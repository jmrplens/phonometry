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

import re
from collections import UserString
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from phonometry import (
    building,
    electroacoustics,
    emission,
    environment,
    filters,
    io,
    metrology,
    simulation,
    speech,
)
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
    "method_b_source_ranking(rankings)": (
        lambda text: environment.method_b_source_ranking([text]),
        "rankings",
    ),
    "bin_amplitude_modulation(bands)": (
        lambda text: environment.bin_amplitude_modulation(
            np.zeros((2, 3)), np.array([5.0, 6.0]), bands=text
        ),
        "bands",
    ),
    "VideoOptions(ffmpeg_options)": (
        lambda text: io.VideoOptions(ffmpeg_options=text),
        "ffmpeg_options",
    ),
    "Signal(channel_labels)": (
        lambda text: io.Signal(np.zeros((3, 8)), 8000.0, channel_labels=text),
        "channel_labels",
    ),
    "scholte_speed(fluid)": (
        lambda text: simulation.scholte_speed(text, (5000.0, 2800.0, 2600.0)),
        "fluid",
    ),
}

#: Each public entry that reads one text as one name where a sequence of
#: names goes: what to call with a name in its place, a name it knows, and
#: the parameter whose name the refusal of a wrapper says.
_ONE_NAME: dict[str, tuple[Callable[[Any], object], str, str]] = {
    "binaural_indicators(parameters)": (
        lambda name: environment.binaural_indicators(
            np.zeros((2, 8)), 44_100.0, parameters=name
        ),
        "sound_pressure_level",
        "parameters",
    ),
    "standard_speech_spectra(vocal_efforts)": (
        speech.standard_speech_spectra,
        "normal",
        "vocal_efforts",
    ),
    "MicrophoneTraverse(targets)": (
        lambda name: emission.MicrophoneTraverse(
            positions_m=[[0.0, 0.0, 1.0], [0.0, 0.0, 2.0], [0.0, 0.0, 4.0]],
            levels=[[94.0], [88.0], [82.0]],
            targets=name,
        ),
        "boundary center",
        "targets",
    ),
    "NoiseEmissionDeclaration(basic_standards)": (
        lambda name: emission.NoiseEmissionDeclaration(
            (emission.OperatingModeDeclaration("Operating mode 1", 88.0, 2.0),),
            basic_standards=name,
        ),
        "ISO 3744",
        "basic_standards",
    ),
}


#: One character of ``"abc"`` as a refusal shows it: a text, or a code.
_A_CHARACTER = re.compile(r"'[abc]'|\b9[789]\b")


def _refusal(call: Callable[[], object]) -> BaseException:
    with pytest.raises((TypeError, ValueError)) as caught:
        call()
    return caught.value


@pytest.mark.parametrize("wrap", [UserString, str.encode], ids=["UserString", "bytes"])
@pytest.mark.parametrize("entry", sorted(_ENTRIES))
def test_a_wrapped_text_is_refused_as_the_text_is(
    entry: str, wrap: Callable[[str], object]
) -> None:
    call, name = _ENTRIES[entry]
    plain = _refusal(lambda: call("abc"))
    wrapped = _refusal(lambda: call(wrap("abc")))
    assert type(wrapped) is type(plain), (entry, wrapped, plain)
    assert name in str(wrapped), (entry, wrapped)
    # The refusal is of the whole text, never of one of its characters.
    assert not _A_CHARACTER.search(str(wrapped)), (entry, wrapped)


@pytest.mark.parametrize("wrap", [UserString, str.encode], ids=["UserString", "bytes"])
@pytest.mark.parametrize("entry", sorted(_ONE_NAME))
def test_a_wrapped_name_is_refused_by_name_and_never_split(
    entry: str, wrap: Callable[[str], object]
) -> None:
    call, known, name = _ONE_NAME[entry]
    call(known)
    wrapped = wrap(known)
    with pytest.raises(TypeError, match=name) as caught:
        call(wrapped)
    # The refusal shows the whole wrapper, not a character it was split into.
    assert f"got {wrapped!r}" in str(caught.value), (entry, caught.value)


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
