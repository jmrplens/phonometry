#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The records that replaced unpacked tuples draw the arrays they hold.

Each of these answers used to come back as a ``(frequencies, values)`` pair;
as a record it plots itself, and the curve on the axes has to be the record's
own data, in the order it holds it, under the labels of the language asked
for.
"""

from __future__ import annotations

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

import phonometry as ph
from phonometry.environment.sources import cnossos_rail


@pytest.fixture(autouse=True)
def _close_figures() -> None:
    yield
    plt.close("all")


def test_the_coherence_draws_every_bin_above_0_hz_on_0_to_1() -> None:
    t = np.arange(4096)
    x = np.sin(t / 3.0)
    result = ph.electroacoustics.coherence(x, x + np.cos(t / 7.0), fs=1000.0)
    ax = result.plot()
    (line,) = ax.lines
    above = result.frequencies > 0.0
    np.testing.assert_array_equal(line.get_xdata(), result.frequencies[above])
    np.testing.assert_array_equal(line.get_ydata(), result.coherence[above])
    assert ax.get_ylim() == (0.0, 1.05)
    assert ax.get_title() == "Ordinary coherence"
    assert result.plot(language="es").get_title() == "Coherencia ordinaria"


def test_one_spectrum_of_octave_levels_is_one_bar_per_octave() -> None:
    result = ph.emission.octave_band_levels(
        [60.0, 62.0, 61.0, 50.0, 52.0, 51.0], frequencies=[50, 63, 80, 100, 125, 160]
    )
    ax = result.plot()
    heights = [patch.get_height() for patch in ax.patches]
    np.testing.assert_allclose(heights, result.levels)
    labels = [tick.get_text() for tick in ax.get_xticklabels()]
    assert labels == ["63", "125"]
    assert ax.get_ylabel() == "Octave-band level [dB]"
    es = result.plot(language="es")
    assert es.get_ylabel() == "Nivel en banda de octava [dB]"


def test_several_spectra_of_octave_levels_are_one_numbered_line_each() -> None:
    thirds = np.array([[60.0, 62.0, 61.0], [50.0, 52.0, 51.0]])
    result = ph.emission.octave_band_levels(thirds, frequencies=[50, 63, 80])
    ax = result.plot(language="es")
    assert [line.get_ydata()[0] for line in ax.lines] == pytest.approx(
        result.levels[:, 0]
    )
    legend = [text.get_text() for text in ax.get_legend().get_texts()]
    assert legend == ["Espectro 1", "Espectro 2"]


def test_a_wavelength_spectrum_runs_from_the_longest_wavelength() -> None:
    result = cnossos_rail.wheel_roughness("c")
    ax = result.plot()
    (line,) = ax.lines
    np.testing.assert_array_equal(line.get_xdata(), result.wavelengths_mm)
    np.testing.assert_array_equal(line.get_ydata(), result.levels)
    left, right = ax.get_xlim()
    assert left == result.wavelengths_mm.max()
    assert right == result.wavelengths_mm.min()
    assert ax.get_xscale() == "log"
    assert ax.get_xlabel() == r"Wavelength $\lambda$ [mm]"
    es = result.plot(language="es")
    assert es.get_xlabel() == r"Longitud de onda $\lambda$ [mm]"


def test_a_band_with_no_absorption_sample_is_marked_inside_the_axes() -> None:
    freqs = np.linspace(400.0, 1200.0, 200)
    result = ph.materials.surfaces.one_third_octave_absorption(
        np.linspace(0.1, 0.9, 200), frequencies=freqs, f_max=1600.0
    )
    assert np.isnan(result.absorption[-1])
    ax = result.plot()
    measured = np.isfinite(result.absorption)
    heights = [patch.get_height() for patch in ax.patches]
    np.testing.assert_allclose(heights, result.absorption[measured])
    # The band axis puts band i at x = i: every empty band is marked at its
    # own position, the empty bands at both ends inside the limits.
    empty = np.flatnonzero(~measured)
    assert empty[0] == 0
    assert empty[-1] == result.frequencies.size - 1
    assert [text.get_position()[0] for text in ax.texts] == empty.tolist()
    left, right = ax.get_xlim()
    assert left < empty[0]
    assert right > empty[-1]
    assert ax.get_title() == "Road-surface absorption in one-third-octave bands"


def test_a_contour_is_titled_with_its_phon_and_the_threshold_as_the_threshold() -> None:
    contour = ph.psychoacoustics.equal_loudness_contour(40.0)
    ax = contour.plot()
    (line,) = ax.lines
    np.testing.assert_array_equal(line.get_xdata(), contour.frequencies)
    np.testing.assert_array_equal(line.get_ydata(), contour.levels)
    assert contour.phon == 40.0
    assert ax.get_title() == "ISO 226:2023 equal-loudness contour, 40 phon"
    assert (
        contour.plot(language="es").get_title()
        == "Curva isofónica ISO 226:2023, 40 fonios"
    )
    threshold = ph.psychoacoustics.hearing_threshold()
    assert threshold.phon is None
    tax = threshold.plot()
    assert tax.get_title() == r"ISO 226:2023 threshold of hearing $T_f$"
    assert tax.lines[0].get_linestyle() == "--"


def test_the_energy_spectral_density_is_drawn_re_its_highest_bin() -> None:
    result = ph.vibration.energy_spectral_density(
        np.exp(-np.arange(128) / 8.0), fs=1000.0
    )
    ax = result.plot()
    (line,) = ax.lines
    expected = 10.0 * np.log10(result.density / result.density.max())
    np.testing.assert_allclose(line.get_ydata(), expected)
    assert np.nanmax(line.get_ydata()) == 0.0
    es = result.plot(language="es")
    assert es.get_ylabel() == "Densidad espectral de energía $G$ [dB re máximo]"
