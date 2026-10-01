#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Tests for the acoustic rail roughness of EN 15610:2009.

EN 15610 prints no worked example: nothing in it is a record turned into a
spectrum with the numbers shown. The oracles are closed forms instead. A
sinusoid of amplitude :math:`A` whose wavenumber sits on a Fourier line has a
mean square of :math:`A^2/2`, all of it inside one band, so its band level is
:math:`10 \lg (A^2/2)`; a narrow pit is bridged where a circle of radius
0,375 m rests on its rims; and the Annex C sharing of a band's energy by the
width it covers conserves the energy that falls inside the targets. The
spike loop is run on the ridge the Annex B listing never finishes on.
"""

from __future__ import annotations

import math

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import environment
from phonometry.environment.sources.acoustic_roughness import (
    AcousticRoughnessSpectrum,
    acoustic_roughness_spectrum,
    average_roughness_spectra,
    curvature_processed_roughness,
    redistributed_band_energies,
    remove_roughness_spikes,
    roughness_measurement_lines,
)

_DX = 1.0e-3


def _sinusoid(
    amplitude_um: float, wavenumber_per_m: float, length_m: float
) -> np.ndarray:
    x = np.arange(0.0, length_m, _DX)
    return amplitude_um * np.cos(2.0 * np.pi * wavenumber_per_m * x)


def test_a_sinusoid_on_a_line_reads_its_mean_square_in_its_band() -> None:
    """A 3 um sinusoid of 1 cm wavelength is 10 lg(9/2) dB re 1 um in the 1 cm band."""
    spectrum = acoustic_roughness_spectrum(
        _sinusoid(3.0, 100.0, 15.0),
        sample_spacing_m=_DX,
        spike_removal=False,
        curvature_processing=False,
    )
    assert spectrum.level_at(0.01) == pytest.approx(10.0 * math.log10(4.5), abs=1e-9)
    # 7.4.2: 1 m segments overlapping by half, starting every 0,5 m to 14 m.
    assert spectrum.segment_count == 29


def test_the_linear_trend_of_each_segment_is_removed() -> None:
    """7.4.2: each segment has its mean and its linear trend removed.

    A 1 mm/m slope under the 3 um sinusoid leaves the 1 cm band at
    10 lg 4,5 dB and puts nothing measurable in the 0,25 m band (about
    -86 dB, rounding); removing the mean alone would leave a sawtooth of
    0,5 mm in every segment, about +9 dB there.
    """
    x = np.arange(0.0, 15.0, _DX)
    record = _sinusoid(3.0, 100.0, 15.0) + 1000.0 * x
    spectrum = acoustic_roughness_spectrum(
        record, sample_spacing_m=_DX, spike_removal=False, curvature_processing=False
    )
    assert spectrum.level_at(0.01) == pytest.approx(10.0 * math.log10(4.5), abs=1e-6)
    assert spectrum.level_at(0.25) < -60.0


def test_a_band_reaches_its_base_ten_edges() -> None:
    """The 1 cm band runs from 10^(2 - 0,05) to 10^(2 + 0,05) per metre, 89,1 to 112,2.

    A sinusoid of 110 cycles per metre on a 1 m segment puts its energy on
    the lines at 109, 110 and 111 per metre, all inside the band, so the
    band reads 10 lg(A^2/2); bands narrower than their tenth of a decade
    would leave most of it in a gap.
    """
    spectrum = acoustic_roughness_spectrum(
        _sinusoid(2.0, 110.0, 15.0),
        sample_spacing_m=_DX,
        spike_removal=False,
        curvature_processing=False,
    )
    assert spectrum.level_at(0.01) == pytest.approx(10.0 * math.log10(2.0), abs=1e-9)


def test_a_band_edge_splits_the_line_it_crosses() -> None:
    """The upper edge of the 1 cm band, 100 x 10^0,05 = 112,20 per metre, cuts the line at 112.

    A sinusoid of 111 cycles per metre on 1 m segments puts a sixth of its
    mean square on the lines at 110 and 112 per metre and four sixths on
    111. The line at 112 spans 111,5 to 112,5 per metre, and the band keeps
    the part of it below its edge (Annex C), so the band reads
    10 lg(A^2/2 x (5 + p)/6) with p = 112,20 - 111,5.
    """
    spectrum = acoustic_roughness_spectrum(
        _sinusoid(2.0, 111.0, 15.0),
        sample_spacing_m=_DX,
        spike_removal=False,
        curvature_processing=False,
    )
    inside = 100.0 * 10.0**0.05 - 111.5
    expected = 10.0 * math.log10(2.0 * (5.0 + inside) / 6.0)
    assert spectrum.level_at(0.01) == pytest.approx(expected, abs=1e-9)


def test_a_longer_segment_keeps_a_longer_wavelength_inside_its_band() -> None:
    """At 0,1 m the Hanning lobe of 1 m segments leaks out of the band; 4 m ones keep it."""
    record = _sinusoid(2.0, 10.0, 24.0)
    long = acoustic_roughness_spectrum(
        record,
        sample_spacing_m=_DX,
        spike_removal=False,
        curvature_processing=False,
        segment_length_m=4.0,
    )
    assert long.level_at(0.1) == pytest.approx(10.0 * math.log10(2.0), abs=1e-9)
    short = acoustic_roughness_spectrum(
        record, sample_spacing_m=_DX, spike_removal=False, curvature_processing=False
    )
    assert short.level_at(0.1) < long.level_at(0.1)


def test_the_bands_run_from_a_quarter_segment_down_to_nyquist() -> None:
    """1 m segments at 1 mm resolve 0,25 m (7.5) down to the 2,5 mm band, longest first."""
    spectrum = acoustic_roughness_spectrum(
        _sinusoid(1.0, 50.0, 3.0), sample_spacing_m=_DX
    )
    assert spectrum.wavelengths_m[0] == pytest.approx(0.25)
    assert spectrum.wavelengths_m[-1] == pytest.approx(0.0025)
    assert np.all(np.diff(spectrum.wavelengths_m) < 0.0)
    assert spectrum.record_length_m == pytest.approx(3.0)
    assert spectrum.segment_count == 5


def test_a_band_longer_than_a_quarter_segment_is_left_out() -> None:
    """7.5: 1,2 m segments resolve 0,30 m, which leaves out the 0,315 m band."""
    spectrum = acoustic_roughness_spectrum(
        _sinusoid(1.0, 50.0, 3.0), sample_spacing_m=_DX, segment_length_m=1.2
    )
    assert spectrum.wavelengths_m[0] == pytest.approx(0.25)


def test_the_nominal_wavelengths_are_the_preferred_numbers() -> None:
    """Clause 9 labels bands by the EN ISO 266 preferred numbers, read as wavelengths."""
    spectrum = acoustic_roughness_spectrum(
        _sinusoid(1.0, 50.0, 2.0), sample_spacing_m=_DX
    )
    nominal = [0.25, 0.2, 0.16, 0.125, 0.1, 0.08, 0.063, 0.05, 0.04, 0.0315]
    np.testing.assert_allclose(spectrum.wavelengths_m[: len(nominal)], nominal)


def test_a_spike_is_removed_by_a_straight_line() -> None:
    """A one-sample 30 um spike on a flat record is interpolated away (7.2)."""
    record = np.zeros(2000)
    record[1000] = 30.0
    cleaned = remove_roughness_spikes(record, sample_spacing_m=_DX)
    assert np.max(np.abs(cleaned)) == pytest.approx(0.0, abs=1e-12)
    assert record[1000] == pytest.approx(30.0)


@pytest.mark.parametrize(("height_um", "removed"), [(4.9, False), (5.1, True)])
def test_a_spike_bends_under_minus_1e7_um_per_m2(
    height_um: float, *, removed: bool
) -> None:
    """7.2 c): a one-sample peak of h um bends by -2h/dx**2 at its crest.

    At 4,9 um that is -9,8e6 um/m**2, no spike; at 5,1 um it is
    -1,02e7 um/m**2, a spike. Either would pass the height test,
    h > w**2/a with w = 2 mm, so the second derivative alone decides.
    """
    record = np.zeros(200)
    record[100] = height_um
    cleaned = remove_roughness_spikes(record, sample_spacing_m=_DX)
    if removed:
        assert np.max(np.abs(cleaned)) == pytest.approx(0.0, abs=1e-12)
    else:
        np.testing.assert_array_equal(cleaned, record)


def test_a_crest_bending_at_exactly_minus_1e7_um_per_m2_is_no_spike() -> None:
    """7.2 c) asks for a second derivative less than -1e7 um/m**2, not equal to it.

    At a spacing of 2^-10 m every step is exact in binary, and a one-sample
    peak of 1e7 x dx**2 / 2 um bends by exactly -1e7 um/m**2; one 1 % higher
    bends further and goes.
    """
    spacing = 2.0**-10
    height = 1.0e7 * spacing**2 / 2.0
    record = np.zeros(200)
    record[100] = height
    np.testing.assert_array_equal(
        remove_roughness_spikes(record, sample_spacing_m=spacing), record
    )
    record[100] = 1.01 * height
    cleaned = remove_roughness_spikes(record, sample_spacing_m=spacing)
    assert np.max(np.abs(cleaned)) == pytest.approx(0.0, abs=1e-12)


def test_a_slope_of_exactly_5e3_um_per_m_is_still_inside_the_spike() -> None:
    """7.2 d) puts an edge where abs(dr/dx) becomes less than 5e3 um/m, so 5e3 itself is inside.

    At a spacing of 2^-10 m a 9,765625 um shoulder two samples from the
    crest gives a slope of exactly 5e3 um/m, and the edges run on to the
    flat record; reading the edge at the slope itself would stop on the
    4 um shoulder and leave it.
    """
    spacing = 2.0**-10
    shoulder = 5.0e3 * 2.0 * spacing
    record = np.zeros(200)
    record[97:104] = [0.0, 4.0, shoulder, 100.0, shoulder, 4.0, 0.0]
    cleaned = remove_roughness_spikes(record, sample_spacing_m=spacing)
    assert np.max(np.abs(cleaned)) == pytest.approx(0.0, abs=1e-12)


def test_the_edges_of_a_spike_are_where_the_slope_falls_under_5e3_um_per_m() -> None:
    """7.2 d): a 100 um peak on shoulders of 13,2, 9,8 and 3 um is cut level at 3 um.

    The slope is 5,1e3 um/m two samples out and 4,9e3 um/m three out, so the
    edges are the 3 um samples and the straight line between them is level.
    Edges read at a slope a little steeper would stop on the 9,8 um
    shoulder, and edges read at one a little gentler would run on to the
    flat record at 0 um.
    """
    record = np.zeros(200)
    record[97:104] = [3.0, 9.8, 13.2, 100.0, 13.2, 9.8, 3.0]
    expected = np.zeros(200)
    expected[97:104] = 3.0
    np.testing.assert_allclose(
        remove_roughness_spikes(record, sample_spacing_m=_DX), expected, atol=1e-12
    )


@pytest.mark.parametrize(("height_um", "removed"), [(21.0, False), (22.0, True)])
def test_a_spike_is_removed_when_higher_than_w_squared_over_3_m(
    height_um: float, *, removed: bool
) -> None:
    """7.2: a peak between edges 8 mm apart goes when h > (8 mm)**2 / 3 m, 21,3 um.

    Shoulders of 15, 10,5 and 4 um either side keep the slope above
    5e3 um/m for three samples, put the edges four samples out, where it is
    2e3 um/m, and leave the crest sharp enough to be a spike. The peak stands
    its whole height over the line between the edges, so 21 um stays and
    22 um goes.
    """
    record = np.zeros(200)
    record[96:105] = [0.0, 4.0, 10.5, 15.0, height_um, 15.0, 10.5, 4.0, 0.0]
    cleaned = remove_roughness_spikes(record, sample_spacing_m=_DX)
    if removed:
        assert np.max(np.abs(cleaned)) == pytest.approx(0.0, abs=1e-12)
    else:
        np.testing.assert_array_equal(cleaned, record)


def test_a_broad_ridge_is_kept_and_the_sweep_ends() -> None:
    """A ridge 200 um high on a 40 mm base fails h > w**2/a and stays.

    The slope rule of 7.2 d) puts its edges 42 mm apart, so w**2/3 is
    0,59 mm, above its 0,2 mm. Its crest has the second derivative and the
    sign change of a spike, so it is detected on every pass, and the Annex
    B.9.2 listing, which repeats while any second derivative is below the
    threshold, never stops on it; the sweep here stops when a pass removes
    nothing (errata register).
    """
    record = np.zeros(1000)
    ramp = np.arange(21) * 10.0
    record[480:501] = ramp
    record[500:521] = ramp[::-1]
    cleaned = remove_roughness_spikes(record, sample_spacing_m=_DX)
    np.testing.assert_array_equal(cleaned, record)


def test_a_bend_without_an_extremum_is_no_spike() -> None:
    """A rail rising 20 um/mm, then 5 um/mm, bends at -1,5e7 um/m**2 and stays.

    7.2 c) asks a spike for the change of sign of dr/dx as well, and there
    is none at the bend; the Annex B.9.2 listing loops on it for ever, since
    its loop condition looks at the second derivative alone (errata
    register).
    """
    x = np.arange(1000.0)
    record = np.where(x < 500.0, 20.0 * x, 1.0e4 + 5.0 * (x - 500.0))
    np.testing.assert_array_equal(
        remove_roughness_spikes(record, sample_spacing_m=_DX), record
    )


def test_a_narrow_pit_is_bridged_where_the_wheel_rests_on_its_rims() -> None:
    """The circle of 0,375 m radius spans an 11 mm pit 6 mm either side of its middle."""
    record = np.zeros(2001)
    record[995:1006] = -50.0
    processed = curvature_processed_roughness(record, sample_spacing_m=_DX)
    radius_um = 0.375e6
    rest = -(radius_um - math.sqrt(radius_um**2 - 6.0e3**2))
    assert processed[1000] == pytest.approx(rest, rel=1e-12)
    assert np.all(processed[:994] == 0.0)


def test_a_crest_and_a_flat_record_are_left_alone() -> None:
    """The circle through a crest lies above its flanks, so r'(x) = r(x) there."""
    x = np.arange(-0.05, 0.05, _DX)
    crest = -1.0e3 * x**2  # a crest far flatter than the circle
    np.testing.assert_allclose(
        curvature_processed_roughness(crest, sample_spacing_m=_DX), crest
    )
    flat = np.full(100, 5.0)
    np.testing.assert_array_equal(
        curvature_processed_roughness(flat, sample_spacing_m=_DX), flat
    )


