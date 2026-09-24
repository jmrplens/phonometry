#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The exponential-sweep test of IEC 61260-1:2014 5.14 and its two annexes.

Formula (17) is held to the worked example both IEC 61260-2 and IEC 61260-3
print in Annex B (L_c = 107,97 dB), and its uncertainty to their Annex A
example (0,057 dB, 0,115 dB expanded, 0,128 dB with a 0,1 dB display). The
test run on a bank is held to what Annex G predicts for a time-invariant
filter: it reads the band's effective bandwidth deviation.
"""

from __future__ import annotations

import math

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import reference_data as ref

from phonometry import filters
from phonometry.filters import time_invariance


def _a35_uncertainty(*, display: bool) -> float:
    """Formula (A.2) on the A.3.5 example, with or without the display."""
    inputs = ref.IEC61260_A35_INPUTS
    u_in = math.hypot(
        inputs["level_resolution_db"] / (2.0 * math.sqrt(3.0)),
        inputs["level_constancy_db"],
    )
    return filters.swept_level_uncertainty(
        input_level_uncertainty_db=u_in,
        sweep_duration_s=inputs["sweep_duration_s"],
        sweep_duration_uncertainty_s=inputs["sweep_duration_uncertainty_s"],
        averaging_time_s=inputs["averaging_time_s"],
        averaging_time_uncertainty_s=inputs["averaging_time_uncertainty_s"],
        start_frequency_hz=inputs["start_frequency_hz"],
        start_frequency_uncertainty_hz=inputs["start_frequency_uncertainty_hz"],
        end_frequency_hz=inputs["end_frequency_hz"],
        end_frequency_uncertainty_hz=inputs["end_frequency_uncertainty_hz"],
        display_resolution_db=inputs["display_resolution_db"] if display else 0.0,
    )


# --------------------------------------------------------------------------
# Formula (17): Annex B of IEC 61260-2 and IEC 61260-3
# --------------------------------------------------------------------------
def test_formula_17_reproduces_annex_b() -> None:
    """(B.5): L_c = 127 dB - 19,03 dB = 107,97 dB."""
    example = ref.IEC61260_B5
    level = filters.swept_band_level(
        example["input_level_db"],
        fraction=example["fraction"],
        sweep_duration_s=example["sweep_duration_s"],
        averaging_time_s=example["averaging_time_s"],
        start_frequency_hz=example["start_frequency_hz"],
        end_frequency_hz=example["end_frequency_hz"],
    )
    assert round(level, 2) == example["expected_level_db"]
    assert round(level - example["input_level_db"], 2) == example["correction_db"]


def test_formula_17_subtracts_the_reference_attenuation() -> None:
    kwargs = {
        "fraction": 1,
        "sweep_duration_s": 10.0,
        "averaging_time_s": 12.0,
        "start_frequency_hz": 5.0,
        "end_frequency_hz": 20000.0,
    }
    base = filters.swept_band_level(94.0, **kwargs)
    shifted = filters.swept_band_level(94.0, reference_attenuation_db=0.5, **kwargs)
    assert base - shifted == pytest.approx(0.5, abs=1e-12)
    # lg(f2/f1) = 3/(10 b): the octave band holds 0.3 of a decade.
    decades = math.log10(20000.0 / 5.0)
    assert base == pytest.approx(94.0 + 10 * math.log10(10 / 12 * 0.3 / decades))


def test_formula_17_refuses_a_sweep_that_does_not_rise() -> None:
    with pytest.raises(ValueError, match="'end_frequency_hz' .* must be above"):
        filters.swept_band_level(
            0.0,
            fraction=3,
            sweep_duration_s=10.0,
            averaging_time_s=10.0,
            start_frequency_hz=100.0,
            end_frequency_hz=100.0,
        )


# --------------------------------------------------------------------------
# Annex A: the uncertainty of the swept level
# --------------------------------------------------------------------------
def test_annex_a_reproduces_the_printed_example() -> None:
    """A.3.5: u ~ 0,057 dB, U = 0,115 dB, and 0,128 dB with the display."""
    printed = ref.IEC61260_A35_PRINTED
    u = _a35_uncertainty(display=False)
    assert round(u, 3) == printed["u_lc_db"]
    assert round(2.0 * u, 3) == printed["expanded_db"]
    assert (
        round(2.0 * _a35_uncertainty(display=True), 3)
        == printed["expanded_with_display_db"]
    )


def test_formula_a2_as_printed_would_not_reproduce_its_example() -> None:
    """Without the square on the frequency coefficient (A.2) gives 0,075 dB.

    The printed Formula (A.2) of both annexes leaves the square off
    10 / (ln(f_end/f_start) ln 10); the example's 0,057 dB needs it, and the
    derivative of Formula (17) gives it.
    """
    inputs = ref.IEC61260_A35_INPUTS
    u_in = math.hypot(0.1 / (2 * math.sqrt(3)), 0.03)
    k_t = 10.0 / math.log(10.0)
    k_f = 10.0 / (
        math.log(inputs["end_frequency_hz"] / inputs["start_frequency_hz"])
        * math.log(10.0)
    )
    rel_t = (
        inputs["sweep_duration_uncertainty_s"] / inputs["sweep_duration_s"]
    ) ** 2 + (inputs["averaging_time_uncertainty_s"] / inputs["averaging_time_s"]) ** 2
    rel_f = (
        inputs["end_frequency_uncertainty_hz"] / inputs["end_frequency_hz"]
    ) ** 2 + (
        inputs["start_frequency_uncertainty_hz"] / inputs["start_frequency_hz"]
    ) ** 2
    as_printed = math.sqrt(u_in**2 + k_t**2 * rel_t + k_f * rel_f)
    assert round(as_printed, 3) == 0.075
    assert round(_a35_uncertainty(display=False), 3) == 0.057


def test_annex_a_refuses_a_negative_uncertainty() -> None:
    with pytest.raises(ValueError, match="'sweep_duration_uncertainty_s'"):
        filters.swept_level_uncertainty(
            input_level_uncertainty_db=0.04,
            sweep_duration_s=20.0,
            sweep_duration_uncertainty_s=-0.05,
            averaging_time_s=20.0,
            averaging_time_uncertainty_s=0.02,
            start_frequency_hz=0.5,
            start_frequency_uncertainty_hz=0.05,
            end_frequency_hz=50000.0,
            end_frequency_uncertainty_hz=5.0,
        )


# --------------------------------------------------------------------------
# The test run on a bank
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def third_octave_bank() -> filters.OctaveFilterBank:
    return filters.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[100, 5000])


@pytest.fixture(scope="module")
def swept(third_octave_bank: filters.OctaveFilterBank) -> filters.TimeInvarianceResult:
    return filters.verify_time_invariance(third_octave_bank)


def test_a_time_invariant_bank_reads_its_effective_bandwidth(
    third_octave_bank: filters.OctaveFilterBank,
    swept: filters.TimeInvarianceResult,
) -> None:
    """Annex G, G.2.8: the swept output deviates from L_c by Delta B.

    The multirate bank, decimation included, reads within 0.01 dB of the
    effective bandwidth deviation its transfer functions give at both ends
    of the rates 5.14.3 allows.
    """
    design = filters.verify_filter_class(third_octave_bank)
    delta_b = np.array([b["bandwidth_deviation_db"] for b in design.bands])
    assert swept.seconds_per_decade == (2.0, 5.0)
    np.testing.assert_allclose(
        swept.deviations_db, np.vstack([delta_b, delta_b]), atol=0.01
    )
    assert swept.overall_class == 1
    assert swept.band_classes == (1,) * third_octave_bank.num_bands


def test_the_sweep_starts_and_ends_a_decade_past_the_55_db_points(
    third_octave_bank: filters.OctaveFilterBank,
    swept: filters.TimeInvarianceResult,
) -> None:
    """7.4.2: at least 55 dB below the lowest edge; the design adds a decade."""
    lowest = third_octave_bank.freq[0]
    assert swept.start_frequency_hz < lowest / 10.0
    assert swept.end_frequency_hz == 24000.0
    decades = math.log10(swept.end_frequency_hz / swept.start_frequency_hz)
    assert swept.sweep_durations_s[0] == pytest.approx(2.0 * decades, abs=1e-4)
    assert swept.sweep_durations_s[1] == pytest.approx(5.0 * decades, abs=1e-4)
    for t_sweep, t_avg in zip(
        swept.sweep_durations_s, swept.averaging_times_s, strict=True
    ):
        assert t_avg > t_sweep


def test_the_expected_level_is_formula_17(
    third_octave_bank: filters.OctaveFilterBank,
    swept: filters.TimeInvarianceResult,
) -> None:
    for row, (t_sweep, t_avg) in enumerate(
        zip(swept.sweep_durations_s, swept.averaging_times_s, strict=True)
    ):
        level = filters.swept_band_level(
            0.0,
            fraction=3,
            sweep_duration_s=t_sweep,
            averaging_time_s=t_avg,
            start_frequency_hz=swept.start_frequency_hz,
            end_frequency_hz=swept.end_frequency_hz,
        )
        # A_ref of a Butterworth band at its exact mid-band is a hair off zero.
        np.testing.assert_allclose(swept.expected_levels_db[row], level, atol=1e-3)


def test_a_bank_that_loses_half_its_output_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A band path that drops the second half of what it filters is time-variant.

    Its output energy halves wherever the sweep crossed the band late, so the
    swept level falls far below Formula (17) and no class is met.
    """
    real = time_invariance._decimate_and_filter

    def forgetful(x: np.ndarray, sos: np.ndarray, factor: int) -> np.ndarray:
        y = real(x, sos, factor)
        y[y.size // 3 :] = 0.0
        return y

    monkeypatch.setattr(time_invariance, "_decimate_and_filter", forgetful)
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[500, 2000])
    result = filters.verify_time_invariance(bank, seconds_per_decade=(5.0,))
    assert result.overall_class is None
    assert result.worst_deviation_db < -0.6


