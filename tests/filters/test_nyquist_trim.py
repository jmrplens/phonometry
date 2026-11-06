#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A bank keeps the bands its sample rate holds, and warns only for limits the caller gave.

The default span runs from 12 Hz to 20 kHz, and at the CD rate the 20 kHz third
octave reaches 22.4 kHz, past fs/2 = 22.05 kHz. Every default bank at 44.1 kHz,
32 kHz, 22.05 kHz, 16 kHz or 8 kHz warned "Low sampling rate", which reads like
an error at the most common rate there is, about a band nobody asked for. The
default span is now trimmed to what the rate holds without a word; a span the
caller gave still warns, and names the bands it loses.
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

from phonometry import emission, filters


@pytest.mark.parametrize("fs", [8000, 16000, 22050, 32000, 44100])
def test_a_default_bank_trims_its_top_bands_without_a_warning(fs: int) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        bank = filters.OctaveFilterBank(fs, fraction=3)
    assert bank.upper_edges.max() <= fs / 2


def test_the_cd_rate_keeps_the_same_32_bands_it_kept_before() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        bank = filters.OctaveFilterBank(44100, fraction=3)
    assert bank.n_bands == 32
    assert bank.labels[-1] == "16k"


def test_octave_filter_on_the_default_span_says_nothing() -> None:
    x = np.random.default_rng(3).standard_normal(8000)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = filters.octave_filter(x, 8000, fraction=3)
    assert result.levels.size > 0


def test_limits_the_caller_gave_warn_and_name_the_band_left_out() -> None:
    with pytest.warns(
        filters.FilterBankWarning,
        match=(
            r"^Low sampling rate: fs = 44100 Hz cannot hold the 20 kHz band, "
            r"whose upper edge 22387 Hz is above fs/2 = 22050 Hz"
        ),
    ):
        bank = filters.OctaveFilterBank(44100, fraction=3, limits=[12, 20000])
    assert bank.n_bands == 32


def test_several_bands_left_out_are_named_from_first_to_last() -> None:
    with pytest.warns(
        filters.FilterBankWarning,
        match=r"cannot hold the 2 bands from 500 Hz to 1 kHz, whose upper edges",
    ):
        filters.OctaveFilterBank(1000, limits=[10.0, 1000.0])


def test_octave_filter_names_the_bands_left_out_at_every_call() -> None:
    """The design is cached, so a warning the design raised spoke only once."""
    x = np.random.default_rng(4).standard_normal(1000)
    for _ in range(2):
        with pytest.warns(filters.FilterBankWarning, match="Low sampling rate"):
            filters.octave_filter(x, 1000, limits=[10.0, 1000.0])


def test_sound_intensity_on_the_default_span_says_nothing() -> None:
    rng = np.random.default_rng(5)
    p1 = rng.standard_normal(8000)
    p2 = np.roll(p1, 1)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        emission.sound_intensity(p1, p2, 8000, spacing_m=0.012, fraction=3)


@pytest.mark.parametrize(
    ("fs", "fraction"), [(20, 3), (24, 3), (28.2, 3), (20, 1), (29, 1), (44.7, 1)]
)
def test_a_rate_that_holds_no_band_of_the_default_span_is_refused(
    fs: float, fraction: int
) -> None:
    """Trimming the default span in silence must not trim it to nothing.

    Below 28.25 Hz the upper edge of the lowest third octave, 12.5 Hz, lies
    above fs/2, and below 44.77 Hz that of the lowest octave, 16 Hz, does: the
    bank kept no band, and once its warning was gone nothing said the analysis
    was empty.
    """
    with pytest.raises(ValueError, match=rf"fs = {fs:g} Hz cannot hold any band"):
        filters.OctaveFilterBank(fs, fraction=fraction)


def test_octave_filter_refuses_a_rate_that_holds_no_band() -> None:
    with pytest.raises(ValueError, match=r"fs = 20 Hz cannot hold any band"):
        filters.octave_filter(np.zeros(200), 20, fraction=3)


def test_limits_the_caller_gave_that_keep_no_band_are_refused() -> None:
    """A bank of no band analyses nothing, whoever chose its span."""
    with pytest.raises(
        ValueError,
        match=(
            r"^fs = 20 Hz cannot hold any band from 10 Hz to 12\.5 Hz: the upper "
            r"edge of the lowest, 11\.22 Hz, is above fs/2 = 10 Hz\.$"
        ),
    ):
        filters.OctaveFilterBank(20, fraction=3, limits=[11, 13])


def test_limits_of_one_band_the_rate_cannot_hold_name_it() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^fs = 20 Hz cannot hold the 1 kHz band, the only one of the bank: "
            r"its upper edge, 1122 Hz, is above fs/2 = 10 Hz\.$"
        ),
    ):
        filters.OctaveFilterBank(20, fraction=3, limits=[1000, 1001])


def test_sound_intensity_refuses_a_rate_that_holds_no_band() -> None:
    rng = np.random.default_rng(6)
    p1 = rng.standard_normal(200)
    with pytest.raises(ValueError, match=r"fs = 20 Hz cannot hold any band"):
        emission.sound_intensity(p1, np.roll(p1, 1), 20, spacing_m=0.012, fraction=3)
