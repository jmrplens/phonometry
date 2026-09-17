#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The result a filter bank hands back, and the spectrum it draws for itself.

``octave_filter`` used to return two items, or three when ``sigbands`` asked
for the band waveforms, which is why it needed twelve overload declarations to
be typed at all. It returns one named result now. These tests cover the part a
type checker cannot: that the fields carry what they say, that the two
accessors refuse rather than hand back a ``None``, and that the renderer draws
the levels it was given rather than an empty axes with the right labels on it.
"""

from __future__ import annotations

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import filters

FS = 48000


def _tone_over_noise(seed: int = 7) -> np.ndarray:
    """A 1 kHz tone on a sloping floor: one band well clear of the rest."""
    t = np.arange(FS) / FS
    rng = np.random.default_rng(seed)
    noise = np.cumsum(rng.standard_normal(FS))
    noise /= np.std(noise)
    return 0.4 * np.sin(2 * np.pi * 1000.0 * t) + 0.05 * noise


@pytest.fixture(autouse=True)
def _close_figures() -> None:
    """Every test here draws; none of them should leave a figure open."""
    yield
    plt.close("all")


# ---------------------------------------------------------------------------
# The fields
# ---------------------------------------------------------------------------
def test_one_level_per_band_centre() -> None:
    """The two sequences are read side by side, so they have to line up."""
    result = filters.octave_filter(_tone_over_noise(), FS, fraction=3)

    assert result.levels is not None
    assert result.levels.shape == (len(result.frequencies),)


def test_the_loudest_band_is_the_band_the_tone_is_in() -> None:
    """The levels are the levels, not some other array of the right length."""
    result = filters.octave_filter(_tone_over_noise(), FS, fraction=3)
    assert result.levels is not None

    loudest = result.frequencies[int(np.argmax(result.levels))]

    assert float(loudest) == pytest.approx(1000.0, rel=0.06)


def test_a_call_that_asks_for_no_band_keeps_none() -> None:
    """Splitting into bands costs a copy per band, so it is not done unasked."""
    assert filters.octave_filter(_tone_over_noise(), FS).bands is None


def test_a_call_that_asks_for_bands_gets_one_per_centre() -> None:
    """And they are waveforms, not levels: as long as the input."""
    result = filters.octave_filter(_tone_over_noise(), FS, sigbands=True)
    bands = result.require_bands()

    assert len(bands) == len(result.frequencies)
    assert np.asarray(bands[0]).shape == (FS,)


def test_nominal_labels_come_back_as_labels() -> None:
    """The IEC 61260-1 labels are strings, and stay strings."""
    result = filters.octave_filter(_tone_over_noise(), FS, nominal=True)

    assert all(isinstance(f, str) for f in result.frequencies)


# ---------------------------------------------------------------------------
# The two accessors
# ---------------------------------------------------------------------------
def test_asking_for_bands_that_were_not_kept_names_the_argument() -> None:
    """A message that says what to do beats a None that fails further on."""
    result = filters.octave_filter(_tone_over_noise(), FS)

    with pytest.raises(ValueError, match="sigbands=True"):
        result.require_bands()


def test_asking_for_levels_that_were_not_computed_names_the_argument() -> None:
    """The same, for the other half of the result."""
    bank = filters.OctaveFilterBank(fs=FS, fraction=1, limits=[125.0, 4000.0])
    result = bank.filter(_tone_over_noise(), sigbands=True, calculate_level=False)

    with pytest.raises(ValueError, match="calculate_level=False"):
        result.require_levels()


def test_the_accessors_return_what_is_there() -> None:
    """They narrow a type; they must not change a value doing it."""
    result = filters.octave_filter(_tone_over_noise(), FS, sigbands=True)

    assert result.require_levels() is result.levels
    assert result.require_bands() is result.bands


# ---------------------------------------------------------------------------
# What the renderer draws
# ---------------------------------------------------------------------------
def test_the_drawn_line_is_the_levels() -> None:
    """Looking at a plot is not covering it: this reads the line back out."""
    result = filters.octave_filter(_tone_over_noise(), FS, fraction=3)
    assert result.levels is not None

    ax = result.plot()
    (line,) = ax.get_lines()

    assert np.allclose(line.get_ydata(), result.levels)
    assert np.allclose(line.get_xdata(), np.asarray(result.frequencies, dtype=float))


def test_a_multichannel_result_draws_one_line_per_channel() -> None:
    """Two channels are two lines, each labelled, not one averaged line."""
    x = np.stack([_tone_over_noise(), 0.5 * _tone_over_noise(seed=8)])
    result = filters.octave_filter(x, FS, fraction=3)

    ax = result.plot()

    assert len(ax.get_lines()) == 2
    assert ax.get_legend() is not None


def test_nominal_labels_are_drawn_as_the_tick_labels() -> None:
    """A string band centre has no place on a log frequency axis."""
    result = filters.octave_filter(_tone_over_noise(), FS, nominal=True)

    ax = result.plot()

    drawn = [t.get_text() for t in ax.get_xticklabels()]
    assert drawn == [str(f) for f in result.frequencies]


def test_a_result_with_no_level_refuses_to_draw() -> None:
    """An empty axes with the right labels on it is worse than an error."""
    bank = filters.OctaveFilterBank(fs=FS, fraction=1, limits=[125.0, 4000.0])
    result = bank.filter(_tone_over_noise(), sigbands=True, calculate_level=False)

    with pytest.raises(ValueError, match="calculate_level=False"):
        result.plot()


def test_the_spanish_labels_are_spanish() -> None:
    """The renderer is registered for both languages like every other one."""
    result = filters.octave_filter(_tone_over_noise(), FS, fraction=3)

    ax = result.plot(language="es")

    assert "Nivel de banda" in ax.get_ylabel()
    assert "Frecuencia" in ax.get_xlabel()


def test_the_spanish_nominal_labels_carry_the_decimal_comma() -> None:
    """``set_xticklabels`` installs fixed strings that no localiser reaches.

    Every other figure in the corpus writes 31,5 in Spanish, and a gate holds
    the whole corpus to it. A nominal spectrum sets its tick labels by hand,
    which is the one way round that gate, so the labels are localised here.
    """
    result = filters.octave_filter(_tone_over_noise(), FS, fraction=3, nominal=True)

    ax = result.plot(language="es")
    drawn = [t.get_text() for t in ax.get_xticklabels()]

    assert "31,5" in drawn
    assert not any("." in label for label in drawn)


def test_an_unknown_language_is_refused() -> None:
    """The house rule for every ``.plot()`` in the tree."""
    result = filters.octave_filter(_tone_over_noise(), FS, fraction=3)

    with pytest.raises(ValueError, match="language"):
        result.plot(language="xx")