def test_band_energy_is_shared_by_the_width_it_covers() -> None:
    """Annex C: the two straddling lines count for their portion inside the band."""
    # Lines 1 Hz wide at 0.5 .. 9.5 Hz, each holding 1; a band from 2.25 to 5.5.
    centres = np.arange(0.5, 10.0, 1.0)
    shared = redistributed_band_energies(
        centres - 0.5, centres + 0.5, np.ones(10), [2.25], [5.5]
    )
    assert shared[0] == pytest.approx(0.75 + 1.0 + 1.0 + 0.5)


def test_band_energy_inside_the_targets_is_conserved() -> None:
    """Shared over targets that tile the sources, no energy is created or lost."""
    rng = np.random.default_rng(3)
    lower = np.cumsum(rng.uniform(0.5, 2.0, 12))
    upper = lower + rng.uniform(0.2, 0.4, 12)
    energies = rng.uniform(0.1, 3.0, 12)
    edges = np.linspace(lower[0], upper[-1], 8)
    shared = redistributed_band_energies(lower, upper, energies, edges[:-1], edges[1:])
    assert shared.sum() == pytest.approx(energies.sum(), rel=1e-12)


def test_band_energy_refuses_malformed_bands() -> None:
    """An upper edge below its lower one is not a band."""
    with pytest.raises(ValueError, match="upper edge must lie above its lower edge"):
        redistributed_band_energies([2.0], [1.0], [1.0], [0.0], [3.0])


