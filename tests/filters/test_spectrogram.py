#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for OctaveFilterBank.spectrogram() short-time band levels."""

import numpy as np
import pytest

from phonometry import filters

FS = 48000


def test_spectrogram_shapes_and_times() -> None:
    """Output shapes follow (bands, frames) and times are window centers."""
    bank = filters.OctaveFilterBank(fs=FS, fraction=1, limits=[100, 5000])
    x = np.random.default_rng(0).standard_normal(FS * 2)
    result = bank.spectrogram(x, window_time=0.25, overlap=0.5)

    hop = 0.25 * 0.5
    expected_frames = int((2.0 - 0.25) / hop) + 1
    assert isinstance(result, filters.OctaveSpectrogramResult)
    assert result.levels.shape == (bank.n_bands, expected_frames)
    assert result.frequencies.shape == (bank.n_bands,)
    assert result.frequencies.dtype == np.float64
    assert not result.frequencies.flags.writeable
    assert result.frequencies == pytest.approx(bank.frequencies)
    assert result.times.shape == (expected_frames,)
    np.testing.assert_allclose(result.times[1] - result.times[0], hop, rtol=1e-6)


def test_spectrogram_detects_level_step() -> None:
    """A tone whose amplitude doubles mid-signal shows a ~6 dB step in its band."""
    bank = filters.OctaveFilterBank(fs=FS, fraction=1, limits=[800, 1200])
    t = np.arange(FS * 2) / FS
    amp = np.where(t < 1.0, 0.5, 1.0)
    x = amp * np.sin(2 * np.pi * 1000 * t)
    result = bank.spectrogram(x, window_time=0.125, overlap=0.0)

    band = int(np.argmin(np.abs(result.frequencies - 1000)))
    first_half = result.levels[band, result.times < 0.9].mean()
    second_half = result.levels[band, result.times > 1.1].mean()
    assert second_half - first_half == pytest.approx(6.02, abs=0.3)


def test_spectrogram_multichannel() -> None:
    bank = filters.OctaveFilterBank(fs=FS, fraction=1, limits=[100, 5000])
    x = np.random.default_rng(1).standard_normal((3, FS))
    result = bank.spectrogram(x, window_time=0.125, overlap=0.5)
    assert result.levels.ndim == 3
    assert result.levels.shape[0] == 3
    assert result.levels.shape[1] == bank.n_bands
    assert result.levels.shape[2] == result.times.shape[0]


def test_spectrogram_rejects_stateful() -> None:
    bank = filters.OctaveFilterBank(
        fs=FS,
        design=filters.FilterDesign(resample=False),
        block_processing=filters.BlockProcessing(stateful=True),
    )
    silence = np.zeros(FS)
    with pytest.raises(
        ValueError, match=r"spectrogram\(\) is not supported on stateful banks"
    ):
        bank.spectrogram(silence)


def test_spectrogram_invalid_params_raise() -> None:
    bank = filters.OctaveFilterBank(fs=FS, fraction=1, limits=[100, 5000])
    # the signals are built outside the raises blocks, so each block holds
    # exactly the one call whose exception is under test
    one_second = np.zeros(FS)
    shorter_than_the_window = np.zeros(1000)
    with pytest.raises(ValueError, match=r"overlap must be in \[0, 1\)"):
        bank.spectrogram(one_second, overlap=1.0)
    with pytest.raises(
        ValueError, match=r"window_time must be positive and shorter than the signal"
    ):
        bank.spectrogram(shorter_than_the_window, window_time=1.0)


@pytest.mark.parametrize("window_time", [float("nan"), float("inf"), -1.0, 0.0])
def test_spectrogram_rejects_non_positive_window_time(window_time: float) -> None:
    """A non-finite window length used to die in round(), naming nothing."""
    bank = filters.OctaveFilterBank(fs=FS, fraction=1, limits=[100, 5000])
    one_second = np.zeros(FS)
    with pytest.raises(ValueError, match="'window_time' must be positive"):
        bank.spectrogram(one_second, window_time=window_time)


def test_spectrogram_rejects_non_string_mode() -> None:
    """A non-string mode used to die in str.lower, deep in level calculation."""
    bank = filters.OctaveFilterBank(fs=FS, fraction=1, limits=[100, 5000])
    one_second = np.zeros(FS)
    with pytest.raises(TypeError, match="'mode' must be a string"):
        bank.spectrogram(one_second, mode=None)  # type: ignore[arg-type]