@pytest.mark.parametrize("rates", [(), (1.5,), (2.0, 5.5)])
def test_rates_outside_the_range_of_5_14_3_are_refused(
    rates: tuple[float, ...],
) -> None:
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[500, 2000])
    with pytest.raises(ValueError, match="'seconds_per_decade' must hold"):
        filters.verify_time_invariance(bank, seconds_per_decade=rates)


def test_the_verdict_has_no_truth_value_and_freezes_its_arrays(
    swept: filters.TimeInvarianceResult,
) -> None:
    with pytest.raises(TypeError, match="TimeInvarianceResult has no truth value"):
        bool(swept)
    assert not swept.output_levels_db.flags.writeable
    assert not swept.band_frequencies.flags.writeable


def test_a_verdict_refuses_levels_of_the_wrong_shape(
    swept: filters.TimeInvarianceResult,
) -> None:
    import dataclasses

    bad = np.asarray(swept.output_levels_db)[:, :-1]
    with pytest.raises(ValueError, match="'output_levels_db' must be shaped"):
        dataclasses.replace(swept, output_levels_db=bad)


@pytest.mark.parametrize("language", ["en", "es"])
def test_the_verdict_plots_one_line_per_rate(
    swept: filters.TimeInvarianceResult, language: str
) -> None:
    ax = swept.plot(language=language)
    rate_lines = [line for line in ax.lines if line.get_marker() in ("o", "s")]
    assert len(rate_lines) == 2
    assert "5.14" in ax.get_title()
    plt.close("all")
