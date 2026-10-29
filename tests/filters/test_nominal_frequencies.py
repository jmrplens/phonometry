#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for IEC 61260-1 nominal frequency helpers and opt-in nominal label support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from phonometry import filters
from phonometry.filters.frequencies import (
    _extended_preferred,
    _format_nominal_freq,
    _iec_e3_round,
    _infer_band_fraction,
    _nominal_freq_for_band,
    nominal_frequencies,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray

# --- nominal_frequencies ---


@pytest.mark.parametrize("fraction", [0, -1, float("nan")])
def test_nominal_frequencies_rejects_non_positive_fraction(fraction: float) -> None:
    """Zero used to divide by zero, NaN to die in index rounding, and a
    negative fraction never terminated (the band centres underflow to 0.0).
    """
    with pytest.raises(ValueError, match="'fraction' must be positive"):
        nominal_frequencies(fraction)


# --- _iec_e3_round ---


def test_iec_e3_round_msd_1_to_4() -> None:
    assert _iec_e3_round(1234.5) == pytest.approx(1230.0)
    assert _iec_e3_round(456.7) == pytest.approx(457.0)


def test_iec_e3_round_msd_5_to_9() -> None:
    assert _iec_e3_round(5678.0) == pytest.approx(5700.0)
    assert _iec_e3_round(99.1) == pytest.approx(99.0)


def test_iec_e3_round_nonpositive() -> None:
    assert _iec_e3_round(0) == 0
    assert _iec_e3_round(-1) == -1


# --- _nominal_freq_for_band ---


def test_nominal_freq_fraction1() -> None:
    assert _nominal_freq_for_band(15.849, 1) == pytest.approx(16.0)
    assert _nominal_freq_for_band(997.2, 1) == pytest.approx(1000.0)


def test_nominal_freq_fraction3() -> None:
    assert _nominal_freq_for_band(12.589, 3) == pytest.approx(12.5)
    assert _nominal_freq_for_band(1995.3, 3) == pytest.approx(2000.0)


@pytest.mark.parametrize("fraction", [1, 3])
def test_extended_table_holds_the_printed_numbers(fraction: int) -> None:
    # Every nominal value is the double nearest the number the standard prints,
    # in the decades below the base table too: scaling by 0.1 once gave
    # 3.1500000000000004 for the 3.15 Hz band.
    for value in _extended_preferred(fraction):
        assert float(f"{value:.6g}") == value


def test_nominal_freq_below_the_base_table() -> None:
    assert _nominal_freq_for_band(3.162, 3) == 3.15
    assert _nominal_freq_for_band(6.310, 3) == 6.3


def test_nominal_freq_other_fraction() -> None:
    assert _nominal_freq_for_band(706.0, 2) == pytest.approx(710.0)


# --- _format_nominal_freq ---


def test_format_below_1k() -> None:
    assert _format_nominal_freq(31.5) == "31.5"
    assert _format_nominal_freq(500.0) == "500"


def test_format_1k_and_above() -> None:
    assert _format_nominal_freq(1000.0) == "1k"
    assert _format_nominal_freq(16000.0) == "16k"
    assert _format_nominal_freq(1250.0) == "1.25k"


# --- nominal_frequencies: the band-set record ---


def test_nominal_frequencies_returns_labels() -> None:
    bands = nominal_frequencies(fraction=3)
    assert isinstance(bands, filters.FractionalOctaveBands)
    assert isinstance(bands.labels, tuple)
    assert all(isinstance(label, str) for label in bands.labels)
    assert len(bands.labels) == bands.frequencies.size
    assert "1k" in bands.labels
    assert "31.5" in bands.labels


def test_nominal_frequencies_fraction1_labels() -> None:
    bands = nominal_frequencies(fraction=1)
    assert "1k" in bands.labels
    assert len(bands.labels) == bands.frequencies.size


def test_the_band_set_is_a_record_and_not_a_tuple() -> None:
    """Four columns by name: no positional unpacking, no writable array."""
    bands = nominal_frequencies(1, [125, 4000])
    with pytest.raises(TypeError, match="cannot unpack non-iterable"):
        _centres, _lower, _upper, _labels = bands  # type: ignore[misc]
    for column in (bands.frequencies, bands.lower_edges, bands.upper_edges):
        assert column.dtype == np.float64
        assert not column.flags.writeable
    assert bands.labels == ("125", "250", "500", "1k", "2k", "4k")
    # IEC 61260-1:2014 5.4: the edges sit G^(1/2b) either side of the centre.
    edge = 10.0 ** (3.0 / 20.0)
    assert bands.lower_edges == pytest.approx(bands.frequencies / edge)
    assert bands.upper_edges == pytest.approx(bands.frequencies * edge)


def test_the_band_set_refuses_columns_that_disagree() -> None:
    """One entry per band in every column, and edges that enclose the centre."""
    centres = [500.0, 1000.0]
    lower = [354.8, 707.9]
    upper = [707.9, 1412.5]
    with pytest.raises(ValueError, match="one entry per band in every column"):
        filters.FractionalOctaveBands(centres, lower, upper, ("500",))
    with pytest.raises(ValueError, match="edges must enclose its centre"):
        filters.FractionalOctaveBands(centres, upper, lower, ("500", "1k"))


def test_the_band_set_refuses_one_string_for_its_labels() -> None:
    """A two-character string is not two labels, even beside two bands."""
    centres = [1000.0, 2000.0]
    lower = [707.9, 1412.5]
    upper = [1412.5, 2818.4]
    with pytest.raises(TypeError, match="'labels' must hold one label per band"):
        filters.FractionalOctaveBands(centres, lower, upper, "1k")  # type: ignore[arg-type]
    # A bytearray is one text too, not one label per character code.
    with pytest.raises(TypeError, match="'labels' must hold one label per band"):
        filters.FractionalOctaveBands(centres, lower, upper, bytearray(b"1k"))  # type: ignore[arg-type]


# --- OctaveFilterBank band-set attributes ---


def test_filterbank_band_set_attributes() -> None:
    fb = filters.OctaveFilterBank(fs=48000, fraction=1)
    assert not hasattr(fb, "nominal_freq")
    assert not hasattr(fb, "freq")
    assert not hasattr(fb, "bands")
    assert isinstance(fb.labels, tuple)
    assert all(isinstance(label, str) for label in fb.labels)
    assert "1k" in fb.labels
    assert len(fb.labels) == fb.n_bands
    assert fb.frequencies.size == fb.lower_edges.size == fb.upper_edges.size
    assert not fb.frequencies.flags.writeable
    replacement = np.ones(fb.n_bands)
    with pytest.raises(AttributeError, match="frequencies"):
        fb.frequencies = replacement  # type: ignore[misc]


# --- filter(nominal=False) — default exact floats ---


def test_filter_nominal_false_returns_floats() -> None:
    fb = filters.OctaveFilterBank(fs=48000, fraction=3)
    x = np.zeros(4800)
    freq = fb.filter(x, nominal=False).frequencies
    assert all(isinstance(f, float) for f in freq)


# --- filter(nominal=True) — nominal string labels ---


def test_filter_nominal_true_returns_strings() -> None:
    fb = filters.OctaveFilterBank(fs=48000, fraction=3)
    x = np.zeros(4800)
    freq = fb.filter(x, nominal=True).frequencies
    assert all(isinstance(f, str) for f in freq)
    assert "1k" in freq


def test_filter_nominal_true_with_sigbands() -> None:
    fb = filters.OctaveFilterBank(fs=48000, fraction=1)
    x = np.zeros(4800)
    filtered = fb.filter(x, sigbands=True, nominal=True)
    freq, xb = filtered.frequencies, filtered.bands
    assert all(isinstance(f, str) for f in freq)
    assert len(xb) == len(freq)


# --- octave_filter(nominal=True) ---


def test_octavefilter_nominal_true() -> None:
    x = np.zeros(4800)
    freq = filters.octave_filter(x, fs=48000, fraction=3, nominal=True).frequencies
    assert all(isinstance(f, str) for f in freq)
    assert "1k" in freq


def test_octavefilter_nominal_false_default() -> None:
    x = np.zeros(4800)
    freq = filters.octave_filter(x, fs=48000, fraction=3).frequencies
    assert all(isinstance(f, float) for f in freq)


def test_normalizedfreq_fraction1_and_invalid_fraction() -> None:
    freq = filters.normalized_frequencies(1)
    assert 1000 in freq

    with pytest.raises(
        ValueError, match="Normalized frequencies only available for fraction"
    ):
        filters.normalized_frequencies(5)


def test_annex_e34_worked_rounding_examples() -> None:
    """IEC 61260-1:2014 E.3.4: 41,567 -> 41,6 (MSD 4, three significant
    figures) and 8 785,2 -> 8 800 (MSD 8, two significant figures).
    """
    from reference_data import IEC61260_E34_EXAMPLES

    from phonometry.filters.frequencies import _iec_e3_round

    for raw, printed in IEC61260_E34_EXAMPLES:
        assert _iec_e3_round(raw) == printed


def test_infer_band_fraction_octave_third_and_single() -> None:
    """Octave centres classify as fraction 1, one-third-octave as 3.

    A single band cannot be told apart from its neighbours' ratio, so the
    helper returns the conventional octave default (1).
    """
    octave = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
    third = np.array([100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0])
    assert _infer_band_fraction(octave) == 1
    assert _infer_band_fraction(third) == 3
    # A wide octave set (>6 bands) is still octave, not one-third-octave.
    assert (
        _infer_band_fraction(
            np.array([16.0, 31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0])
        )
        == 1
    )
    assert _infer_band_fraction(np.array([500.0])) == 1


@pytest.mark.parametrize(
    "limits",
    [np.array([100.0, 4000.0]), np.array([100, 4000]), (100.0, 4000.0)],
    ids=["float array", "integer array", "tuple"],
)
def test_a_pair_of_limits_may_be_an_array_or_a_tuple(
    limits: Sequence[float] | NDArray[Any],
) -> None:
    """A pair read by index is the same pair as an array, a tuple or a list."""
    expected = filters.nominal_frequencies(1, [100.0, 4000.0]).frequencies
    np.testing.assert_array_equal(
        filters.nominal_frequencies(1, limits).frequencies, expected
    )
    bank = filters.OctaveFilterBank(48000, fraction=1, limits=limits)
    assert bank.limits == [100.0, 4000.0]
    signal = np.random.default_rng(0).standard_normal(4800)
    listed = filters.octave_filter(signal, 48000, fraction=1, limits=[100.0, 4000.0])
    paired = filters.octave_filter(signal, 48000, fraction=1, limits=limits)
    np.testing.assert_array_equal(paired.frequencies, listed.frequencies)