def test_band_energy_refuses_a_negative_energy() -> None:
    """Energies are mean squares."""
    with pytest.raises(ValueError, match="'energies' are mean squares"):
        redistributed_band_energies([0.0], [1.0], [-1.0], [0.0], [1.0])


def test_the_average_is_on_mean_squares() -> None:
    """7.6: two spectra average as 10 lg of the mean of their energies."""
    wavelengths = [0.1, 0.08, 0.063]
    one = AcousticRoughnessSpectrum(
        wavelengths, [0.0, 3.0, -2.0], record_length_m=1.0, segment_count=1
    )
    two = AcousticRoughnessSpectrum(
        wavelengths, [6.0, 3.0, 4.0], record_length_m=2.0, segment_count=3
    )
    mean = average_roughness_spectra([one, two])
    expected = 10.0 * np.log10(
        (10.0 ** (one.levels_db / 10) + 10.0 ** (two.levels_db / 10)) / 2
    )
    np.testing.assert_allclose(mean.levels_db, expected, rtol=0, atol=1e-12)
    assert mean.record_length_m == pytest.approx(3.0)
    assert mean.segment_count == 4


def test_the_average_keeps_only_the_common_bands() -> None:
    """Bands one spectrum lacks are left out, and lengths nobody knows stay unknown."""
    one = AcousticRoughnessSpectrum([0.25, 0.2, 0.16], [1.0, 1.0, 1.0])
    two = AcousticRoughnessSpectrum([0.2, 0.16, 0.125], [1.0, 1.0, 1.0])
    mean = average_roughness_spectra([one, two])
    np.testing.assert_allclose(mean.wavelengths_m, [0.2, 0.16])
    assert mean.record_length_m is None