def test_spectrogram_rejects_unknown_mode() -> None:
    bank = filters.OctaveFilterBank(fs=FS, fraction=1, limits=[100, 5000])
    one_second = np.zeros(FS)
    with pytest.raises(ValueError, match="'mode' must be one of"):
        bank.spectrogram(one_second, mode="bogus")


def test_spectrogram_rejects_three_dimensional_input() -> None:
    """A 3-D array used to reach numpy's sliding window before any refusal."""
    bank = filters.OctaveFilterBank(fs=FS, fraction=1, limits=[100, 5000])
    cube = np.zeros((2, 2, FS))
    with pytest.raises(ValueError, match="'x' must be a 1-D signal or a 2-D"):
        bank.spectrogram(cube)


def test_the_spectrogram_is_a_record_and_not_a_tuple() -> None:
    """``levels, freq, times = bank.spectrogram(x)`` is gone: read by name."""
    bank = filters.OctaveFilterBank(fs=FS, fraction=1, limits=[100, 5000])
    result = bank.spectrogram(np.random.default_rng(5).standard_normal(FS))
    with pytest.raises(TypeError, match="cannot unpack non-iterable"):
        _levels, _frequencies, _times = result  # type: ignore[misc]
    assert not result.levels.flags.writeable
    assert not result.times.flags.writeable


def test_the_spectrogram_record_pins_its_grid_to_both_axes() -> None:
    """A level grid one band or one frame off its axes is refused, not stretched."""
    grid = np.zeros((3, 4))
    centres = np.array([250.0, 500.0, 1000.0])
    lower, upper = centres / np.sqrt(2.0), centres * np.sqrt(2.0)
    times = np.array([0.0625, 0.125, 0.1875, 0.25])
    flat = np.zeros(3)
    square_times = times.reshape(2, 2)
    with pytest.raises(ValueError, match="holds 3 bands and 'frequencies' 2"):
        filters.OctaveSpectrogramResult(grid, centres[:2], times, lower, upper)
    with pytest.raises(ValueError, match="holds 4 frames and 'times' 3"):
        filters.OctaveSpectrogramResult(grid, centres, times[:3], lower, upper)
    with pytest.raises(ValueError, match=r"'levels' must be \(bands, frames\)"):
        filters.OctaveSpectrogramResult(flat, centres, times, lower, upper)
    with pytest.raises(ValueError, match="'times' must be one-dimensional"):
        filters.OctaveSpectrogramResult(grid, centres, square_times, lower, upper)
    with pytest.raises(ValueError, match="holds 3 bands and 'lower_edges' 2"):
        filters.OctaveSpectrogramResult(grid, centres, times, lower[:2], upper)
    with pytest.raises(ValueError, match="holds 3 bands and 'upper_edges' 4"):
        filters.OctaveSpectrogramResult(grid, centres, times, lower, np.ones(4))


@pytest.mark.parametrize("field", ["lower_edges", "upper_edges"])
def test_the_spectrogram_record_requires_the_band_edges(field: str) -> None:
    """The plot draws each band between its edges, so the record holds them."""
    import dataclasses

    bank = filters.OctaveFilterBank(fs=FS, fraction=1, limits=[100, 5000])
    result = bank.spectrogram(np.zeros(FS))
    with pytest.raises(TypeError, match=f"'{field}' is required"):
        dataclasses.replace(result, **{field: None})


