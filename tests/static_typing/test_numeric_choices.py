#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A choice beside numbers refuses a misspelt choice, for mypy too.

Five public parameters take one of a few words or numbers: the
``initial_state`` of ``filters.time_weighting``, the ``flow_resistivity`` of
``aircraft.terrain_screening_adjustment`` and of ``aircraft.RotorcraftGround``,
and the ``termination`` of ``materials.layered_absorber`` and of
``materials.diffuse_field_absorption``. They were annotated ``Literal[...] |
ArrayLike``, and numpy's ``ArrayLike`` admits any ``str``, so
``termination="rigidd"`` type-checked as numbers and only the call refused it.
Beside the ``Literal`` they take the package's array-like of numbers now,
which is ``ArrayLike`` without its texts and without arrays typed with another
dtype. Every call below runs; each refused one carries the code mypy refuses
it with, and CI type checks every file in this directory with unused ignores
reported, so a refusal that goes fails the build.
``scripts/check_parameter_annotations.py`` holds every public parameter to the
rule. The ``coefficients`` of ``materials.delany_bazley`` take the same
array-like of numbers beside their presets: they were annotated a ``tuple`` of
floats while the call took a list or an array of the eight numbers as well,
and so does the ``speech_spectrum`` of ``speech.speech_intelligibility_index``
beside its four vocal efforts: it was annotated ``ArrayLike`` alone, which
stated no choice at all.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry import aircraft, filters, materials, speech

if TYPE_CHECKING:
    from numpy.typing import DTypeLike, NDArray

    from phonometry._internal.types import NumericArrayLike

_FS = 48000.0
_CHANNELS = np.random.default_rng(5).standard_normal((2, 480))
_BANDS = np.array([125.0, 250.0, 500.0])


class _Impedance:
    """An object of another library that converts itself to an array."""

    def __array__(
        self, dtype: DTypeLike | None = None, /, *, copy: bool | None = None
    ) -> NDArray[np.complex128]:
        return np.full(3, 400.0 + 10.0j)


class _States:
    """Two channel states that convert themselves to an array."""

    def __array__(
        self, dtype: DTypeLike | None = None, /, *, copy: bool | None = None
    ) -> NDArray[np.float64]:
        return np.array([0.1, 0.2])


def _layers() -> list[materials.PorousLayer]:
    with pytest.warns(materials.PorousAbsorberWarning):
        medium = materials.miki(_BANDS, 20000.0)
    return [materials.PorousLayer(thickness_m=0.05, medium=medium)]


def _numbers(values: NumericArrayLike) -> NDArray[np.complex128]:
    return np.asarray(values, dtype=np.complex128)


def test_the_array_like_of_numbers_takes_the_listed_forms_of_numbers() -> None:
    """A number, a numpy number, nested sequences, arrays and what converts itself."""
    integers: NDArray[np.int64] = np.arange(3, dtype=np.int64)
    flags: NDArray[np.bool_] = np.ones(3, dtype=np.bool_)
    rows: list[NDArray[np.float64]] = [np.zeros(3), np.ones(3)]
    forms: list[NDArray[np.complex128]] = [
        _numbers(values=True),
        _numbers(2),
        _numbers(2.5),
        _numbers(1.0 + 2.0j),
        _numbers(np.float32(2.5)),
        _numbers(np.int64(2)),
        _numbers(np.complex64(1.0j)),
        _numbers(np.True_),
        _numbers([1, 2, 3]),
        _numbers((1.0, 2.0, 3.0)),
        _numbers([[1.0, 2.0], [3.0, 4.0]]),
        _numbers([1.0j, 2.0j]),
        _numbers(range(3)),
        _numbers([np.float32(1.0), np.float32(2.0)]),
        _numbers(integers),
        _numbers(flags),
        _numbers(rows),
        _numbers(_Impedance()),
    ]
    assert [form.ndim for form in forms] == [0] * 8 + [1, 1, 2, 1, 1, 1, 1, 1, 2, 1]


def test_the_array_like_of_numbers_refuses_every_text() -> None:
    """A text, a bytes, texts in a sequence and an array of texts are no numbers."""
    texts: list[str] = ["rigid"]
    words: NDArray[np.str_] = np.array(["rigid"])
    with pytest.raises(ValueError, match="malformed string"):
        _numbers("rigid")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="malformed string"):
        _numbers(b"rigid")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="malformed string"):
        _numbers(["rigid"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="malformed string"):
        _numbers(texts)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="malformed string"):
        _numbers(words)  # type: ignore[arg-type]


def test_the_array_like_of_numbers_refuses_an_array_typed_with_another_dtype() -> None:
    """An object, generic, date or duration array, or a buffer, is typed as no numbers.

    ``ArrayLike`` admitted each of them, and numpy converts each of them all
    the same, an object array of numbers among them: a leniency the type
    does not state. The type of an object array says nothing of what it
    holds, and ``NDArray[np.generic]`` cannot be admitted without an array
    of texts, whose dtype is one.
    """
    objects: NDArray[np.object_] = np.array([1.0, 2.0], dtype=object)
    generic: NDArray[np.generic] = np.zeros(2)
    dates: NDArray[np.datetime64] = np.array(["2026-10-29"], dtype="datetime64[D]")
    durations: NDArray[np.timedelta64] = np.array([1], dtype="timedelta64[s]")
    converted = [
        _numbers(objects),  # type: ignore[arg-type]
        _numbers(generic),  # type: ignore[arg-type]
        _numbers(dates),  # type: ignore[arg-type]
        _numbers(durations),  # type: ignore[arg-type]
        _numbers(memoryview(b"ab")),  # type: ignore[arg-type]
    ]
    assert [form.shape for form in converted] == [(2,), (2,), (1,), (1,), (2,)]