def test_the_average_needs_a_spectrum() -> None:
    """An empty list has nothing to average."""
    with pytest.raises(ValueError, match="'spectra' holds no spectrum"):
        average_roughness_spectra([])


@pytest.mark.parametrize(
    ("width_mm", "lines"),
    [
        (10.0, (1, 0.0)),
        (20.0, (1, 0.0)),
        (20.5, (3, 5.0)),
        (30.0, (3, 5.0)),
        (30.5, (3, 10.0)),
    ],
)
def test_the_lines_follow_the_reference_width(
    width_mm: float, lines: tuple[int, float]
) -> None:
    """6.4.3: one line up to 20 mm, three 5 mm apart up to 30 mm, 10 mm apart above."""
    assert roughness_measurement_lines(width_mm) == lines


def test_a_spectrum_holds_its_bands_read_only() -> None:
    """The arrays of a spectrum refuse in-place writes."""
    spectrum = AcousticRoughnessSpectrum([0.1, 0.05], [1.0, 2.0])
    with pytest.raises(ValueError, match="assignment destination is read-only"):
        spectrum.levels_db[0] = 3.0


def test_a_spectrum_refuses_increasing_wavelengths() -> None:
    """Bands run from the longest wavelength down, as clause 9 draws them."""
    with pytest.raises(ValueError, match="'wavelengths_m' must name distinct bands"):
        AcousticRoughnessSpectrum([0.05, 0.1], [1.0, 2.0])


