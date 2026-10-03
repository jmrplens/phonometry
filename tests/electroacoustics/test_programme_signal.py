#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 60268-1:1985 Clause 7: the simulated programme signal."""

from __future__ import annotations

import dataclasses
import math
from types import MappingProxyType
from typing import Literal

import numpy as np
import pytest
import reference_data as ref

import phonometry as ph
from phonometry.electroacoustics import programme_signal as ps

ea = ph.electroacoustics

FS = 48000


def _table() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = np.array(ref.IEC60268_1_TABLE_II)
    return rows[:, 0], rows[:, 1], rows[:, 2]


def _figure_2_band_levels() -> np.ndarray:
    """Pink noise through Figure 2 in ideal one-third-octave bands, in dB."""
    frequencies, _, _ = _table()
    exact = 1000.0 * 10.0 ** (np.round(10.0 * np.log10(frequencies / 1000.0)) / 10.0)
    edge = 10.0 ** (1.0 / 20.0)
    levels = []
    for centre in exact:
        f = np.geomspace(centre / edge, centre * edge, 4001)
        power = np.abs(ea.programme_signal_filter(f)) ** 2 / f
        levels.append(10.0 * np.log10(np.trapezoid(power, f) / math.log(edge**2)))
    return np.asarray(levels)


# ---------------------------------------------------------------------------
# Table II
# ---------------------------------------------------------------------------


def test_table_ii_is_transcribed_as_printed() -> None:
    printed = {f: (level, tol) for f, level, tol in ref.IEC60268_1_TABLE_II}
    table = ea.SIMULATED_PROGRAMME_SPECTRUM
    assert list(table) == list(printed)
    for frequency, band in table.items():
        level, tolerance = printed[frequency]
        assert band.relative_level_db == level
        assert band.tolerance_plus_db == tolerance
        assert band.tolerance_minus_db == tolerance


def test_table_ii_is_immutable() -> None:
    table = ea.SIMULATED_PROGRAMME_SPECTRUM
    assert isinstance(table, MappingProxyType)
    band = table[1000.0]
    with pytest.raises(dataclasses.FrozenInstanceError, match="relative_level_db"):
        band.relative_level_db = 0.0


def test_clause_7_note_full_range_is_about_12_5_db_above_one_band() -> None:
    _, levels, _ = _table()
    excess = 10.0 * math.log10(float(np.sum(10.0 ** (levels / 10.0))))
    assert excess == pytest.approx(ref.IEC60268_1_FULL_RANGE_EXCESS_DB, abs=0.1)


# ---------------------------------------------------------------------------
# Figure 2
# ---------------------------------------------------------------------------


def test_figure_2_closed_form_matches_the_nodal_equations() -> None:
    values = dict(ref.IEC60268_1_FIGURE2_OHM_FARAD)
    frequencies = np.geomspace(5.0, 40000.0, 37)
    expected = []
    for f in frequencies:
        s = 2j * math.pi * f
        z1 = values["series source resistor"] + 1 / (s * values["series capacitor"])
        z2 = values["second series resistor"] + 1 / (
            s * values["second series capacitor"]
        )
        z3 = 1 / (s * values["output series capacitor"])
        ya = 1 / values["first shunt resistor"] + s * values["first shunt capacitor"]
        yb = 1 / values["second shunt resistor"] + s * values["second shunt capacitor"]
        yc = 1 / values["output resistor"]
        matrix = np.array(
            [
                [1 / z1 + ya + 1 / z2, -1 / z2, 0],
                [-1 / z2, 1 / z2 + yb + 1 / z3, -1 / z3],
                [0, -1 / z3, 1 / z3 + yc],
            ]
        )
        expected.append(np.linalg.solve(matrix, [1 / z1, 0, 0])[2])
    np.testing.assert_allclose(
        ea.programme_signal_filter(frequencies), expected, rtol=1e-12
    )


def test_figure_2_keeps_its_shape_for_any_array() -> None:
    response = ea.programme_signal_filter(np.full((2, 3), 1000.0))
    assert response.shape == (2, 3)
    assert response.dtype == np.complex128


def test_figure_2_with_pink_noise_lands_inside_table_ii() -> None:
    frequencies, _, _ = _table()
    check = ea.check_programme_signal(frequencies, _figure_2_band_levels())
    assert check.passes
    assert check.margin_db == pytest.approx(0.178, abs=0.002)
    assert 5000.0 in check.binding_bands_hz


def test_figure_2_rejects_a_non_positive_frequency() -> None:
    with pytest.raises(ValueError, match="frequencies_hz"):
        ea.programme_signal_filter([0.0, 100.0])


# ---------------------------------------------------------------------------
# The generator
# ---------------------------------------------------------------------------