def test_a_time_weighting_starts_from_a_choice_or_numbers() -> None:
    """None, a choice, a number of any kind, or one state per channel."""
    states: NDArray[np.float64] = np.array([0.1, 0.2])
    whole: NDArray[np.int64] = np.ones(2, dtype=np.int64)
    for start in (None, "zero", "first", 0.5, 1, np.float32(0.5)):
        assert filters.time_weighting(_CHANNELS, _FS, initial_state=start).shape == (
            2,
            480,
        )
    for per_channel in ([0.1, 0.2], (0.1, 0.2), states, whole, _States()):
        out = filters.time_weighting(_CHANNELS, _FS, initial_state=per_channel)
        assert out.shape == (2, 480)


def test_a_termination_closes_the_stack_by_name_or_by_impedance() -> None:
    """A named wall, one impedance, or one impedance per band in any form."""
    layers = _layers()
    per_band: NDArray[np.complex128] = np.full(3, 400.0 + 10.0j)
    for termination in (
        "rigid",
        "free",
        400.0 + 0.0j,
        1000,
        np.complex128(400.0 + 10.0j),
        [400.0 + 0.0j] * 3,
        (400.0, 410.0, 420.0),
        [np.float32(400.0)] * 3,
        per_band,
        _Impedance(),
    ):
        one = materials.layered_absorber(_BANDS, layers, termination=termination)
        diffuse = materials.diffuse_field_absorption(
            _BANDS, layers, termination=termination
        )
        assert one.absorption.shape == diffuse.absorption.shape == (3,)


def test_a_flow_resistivity_is_a_class_letter_or_numbers() -> None:
    """A Nordtest class, a value in Pa s/m2, or one value per segment or point."""
    grid: NDArray[np.float64] = np.full((2, 2), 2.0e4)
    for resistivity in ("G", 2.0e4, 200, np.float64(2.0e4), [2.0e4, 3.0e4]):
        screened = aircraft.terrain_screening_adjustment(
            (0.0, 1.0),
            (100.0, 1.5),
            [0.0, 50.0, 100.0],
            [0.0, 0.0, 0.0],
            frequencies=_BANDS,
            flow_resistivity=resistivity,
        )
        assert screened.adjustment.shape == (3,)
    for held in ("G", 2.0e4, np.int64(200), [[2.0e4, 3.0e4]], grid):
        assert aircraft.RotorcraftGround(flow_resistivity=held).receiver_height_m == 1.2


def test_a_misspelt_choice_is_refused_before_the_call() -> None:
    """Each misspelling is a type error, and a ValueError when the call runs."""
    layers = _layers()
    with pytest.raises(ValueError, match="'initial_state' must be one of"):
        filters.time_weighting(_CHANNELS, _FS, initial_state="ZERO")  # type: ignore[call-overload]
    with pytest.raises(ValueError, match="'termination' must be one of"):
        materials.layered_absorber(_BANDS, layers, termination="rigidd")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="'termination' must be one of"):
        materials.diffuse_field_absorption(_BANDS, layers, termination="Rigid")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="'flow_resistivity' must be one of"):
        aircraft.terrain_screening_adjustment(
            (0.0, 1.0),
            (100.0, 1.5),
            [0.0, 100.0],
            [0.0, 0.0],
            frequencies=_BANDS,
            flow_resistivity="Gg",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="'flow_resistivity' must be one of"):
        aircraft.RotorcraftGround(flow_resistivity="g")  # type: ignore[arg-type]


def test_delany_bazley_takes_a_preset_or_its_eight_numbers() -> None:
    """A preset name, or the eight coefficients as a tuple, a list or an array."""
    preset = materials.DELANY_BAZLEY_COEFFICIENTS["garai_pompoli"]
    named: NDArray[np.float64] = np.asarray(preset)
    for coefficients in ("garai_pompoli", tuple(preset), list(preset), named):
        with pytest.warns(materials.PorousAbsorberWarning):
            medium = materials.delany_bazley(_BANDS, 20000.0, coefficients=coefficients)
        assert medium.characteristic_impedance.shape == (3,)
    with pytest.raises(ValueError, match="'coefficients' must be one of"):
        materials.delany_bazley(_BANDS, 20000.0, coefficients="garai")  # type: ignore[arg-type]


def test_a_speech_spectrum_is_a_vocal_effort_or_its_levels() -> None:
    """A vocal effort, or one level per band, in any form of numbers."""
    levels: NDArray[np.float64] = np.full(18, 60.0)
    for spectrum in ("normal", "shout", [60.0] * 18, tuple([60] * 18), levels):
        assert 0.0 <= speech.speech_intelligibility_index(spectrum).sii <= 1.0
    with pytest.raises(ValueError, match="'speech_spectrum' must be one of"):
        speech.speech_intelligibility_index("Normal")  # type: ignore[arg-type]