def test_a_missing_band_is_a_key_error() -> None:
    """level_at names the band it could not find."""
    spectrum = AcousticRoughnessSpectrum([0.1, 0.05], [1.0, 2.0])
    with pytest.raises(KeyError, match=r"no band at 0\.2 m"):
        spectrum.level_at(0.2)


def test_the_sampling_interval_is_at_most_a_millimetre() -> None:
    """5.5 asks for 1 mm or less."""
    record = np.zeros(1000)
    for spacing in (1.01e-3, 2.0e-3):
        with pytest.raises(ValueError, match="'sample_spacing_m' is .*1 mm or less"):
            acoustic_roughness_spectrum(record, sample_spacing_m=spacing)


def test_a_segment_is_at_least_a_metre() -> None:
    """7.4.2 asks for Fourier segments of at least 1 m."""
    record = np.zeros(2000)
    with pytest.raises(ValueError, match="'segment_length_m' is .*at least 1 m"):
        acoustic_roughness_spectrum(record, sample_spacing_m=_DX, segment_length_m=0.5)


def test_a_record_shorter_than_a_segment_is_refused() -> None:
    """5.6 asks for records of at least 1 m."""
    record = np.zeros(500)
    with pytest.raises(ValueError, match="shorter than one 1 m segment"):
        acoustic_roughness_spectrum(record, sample_spacing_m=_DX)


def test_the_spectrum_plot_draws_the_limit_on_a_reversed_axis() -> None:
    """The wavelength decreases to the right and the limit is its own line."""
    spectrum = acoustic_roughness_spectrum(
        _sinusoid(1.0, 50.0, 2.0), sample_spacing_m=_DX
    )
    ax = spectrum.plot(
        limit_db=environment.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB, language="es"
    )
    left, right = ax.get_xlim()
    assert left > right
    labels = [line.get_label() for line in ax.get_lines()]
    assert labels == ["Medida", "Límite"]
    assert ax.get_xlabel() == r"Longitud de onda $\lambda$ [cm]"
    plt.close(ax.figure)