def _table_band_levels_by_quadrature() -> np.ndarray:
    r"""The ``"table"`` density integrated numerically over each exact band, in dB.

    Independent of the closed form the nodes are fitted with: the density the
    generator shapes its spectrum by, summed by the trapezoidal rule in
    :math:`\lg f` across each ideal base-ten band and divided by its width.
    """
    levels = []
    for n in range(-17, 14):
        centre = 3.0 + n / 10.0
        u = np.linspace(centre - 0.05, centre + 0.05, 20001)
        power = 10.0 ** (ps._table_density_db(10.0**u) / 10.0)
        levels.append(10.0 * np.log10(np.trapezoid(power, u) / 0.1))
    return np.asarray(levels)


def test_table_density_puts_every_band_on_its_printed_level() -> None:
    _, levels, _ = _table()
    np.testing.assert_allclose(_table_band_levels_by_quadrature(), levels, atol=1e-6)


def test_generator_is_zero_mean_at_the_requested_rms() -> None:
    x = ea.simulated_programme_signal(FS, 2.0, rms=0.25, seed=3)
    assert x.shape == (2 * FS,)
    assert float(np.mean(x)) == pytest.approx(0.0, abs=1e-12)
    assert float(np.sqrt(np.mean(x * x))) == pytest.approx(0.25, rel=1e-12)


def test_generator_is_reproducible_with_a_seed() -> None:
    first = ea.simulated_programme_signal(FS, 0.5, seed=11)
    second = ea.simulated_programme_signal(FS, 0.5, seed=11)
    np.testing.assert_array_equal(first, second)


@pytest.mark.parametrize("spectrum", ["table", "figure_2"])
def test_generator_spectrum_conforms_over_a_long_record(
    spectrum: Literal["table", "figure_2"],
) -> None:
    x = ea.simulated_programme_signal(FS, 120.0, spectrum=spectrum, seed=2)
    bands = ph.filters.octave_filter(x, FS, fraction=3, limits=[19.95, 19952.6])
    check = ea.check_programme_signal(bands.frequencies, np.asarray(bands.levels))
    assert check.passes
    assert check.frequencies_hz.size == 31


def test_table_spectrum_sits_on_the_table() -> None:
    x = ea.simulated_programme_signal(FS, 120.0, seed=4)
    bands = ph.filters.octave_filter(x, FS, fraction=3, limits=[19.95, 19952.6])
    check = ea.check_programme_signal(bands.frequencies, np.asarray(bands.levels))
    # The middle bands are wide enough for 120 s to settle well inside 0,5 dB.
    middle = (check.frequencies_hz >= 250.0) & (check.frequencies_hz <= 8000.0)
    assert np.max(np.abs(check.deviations_db[middle])) < 0.1


def test_generator_is_gaussian_without_clipping() -> None:
    x = ea.simulated_programme_signal(FS, 10.0, seed=5)
    kurtosis = float(np.mean(x**4))
    assert kurtosis == pytest.approx(3.0, abs=0.1)


@pytest.mark.parametrize("ratio", ref.IEC60268_7_LIMITING_PEAK_TO_RMS)
def test_clipping_reaches_the_requested_peak_to_rms(ratio: float) -> None:
    x = ea.simulated_programme_signal(FS, 5.0, rms=2.0, peak_to_rms=ratio, seed=6)
    rms = float(np.sqrt(np.mean(x * x)))
    assert rms == pytest.approx(2.0, rel=1e-12)
    assert float(np.max(np.abs(x))) / rms == pytest.approx(ratio, rel=1e-9)


def test_clipping_beyond_the_unclipped_ratio_is_refused() -> None:
    with pytest.raises(ValueError, match="peak_to_rms"):
        ea.simulated_programme_signal(FS, 1.0, peak_to_rms=20.0, seed=1)


def test_clipping_to_a_ratio_of_one_is_refused() -> None:
    with pytest.raises(ValueError, match="peak_to_rms"):
        ea.simulated_programme_signal(FS, 1.0, peak_to_rms=1.0, seed=1)


def test_an_unknown_spectrum_is_refused() -> None:
    with pytest.raises(ValueError, match="spectrum"):
        ea.simulated_programme_signal(FS, 1.0, spectrum="pink")  # type: ignore[arg-type]


def test_a_record_too_short_is_refused() -> None:
    with pytest.raises(ValueError, match="16 samples"):
        ea.simulated_programme_signal(FS, 1e-4)


# ---------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------


def test_the_table_itself_passes_with_its_whole_tolerance() -> None:
    frequencies, levels, tolerances = _table()
    check = ea.check_programme_signal(frequencies, levels + 73.0)
    assert check.passes
    assert check.offset_db == pytest.approx(-73.0, abs=1e-12)
    assert check.margin_db == pytest.approx(float(np.min(tolerances)), abs=1e-12)


