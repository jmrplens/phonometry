#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The class check grades a decimated band at the bank's input rate.

A band the bank decimates by M filters its input, keeps one sample in M and
runs its sections at fs / M, so every input frequency k fs / M +/- f comes
out at f: the band reads alias images of itself across the whole input band.
IEC 61260-1:2014 5.15 and IEC 61260:1995 4.8 ask the anti-aliasing filters
to keep those images from taking the relative attenuation past Table 1, and
Table 1 covers every frequency, so :func:`verify_filter_class` grades the
response the band has at the input rate, up to half of it. These tests hold
the check to what tones run through the running bank read, show it failing a
bank whose decimator lets the images through, and hold the library's banks
to the class they declare once the images are graded.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import signal

from phonometry import filters
from phonometry.filters import compliance
from phonometry.filters.compliance import _band_relative_attenuation, _BandGrid
from phonometry.filters.core import _decimate_and_filter, _multirate_lowpass


def _kaiser_5_lowpass(factor: int) -> np.ndarray:
    """The anti-aliasing filter ``scipy.signal.resample_poly`` designs by default."""
    return np.asarray(
        signal.firwin(2 * 10 * factor + 1, 1.0 / factor, window=("kaiser", 5.0))
    )


def _tone_attenuation_db(
    bank: filters.OctaveFilterBank, index: int, frequency_hz: float
) -> float:
    """The relative attenuation a tone reads through one band of the running bank.

    The tone runs through the bank's own decimation and sections; the mean
    square of the settled second half of its output is compared with that of
    a tone at the exact mid-band frequency.
    """
    fs = int(bank.fs)
    t = np.arange(8 * fs) / fs
    factor = int(bank.factor[index])

    def mean_square(f: float) -> float:
        y = _decimate_and_filter(
            np.cos(2.0 * np.pi * f * t + 0.3), bank.sos[index], factor
        )
        return float(np.mean(y[y.size // 2 :] ** 2))

    return 10.0 * math.log10(
        mean_square(float(bank.freq[index])) / mean_square(frequency_hz)
    )


def test_the_graded_images_are_what_tones_through_the_bank_read() -> None:
    """At the images k fs/M +/- f_m the check reads what the running bank delivers.

    The 63 Hz band of the 16 kHz octave bank is decimated by 5: tones at the
    first two images of its mid-band frequency and of the frequency 3 kHz
    above, run through the bank, read the relative attenuation the check
    grades, to a hundredth of a decibel, more than 120 dB down.
    """
    bank = filters.OctaveFilterBank(16000, fraction=1)
    index = int(np.argmin(np.abs(np.asarray(bank.freq) - 63.0)))
    factor = int(bank.factor[index])
    assert factor == 5
    rate = bank.fs / factor
    mid = float(bank.freq[index])
    tones = np.array([rate - mid, rate + mid, 2.0 * rate - mid])
    graded = _band_relative_attenuation(
        bank.sos[index], factor, float(bank.fs), mid, tones
    )
    measured = [_tone_attenuation_db(bank, index, float(f)) for f in tones]
    np.testing.assert_allclose(measured, graded, atol=0.01)
    assert float(np.min(graded)) > 120.0


def test_every_image_the_verdict_reads_is_what_a_tone_reads() -> None:
    """The images the verdict grades, the second ones included, match tones.

    The verdict reads the images through a zoom transform of the shifted
    anti-aliasing taps, one per image and side. The 63 Hz band of the 16 kHz
    octave bank is decimated by 5, so it has two images on either side below
    8 kHz. At the grid point nearest its mid-band frequency, each of the four
    reads what a tone run through the bank delivers, to a hundredth of a
    decibel.
    """
    bank = filters.OctaveFilterBank(16000, fraction=1)
    index = int(np.argmin(np.abs(np.asarray(bank.freq) - 63.0)))
    factor = int(bank.factor[index])
    assert factor == 5
    grid = _BandGrid(
        np.asarray(bank.sos[index]),
        factor,
        float(bank.fs),
        float(bank.freq[index]),
        2**8,
    )
    offset = round(float(bank.freq[index]) / grid.spacing_hz) * grid.spacing_hz
    read = {
        round(float(f), 6): float(d)
        for freqs, delta_a in grid.images(0, grid.num_points)
        for f, d in zip(freqs, delta_a, strict=True)
    }
    tones = [k * grid.rate_hz + sign * offset for k in (1, 2) for sign in (-1.0, 1.0)]
    graded = [read[round(f, 6)] for f in tones]
    measured = [_tone_attenuation_db(bank, index, f) for f in tones]
    np.testing.assert_allclose(measured, graded, atol=0.01)
    assert min(graded) > 120.0


def test_a_decimated_band_is_graded_up_to_half_the_input_rate() -> None:
    """``checked_to_omega`` is fs / 2 over f_m for every band, decimated or not."""
    bank = filters.OctaveFilterBank(48000, fraction=3, limits=[100, 10000])
    assert max(bank.factor) > 1
    result = filters.verify_filter_class(bank)
    reach = [b["checked_to_omega"] * b["freq"] for b in result.bands]
    np.testing.assert_allclose(reach, 24000.0, rtol=1e-12)


@pytest.mark.parametrize("fs", [8000, 16000, 32000])
def test_the_check_fails_a_bank_whose_decimator_lets_images_through(
    monkeypatch: pytest.MonkeyPatch, fs: int
) -> None:
    """With scipy's default decimator the octave bank is not class 1 at these rates.

    Its Kaiser window (beta 5) leaves the first image of each decimated band
    68.9 dB down, under the 70 dB Table 1 of IEC 61260-1:2014 asks of class 1
    at and beyond G**4. A check that stopped at the decimated Nyquist
    frequency read the same bank as class 1.
    """
    bank = filters.OctaveFilterBank(fs, fraction=1)
    monkeypatch.setattr(compliance, "_multirate_lowpass", _kaiser_5_lowpass)
    result = filters.verify_filter_class(bank, num_points=2**12)
    assert result.requirement_class("relative_attenuation") == 2
    worst = min(result.bands, key=lambda b: b["margin_class1_db"])
    assert worst["margin_class1_db"] == pytest.approx(68.9 - 70.0, abs=0.05)
    assert int(bank.factor[result.bands.index(worst)]) > 1


@pytest.mark.parametrize("fs", [8000, 16000, 22050, 32000, 44100, 48000, 96000])
@pytest.mark.parametrize("fraction", [1, 3])
def test_the_default_banks_are_the_class_they_declare(fs: int, fraction: int) -> None:
    """Images graded, the default banks are class 1 of 2014 and class 0 of 1995."""
    bank = filters.OctaveFilterBank(fs, fraction=fraction)
    assert filters.verify_filter_class(bank, num_points=2**12).overall_class == 1
    assert (
        filters.verify_filter_class(
            bank, edition="1995", num_points=2**12
        ).overall_class
        == 0
    )


@pytest.mark.parametrize("fs", [8000, 44100, 48000])
@pytest.mark.parametrize("fraction", [1, 3])
def test_the_bank_keeps_every_image_more_than_125_db_down(
    fs: int, fraction: int
) -> None:
    """The anti-aliasing filter of the bank leaves no image within 125 dB."""
    bank = filters.OctaveFilterBank(fs, fraction=fraction)
    worst = math.inf
    for index in range(bank.num_bands):
        factor = int(bank.factor[index])
        if factor == 1:
            continue
        grid = _BandGrid(
            np.asarray(bank.sos[index]),
            factor,
            float(bank.fs),
            float(bank.freq[index]),
            2**12,
        )
        for _, delta_a in grid.images(0, grid.num_points):
            if delta_a.size:
                worst = min(worst, float(np.min(delta_a)))
    assert worst > 125.0


@pytest.mark.parametrize("decimator", [_multirate_lowpass, _kaiser_5_lowpass])
def test_the_images_read_are_all_that_can_bind(
    monkeypatch: pytest.MonkeyPatch, decimator: object
) -> None:
    """Skipping the images that cannot bind leaves every margin as the full grid has it."""
    bank = filters.OctaveFilterBank(48000, fraction=3, limits=[12, 1000])
    monkeypatch.setattr(compliance, "_multirate_lowpass", decimator)
    pruned = filters.verify_filter_class(bank, edition="1995", num_points=2**11)
    monkeypatch.setattr(
        compliance,
        "_image_window",
        lambda grid, *_: (0, grid.num_points) if grid.factor > 1 else (0, -1),
    )
    full = filters.verify_filter_class(bank, edition="1995", num_points=2**11)
    for a, b in zip(pruned.bands, full.bands, strict=True):
        for cls in (0, 1, 2):
            key = f"margin_class{cls}_db"
            assert a[key] == pytest.approx(b[key], abs=1e-6)


def test_the_bank_decimates_and_interpolates_through_the_graded_filter() -> None:
    """The band signals come back to the input rate through the same filter.

    The anti-aliasing filter has unit gain at DC, and a tone at the mid-band
    frequency of a decimated band reads, interpolated back to the input rate,
    the mean square it has at the decimated rate, to a thousandth of a
    decibel.
    """
    bank = filters.OctaveFilterBank(16000, fraction=1, limits=[50, 200])
    index = 0
    factor = int(bank.factor[index])
    assert factor > 1
    assert float(np.sum(_multirate_lowpass(factor))) == pytest.approx(1.0, abs=1e-12)
    t = np.arange(8 * bank.fs) / bank.fs
    tone = np.cos(2.0 * np.pi * float(bank.freq[index]) * t)
    out = bank.filter(tone, sigbands=True, calculate_level=False, detrend=False)
    band = np.asarray(out.require_bands()[index])
    decimated = _decimate_and_filter(tone, bank.sos[index], factor)

    def settled_db(y: np.ndarray) -> float:
        return 10.0 * math.log10(float(np.mean(y[y.size // 4 : -y.size // 4] ** 2)))

    assert settled_db(band) == pytest.approx(settled_db(decimated), abs=1e-3)