def test_the_spectrogram_carries_the_edges_of_its_bank() -> None:
    bank = filters.OctaveFilterBank(fs=FS, fraction=3, limits=[250, 4000])
    result = bank.spectrogram(np.zeros(FS // 2), window_time=0.125)
    np.testing.assert_array_equal(result.lower_edges, bank.lower_edges)
    np.testing.assert_array_equal(result.upper_edges, bank.upper_edges)
    assert not result.lower_edges.flags.writeable
    assert not result.upper_edges.flags.writeable


def test_a_one_band_spectrogram_is_drawn_between_its_own_edges() -> None:
    """A single third-octave band is not drawn one octave tall.

    The centres alone carry no band width when there is one of them, and the
    plot fell back on an octave, painting colour from 707 Hz to 1.41 kHz over
    a band measured from 891 Hz to 1.12 kHz.
    """
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    bank = filters.OctaveFilterBank(fs=FS, fraction=3, limits=[990, 1010])
    signal = np.random.default_rng(7).standard_normal(FS // 2)
    result = bank.spectrogram(signal, window_time=0.125)
    assert result.frequencies.size == 1
    ax = result.plot()
    _, _, bottom, top = ax.images[0].get_extent()
    assert 10.0**bottom == pytest.approx(bank.lower_edges[0])
    assert 10.0**top == pytest.approx(bank.upper_edges[0])
    assert ax.get_ylim() == pytest.approx((891.25, 1122.02), abs=0.01)
    plt.close("all")


def _third_octave_spectrogram(channels: int = 1) -> filters.OctaveSpectrogramResult:
    bank = filters.OctaveFilterBank(fs=FS, fraction=3, limits=[250, 4000])
    rng = np.random.default_rng(6)
    shape = (channels, FS // 2) if channels > 1 else (FS // 2,)
    x = rng.standard_normal(shape)
    return bank.spectrogram(x, window_time=0.125, overlap=0.5)


def test_the_spectrogram_plot_places_the_raster_on_the_band_edges() -> None:
    """One imshow image, rows from the first lower edge to the last upper edge.

    The centres are a geometric series, so the raster is laid out in log10 of
    the frequency, one band per row from the bank's first lower edge to its
    last upper edge, and carried onto the logarithmic axis through 10**y; the
    columns are one hop wide, centred on the window times.
    """
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    result = _third_octave_spectrogram()
    edges = filters.nominal_frequencies(3, [250, 4000])
    ax = result.plot()
    assert len(ax.images) == 1
    assert not ax.collections  # no pcolormesh quads
    left, right, bottom, top = ax.images[0].get_extent()
    hop = float(result.times[1] - result.times[0])
    assert left == pytest.approx(result.times[0] - hop / 2)
    assert right == pytest.approx(result.times[-1] + hop / 2)
    assert 10.0**bottom == pytest.approx(edges.lower_edges[0])
    assert 10.0**top == pytest.approx(edges.upper_edges[-1])
    assert ax.get_yscale() == "log"
    assert ax.get_xlabel() == "Time [s]"
    assert ax.get_ylabel() == "Frequency [Hz]"
    assert ax.get_title() == "Band levels over time"
    colourbar = ax.figure.axes[-1]
    assert colourbar.get_ylabel() == "Band level [dB]"
    assert "1k" in [label.get_text() for label in ax.get_yticklabels()]
    plt.close("all")


def test_the_spectrogram_plot_speaks_spanish() -> None:
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    ax = _third_octave_spectrogram().plot(language="es")
    assert ax.get_xlabel() == "Tiempo [s]"
    assert ax.get_ylabel() == "Frecuencia [Hz]"
    assert ax.get_title() == "Niveles de banda en el tiempo"
    assert ax.figure.axes[-1].get_ylabel() == "Nivel de banda [dB]"
    labels = [label.get_text() for label in ax.get_yticklabels()]
    assert labels[:5] == ["250", "500", "1k", "2k", "4k"]
    plt.close("all")


def test_a_multichannel_spectrogram_draws_the_channel_it_is_asked_for() -> None:
    """Two channels cannot share one raster: the plot asks which one."""
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    result = _third_octave_spectrogram(channels=2)
    with pytest.raises(ValueError, match="holds 2 channels; pass channel="):
        result.plot()
    with pytest.raises(ValueError, match="channel=2 is not one of"):
        result.plot(channel=2)
    ax = result.plot(channel=1)
    drawn = np.asarray(ax.images[0].get_array())
    assert drawn == pytest.approx(result.levels[1])
    assert ax.get_title() == "Band levels over time, channel 2"
    plt.close("all")


def test_each_row_of_the_spectrogram_lands_on_its_own_band() -> None:
    """A row sits on its band centre, not where an even spread in hertz puts it.

    An image is laid out evenly in its own coordinates, so a raster whose rows
    are evenly spaced in log frequency, placed straight on a logarithmic axis,
    is spread evenly in hertz: a 250 Hz tone in a 1/12-octave spectrogram from
    50 Hz drew near 3.6 kHz. The image's transform must put the centre of
    every row at the display height of that row's centre frequency.
    """
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    bank = filters.OctaveFilterBank(fs=FS, fraction=12, limits=[50, 12000])
    t = np.arange(FS // 2) / FS
    result = bank.spectrogram(np.sin(2 * np.pi * 250 * t), window_time=0.125)
    ax = result.plot()
    image = ax.images[0]
    _, _, bottom, top = image.get_extent()
    rows = result.frequencies.size
    row_height = (top - bottom) / rows
    centres = bottom + (np.arange(rows) + 0.5) * row_height
    x = float(result.times[0])
    drawn = image.get_transform().transform(
        np.column_stack([np.full(rows, x), centres])
    )
    expected = ax.transData.transform(
        np.column_stack([np.full(rows, x), result.frequencies])
    )
    np.testing.assert_allclose(drawn[:, 1], expected[:, 1], atol=1e-6)
    plt.close("all")