def test_a_band_on_its_limit_passes() -> None:
    frequencies, levels, _ = _table()
    shifted = levels.copy()
    # 20 Hz raised 3,5 dB: the only level that fits is -0,5 dB, which puts it
    # on its +3 dB limit and the 0,5 dB bands of the middle on their -0,5 dB.
    shifted[0] += 3.5
    check = ea.check_programme_signal(frequencies, shifted)
    assert check.offset_db == pytest.approx(-0.5, abs=1e-12)
    assert check.margin_db == pytest.approx(0.0, abs=1e-12)
    assert check.passes


def test_a_band_beyond_its_limit_fails_and_is_named() -> None:
    frequencies, levels, _ = _table()
    shifted = levels.copy()
    shifted[14] += 1.5  # 500 Hz, tolerance 0,5 dB
    check = ea.check_programme_signal(frequencies, shifted)
    assert not check.passes
    assert 500.0 in check.binding_bands_hz
    assert check.margin_db < 0.0


def test_exact_band_centres_are_read_as_nominal() -> None:
    frequencies, levels, _ = _table()
    exact = 1000.0 * 10.0 ** (np.round(10.0 * np.log10(frequencies / 1000.0)) / 10.0)
    check = ea.check_programme_signal(exact, levels)
    np.testing.assert_array_equal(check.frequencies_hz, frequencies)


def test_a_partial_spectrum_is_judged_on_its_bands() -> None:
    frequencies, levels, _ = _table()
    check = ea.check_programme_signal(frequencies[:30], levels[:30])
    assert check.frequencies_hz.size == 30
    assert check.passes


def test_check_results_are_read_only() -> None:
    frequencies, levels, _ = _table()
    check = ea.check_programme_signal(frequencies, levels)
    assert not check.band_levels_db.flags.writeable
    assert not check.frequencies_hz.flags.writeable


def test_check_has_no_truth_value() -> None:
    frequencies, levels, _ = _table()
    check = ea.check_programme_signal(frequencies, levels)
    with pytest.raises(TypeError, match="passes"):
        bool(check)


def test_a_frequency_outside_table_ii_is_refused() -> None:
    with pytest.raises(ValueError, match="Table II"):
        ea.check_programme_signal([20.0, 22000.0], [0.0, 0.0])


def test_a_repeated_band_is_refused() -> None:
    with pytest.raises(ValueError, match="more than once"):
        ea.check_programme_signal([1000.0, 1000.0], [0.0, 0.0])


def test_one_band_is_refused() -> None:
    with pytest.raises(ValueError, match="At least 2 bands"):
        ea.check_programme_signal([1000.0], [0.0])


def test_lengths_must_agree() -> None:
    with pytest.raises(ValueError, match="equal length"):
        ea.check_programme_signal([1000.0, 1250.0], [0.0])


def test_a_level_must_be_finite() -> None:
    with pytest.raises(ValueError, match="band_levels_db"):
        ea.check_programme_signal([1000.0, 1250.0], [0.0, np.nan])


# ---------------------------------------------------------------------------
# What the plots draw
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("language", ["en", "es"])
def test_check_plot_draws_the_bands_referred_by_the_offset(language: str) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    frequencies, levels, tolerances = _table()
    shifted = levels + 73.0
    shifted[0] += 2.9  # 20 Hz near its +3 dB limit moves the centred level
    check = ea.check_programme_signal(frequencies, shifted)
    assert check.offset_db == pytest.approx(-73.2, abs=1e-12)
    ax = check.plot(language=language)
    table, referred = ax.lines
    np.testing.assert_array_equal(table.get_ydata(), check.relative_levels_db)
    np.testing.assert_allclose(referred.get_ydata(), shifted + check.offset_db)
    band = ax.collections[0].get_paths()[0].vertices[:, 1]
    assert float(np.min(band)) == pytest.approx(float(np.min(levels - tolerances)))
    assert float(np.max(band)) == pytest.approx(float(np.max(levels + tolerances)))
    verdict = "pass" if language == "en" else "cumple"
    assert ax.get_title().endswith(verdict)
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
def test_limiting_plot_names_the_ratio_and_the_verdict(language: str) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    x = ea.simulated_programme_signal(FS, 10.0, seed=8)
    check = ea.check_limiting_test_signal(x, FS)
    ax = check.plot(language=language)
    np.testing.assert_allclose(
        ax.lines[1].get_ydata(),
        check.spectrum.band_levels_db + check.spectrum.offset_db,
    )
    ratio = f"{check.peak_to_rms:.2f}"
    if language == "es":
        ratio = ratio.replace(".", ",")
    assert ratio in ax.get_title()
    verdict = "fail" if language == "en" else "no cumple"
    assert ax.get_title().endswith(verdict)
    plt.close("all")
