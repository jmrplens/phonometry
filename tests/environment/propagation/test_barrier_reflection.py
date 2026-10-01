#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The in situ sound reflection index of EN 1793-5:2016.

Oracles from the printed pages (``tests/reference_data/barrier_reflection.py``
names each page and folio):

- Table 2, the paths and the divergence correction of the nine microphones,
  and Table 3, the path differences of the two position checks, both
  recomputed from the three distances the standard fixes;
- 5.6.1 NOTE 1, the 1,96 m sampled area of a 4 m sample at 340 m/s;
- 5.5.5 and 5.5.1, the three lengths of each window;
- Table B.1, the average of twelve grid positions and its single number, and
  Table B.2, the expanded uncertainty of the same example.

Closed forms the processing has to satisfy whatever the loudspeaker does,
which is what makes a synthetic record an oracle rather than a regression
pin:

- a perfect flat reflector returns :math:`RI = 1` in every band, once the
  divergence correction has put back the longer path;
- a reflection of amplitude :math:`r` returns :math:`r^2`;
- a reflection of two impulses :math:`\tau` apart returns
  :math:`r^2 (2 + 2\,\overline{\cos 2\pi f\tau})`, the mean over the exact band
  edges, which pins the bands and which window serves which of them;
- a gain change between the two configurations does not move the index,
  which is what the gain factor is for;
- the subtraction finds a sub-sample shift on its 1/50 grid.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest
from reference_data import barrier_reflection as oracle

from phonometry.environment import propagation as prop
from phonometry.environment.propagation import barrier_reflection as br

_FS = 48000.0
_C = 343.0
_N = 4096
_START = 300.0
_BANDS = len(prop.TRAFFIC_NOISE_BANDS_HZ)


def _pulse(at: float, amplitude: float, *, width_s: float = 0.05e-3) -> np.ndarray:
    """A short band-pass pulse centred on sample ``at`` (fractional allowed)."""
    t = (np.arange(_N) - at) / _FS
    return (
        amplitude * np.exp(-0.5 * (t / width_s) ** 2) * np.cos(2 * np.pi * 3000.0 * t)
    )


def _grid(
    *, reflection: float = 1.0, gain: float = 1.0, shift: float = 0.0
) -> tuple[np.ndarray, np.ndarray]:
    """Nine in-front and free-field records of a flat reflector of amplitude ``reflection``."""
    paths = prop.reflection_grid_paths_m()
    front = np.zeros((9, _N))
    free = np.zeros((9, _N))
    for k, (direct, reflected) in enumerate(paths):
        at = _START + direct / _C * _FS
        free[k] = _pulse(at + shift, 1.0 / direct)
        front[k] = gain * (
            _pulse(at, 1.0 / direct)
            + reflection * _pulse(_START + reflected / _C * _FS, 1.0 / reflected)
        )
    return front, free


def _impulse_grid(
    *,
    reflection: float,
    taps: tuple[int, ...] = (0,),
    late_s: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """One-sample direct sounds and reflections, all on whole samples.

    Microphone ``k`` hears the direct sound as an impulse of ``1 / d_i`` and
    the reflection as ``reflection / d_r`` at each tap, whole samples after
    the specular arrival. With ``late_s`` a further impulse of half the
    reflection arrives that long after it. Every impulse but the late one
    lies in the flat part of its window, so the band energies are closed forms.
    """
    paths = prop.reflection_grid_paths_m()
    front = np.zeros((9, _N))
    free = np.zeros((9, _N))
    for k, (direct, reflected) in enumerate(paths):
        at = round(_START + direct / _C * _FS)
        back = at + round((reflected - direct) / _C * _FS)
        free[k, at] = 1.0 / direct
        front[k, at] = 1.0 / direct
        for tap in taps:
            front[k, back + tap] += reflection / reflected
        if late_s is not None:
            front[k, back + round(late_s * _FS)] += 0.5 * reflection / reflected
    return front, free


def _comb(reflection: float, delay_s: float) -> np.ndarray:
    """Formula (1) in closed form for two impulses ``delay_s`` apart, per band."""
    centres = 1000.0 * 10.0 ** (
        np.round(10.0 * np.log10(np.asarray(prop.TRAFFIC_NOISE_BANDS_HZ) / 1000.0))
        / 10.0
    )
    lower, upper = centres * 10.0**-0.05, centres * 10.0**0.05
    phase = 2.0 * np.pi * delay_s
    mean_cos = (np.sin(phase * upper) - np.sin(phase * lower)) / (
        phase * (upper - lower)
    )
    return reflection**2 * (2.0 + 2.0 * mean_cos)


def _index(
    front: np.ndarray, free: np.ndarray, **kwargs: object
) -> prop.ReflectionIndexResult:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", prop.RoadDeviceWarning)
        return prop.reflection_index(front, free, _FS, speed_of_sound=_C, **kwargs)


class TestGeometry:
    """Formula (2), Tables 2 and 3, Formula (8)."""

    def test_table_2_is_the_geometry_rounded(self) -> None:
        paths = prop.reflection_grid_paths_m()
        corrections = prop.geometric_divergence_corrections()
        for k, (d_i, d_r, c_geo) in enumerate(oracle.TABLE_2):
            assert round(float(paths[k, 0]), 2) == pytest.approx(d_i)
            assert round(float(paths[k, 1]), 2) == pytest.approx(d_r)
            assert round(float(corrections[k]), 2) == pytest.approx(c_geo)

    def test_the_published_table_2_is_the_printed_one(self) -> None:
        assert tuple(prop.REFLECTION_GRID_DISTANCES[k] for k in range(1, 10)) == (
            oracle.TABLE_2
        )

    def test_table_3_is_the_geometry_rounded(self) -> None:
        paths = prop.reflection_grid_paths_m()
        direct_to_five = paths[:, 0] - paths[4, 0]
        direct_to_reflected = paths[:, 1] - paths[:, 0]
        for k, (dk5, dk) in enumerate(oracle.TABLE_3):
            assert round(float(direct_to_five[k]), 3) == pytest.approx(dk5)
            assert round(float(direct_to_reflected[k]), 3) == pytest.approx(dk)
        assert tuple(prop.REFLECTION_PATH_DIFFERENCES_M[k] for k in range(1, 10)) == (
            oracle.TABLE_3
        )
        assert oracle.TABLE_3_TOLERANCE_M == pytest.approx(
            prop.REFLECTION_PATH_TOLERANCE_M
        )

    def test_microphone_5_is_the_closed_form(self) -> None:
        paths = prop.reflection_grid_paths_m()
        assert paths[4, 0] == pytest.approx(1.25, abs=1e-12)
        assert paths[4, 1] == pytest.approx(1.75, abs=1e-12)
        assert prop.geometric_divergence_corrections()[4] == pytest.approx(
            1.96, abs=1e-12
        )

    def test_the_grid_is_symmetric(self) -> None:
        corrections = prop.geometric_divergence_corrections()
        assert corrections[0] == pytest.approx(corrections[8])
        assert corrections[1] == pytest.approx(corrections[3])

    def test_the_sampled_area_of_note_1(self) -> None:
        radius = prop.reflection_sampled_area_radius_m(
            oracle.SAMPLED_AREA_WINDOW_S,
            speed_of_sound=oracle.SAMPLED_AREA_SPEED_M_S,
        )
        assert round(radius, 2) == pytest.approx(oracle.SAMPLED_AREA_RADIUS_M)

    def test_a_grid_behind_the_loudspeaker_is_refused(self) -> None:
        with pytest.raises(ValueError, match="'microphone_distance_m' must be smaller"):
            prop.reflection_grid_paths_m(source_distance_m=0.2)

    def test_the_results_refuse_writes(self) -> None:
        paths = prop.reflection_grid_paths_m()
        with pytest.raises(ValueError, match="read-only"):
            paths[0, 0] = 2.0


class TestAdrienneWindow:
    """5.5.5 and Formula (7)."""

    @pytest.mark.parametrize("length_s", sorted(oracle.WINDOW_PARTS_S))
    def test_the_three_printed_lengths(self, length_s: float) -> None:
        # At 100 kHz every printed length is a whole number of samples.
        fs = 100_000.0
        window = prop.adrienne_reflection_window(fs, length_s)
        lead, flat, trail = oracle.WINDOW_PARTS_S[length_s]
        assert window.size == round((lead + flat + trail) * fs)
        n_lead, n_flat = round(lead * fs), round(flat * fs)
        np.testing.assert_array_equal(window[n_lead : n_lead + n_flat], 1.0)
        assert np.all(window[:n_lead] < 1.0)
        assert np.all(window[n_lead + n_flat :] < 1.0)
        assert window[0] < 1e-3
        assert window[-1] < 1e-3

    def test_the_default_is_the_standard_length(self) -> None:
        assert prop.ADRIENNE_STANDARD_LENGTH_S == pytest.approx(7.9e-3)
        # Each part is rounded to whole samples: 24 + 249 + 107 at 48 kHz.
        assert prop.adrienne_reflection_window(_FS).size == 24 + 249 + 107

    def test_a_window_no_longer_than_its_leading_edge_is_refused(self) -> None:
        with pytest.raises(ValueError, match="'window_length_s' must exceed"):
            prop.adrienne_reflection_window(_FS, 0.4e-3)

    def test_the_notch_of_the_standard_window_is_about_160_hz(self) -> None:
        # Garai and Guidorzi (2000), III.D.4: about 160 Hz for 7,9 ms.
        notch = prop.adrienne_low_frequency_limit_hz(7.9e-3)
        assert notch == pytest.approx(162.55, abs=0.05)

    def test_the_notch_rises_as_the_window_shortens(self) -> None:
        notches = [
            prop.adrienne_low_frequency_limit_hz(t) for t in (7.9e-3, 6.0e-3, 1.3e-3)
        ]
        assert notches[0] < notches[1] < notches[2]
        assert notches[1] == pytest.approx(216.52, abs=0.05)

    def test_the_notch_is_a_minimum_of_the_sampled_window(self) -> None:
        # Independent of the closed form: a finely sampled window's spectrum.
        fs = 2_000_000.0
        window = prop.adrienne_reflection_window(fs, 7.9e-3)
        size = 1 << 23
        spectrum = np.abs(np.fft.rfft(window, n=size))
        freqs = np.fft.rfftfreq(size, 1.0 / fs)
        band = (freqs > 100.0) & (freqs < 250.0)
        sampled = float(freqs[band][np.argmin(spectrum[band])])
        assert sampled == pytest.approx(
            prop.adrienne_low_frequency_limit_hz(7.9e-3), abs=0.5
        )


class TestSubtraction:
    """5.5.4 and Formula (6)."""

    def test_a_sub_sample_shift_is_found_on_the_fiftieth_grid(self) -> None:
        front, free = _grid(reflection=0.5, shift=0.36)
        result = prop.subtract_direct_sound(front[4], free[4], _FS)
        assert result.shift_samples == pytest.approx(-0.36, abs=1e-12)
        assert result.amplitude_factor == pytest.approx(1.0, rel=1e-6)
        assert result.reduction_db > 60.0

    def test_the_residual_is_the_reflection(self) -> None:
        front, free = _grid(reflection=0.5)
        result = prop.subtract_direct_sound(front[4], free[4], _FS)
        paths = prop.reflection_grid_paths_m()
        expected = 0.5 * _pulse(_START + paths[4, 1] / _C * _FS, 1.0 / paths[4, 1])
        np.testing.assert_allclose(result.residual, expected, atol=1e-9)
        # Only rounding is left of the direct sound.
        assert result.reduction_db > 200.0

    def test_the_amplitude_is_matched_to_the_peak(self) -> None:
        front, free = _grid(reflection=0.5, gain=1.2)
        result = prop.subtract_direct_sound(front[4], free[4], _FS)
        assert result.amplitude_factor == pytest.approx(1.2, rel=1e-9)

    def test_the_reduction_factor_integrates_half_a_millisecond_each_side(
        self,
    ) -> None:
        # Formula (6): what is left within 0,5 ms of the peak (24 samples at
        # 48 kHz) counts, what is left beyond it does not.
        free = np.zeros(_N)
        free[1000] = 1.0
        front = free.copy()
        front[1010] = 0.01
        front[1036] = 0.05
        result = prop.subtract_direct_sound(front, free, _FS)
        assert result.shift_samples == pytest.approx(0.0, abs=1e-12)
        assert result.reduction_db == pytest.approx(40.0, abs=1e-9)

    def test_a_poor_subtraction_warns_below_10_db(self) -> None:
        front, _ = _grid(reflection=0.5)
        other = np.zeros(_N)
        paths = prop.reflection_grid_paths_m()
        other += _pulse(
            _START + paths[4, 0] / _C * _FS, 1.0 / paths[4, 0], width_s=0.12e-3
        )
        with pytest.warns(prop.BarrierReflectionWarning, match="R_sub"):
            prop.subtract_direct_sound(front[4], other, _FS)

    def test_a_calibrated_signal_comes_back_in_pascals(self) -> None:
        from phonometry.io import Signal

        front, free = _grid(reflection=0.5)
        bare = prop.subtract_direct_sound(2.0 * front[4], 2.0 * free[4], _FS)
        result = prop.subtract_direct_sound(
            Signal(front[4], int(_FS), calibration_factor=2.0),
            Signal(free[4], int(_FS), calibration_factor=2.0),
        )
        assert isinstance(result.residual, Signal)
        assert result.residual.calibration_factor == 1.0
        np.testing.assert_array_equal(np.asarray(result.residual), bare.residual)
        assert result.fs == pytest.approx(_FS)

    def test_a_missing_rate_is_refused(self) -> None:
        front, free = _grid()
        with pytest.raises(ValueError, match="fs is required when 'in_front_ir'"):
            prop.subtract_direct_sound(front[4], free[4])

    def test_records_of_different_length_are_refused(self) -> None:
        front, free = _grid()
        with pytest.raises(
            ValueError,
            match="'in_front_ir' and 'free_field_ir' must have the same length",
        ):
            prop.subtract_direct_sound(front[4], free[4, :-1], _FS)

    def test_a_low_sample_rate_warns(self) -> None:
        front, free = _grid()
        with pytest.warns(prop.BarrierReflectionWarning, match="44 kHz"):
            prop.subtract_direct_sound(front[4], free[4], 32000.0)


class TestReflectionIndex:
    """Formula (1) with Formulas (2) to (4)."""

    def test_a_perfect_reflector_is_one_in_every_band(self) -> None:
        front, free = _grid()
        result = _index(front, free)
        np.testing.assert_allclose(result.reflection_index, 1.0, atol=1e-6)
        np.testing.assert_allclose(result.gain_corrections, 1.0, atol=1e-9)

    def test_an_amplitude_r_is_r_squared(self) -> None:
        front, free = _grid(reflection=0.5)
        result = _index(front, free)
        np.testing.assert_allclose(result.reflection_index, 0.25, atol=1e-6)

    def test_a_gain_change_does_not_move_the_index(self) -> None:
        # Formula (4) measures the change and the index divides by it.
        front, free = _grid(reflection=0.5, gain=1.08, shift=0.4)
        result = _index(front, free)
        np.testing.assert_allclose(result.gain_corrections, 1.08**2, rtol=1e-6)
        np.testing.assert_allclose(result.reflection_index, 0.25, atol=1e-5)

    def test_a_gain_change_above_20_percent_warns(self) -> None:
        front, free = _grid(reflection=0.5, gain=1.2)
        with pytest.warns(prop.BarrierReflectionWarning, match="20 %"):
            _index(front, free)

    def test_the_directivity_correction_multiplies(self) -> None:
        front, free = _grid(reflection=0.5)
        directivity = np.full((9, _BANDS), 1.2)
        result = _index(front, free, directivity_corrections=directivity)
        np.testing.assert_allclose(result.reflection_index, 0.3, atol=1e-6)

    def test_a_two_impulse_reflection_is_the_comb_of_its_bands(self) -> None:
        # Each band integrates its own comb between its exact base-ten edges.
        delay_s = 24 / _FS
        front, free = _impulse_grid(reflection=0.5, taps=(0, 24))
        result = _index(front, free)
        np.testing.assert_allclose(
            result.reflection_index, _comb(0.5, delay_s), atol=1e-6
        )
        assert np.ptp(result.reflection_index) > 0.5

    def test_the_long_window_serves_only_the_three_low_bands(self) -> None:
        # An impulse 6 ms after the reflection is outside the 6,0 ms window
        # and inside the tail of the 7,9 ms one (5.5.5).
        front, free = _impulse_grid(reflection=0.5, late_s=6.0e-3)
        result = _index(front, free)
        np.testing.assert_allclose(result.reflection_index[3:], 0.25, atol=1e-12)
        assert np.all(np.abs(result.reflection_index[:3] - 0.25) > 1e-3)

    def test_a_directivity_correction_lands_on_its_own_band(self) -> None:
        front, free = _impulse_grid(reflection=0.5)
        directivity = np.ones((9, _BANDS))
        directivity[:, 5] = 2.0
        result = _index(front, free, directivity_corrections=directivity)
        expected = np.full(_BANDS, 0.25)
        expected[5] = 0.5
        np.testing.assert_allclose(result.reflection_index, expected, atol=1e-12)

    def test_the_speed_of_sound_has_no_default(self) -> None:
        # 5.5.6 and 5.7.3 ask for the value at the temperature of the test.
        front, free = _grid()
        with pytest.raises(TypeError, match="speed_of_sound"):
            prop.reflection_index(front, free, _FS)  # type: ignore[call-arg]

    def test_the_low_bands_average_microphones_1_to_6(self) -> None:
        front, free = _grid(reflection=0.5)
        result = _index(front, free)
        assert result.microphone_values is not None
        low = result.microphone_values[0, :, :3]
        assert np.all(np.isnan(low[6:]))
        assert np.all(np.isfinite(low[:6]))
        assert np.all(np.isfinite(result.microphone_values[0, :, 3:]))

    def test_several_positions_average_every_partial_result(self) -> None:
        front, free = _grid(reflection=0.5)
        front2, free2 = _grid(reflection=0.3)
        result = _index(np.stack([front, front2]), np.stack([free, free2]))
        np.testing.assert_allclose(result.position_values[0], 0.25, atol=1e-6)
        np.testing.assert_allclose(result.position_values[1], 0.09, atol=1e-6)
        np.testing.assert_allclose(result.reflection_index, 0.17, atol=1e-6)

    def test_the_rating_starts_at_the_lowest_band(self) -> None:
        front, free = _grid(reflection=0.5)
        result = _index(front, free, lowest_band_hz=400.0)
        assert result.rating.lowest_band_hz == pytest.approx(400.0)
        assert result.rating.rating == pytest.approx(-10.0 * math.log10(0.25), abs=1e-4)

    def test_the_window_lengths_can_be_given_per_microphone(self) -> None:
        front, free = _grid(reflection=0.5)
        lengths = [5.0e-3] * 3 + [6.0e-3] * 6
        result = _index(front, free, window_length_s=lengths)
        np.testing.assert_allclose(result.reflection_index, 0.25, atol=1e-6)

    def test_a_record_too_short_for_the_window_is_refused(self) -> None:
        front, free = _grid()
        with pytest.raises(
            ValueError, match="the Adrienne window of the .* outside the record"
        ):
            _index(front[:, :700], free[:, :700])

    def test_a_record_that_is_not_nine_microphones_is_refused(self) -> None:
        front, free = _grid()
        with pytest.raises(ValueError, match="'in_front_irs' must be shaped"):
            _index(front[:8], free[:8])

    def test_mismatched_shapes_are_refused(self) -> None:
        front, free = _grid()
        with pytest.raises(
            ValueError,
            match="'in_front_irs' and 'free_field_irs' must have the same shape",
        ):
            _index(front, free[:, :-1])

    def test_a_directivity_array_of_the_wrong_shape_is_refused(self) -> None:
        front, free = _grid()
        with pytest.raises(ValueError, match="'directivity_corrections' must be a"):
            _index(front, free, directivity_corrections=np.ones((9, 17)))

    def test_nine_window_lengths_or_one(self) -> None:
        front, free = _grid()
        with pytest.raises(
            ValueError, match="'window_length_s' must be one length or nine"
        ):
            _index(front, free, window_length_s=[6.0e-3, 6.0e-3])

    def test_an_unknown_low_band_microphone_is_refused(self) -> None:
        front, free = _grid()
        with pytest.raises(ValueError, match="'low_band_microphones' must name"):
            _index(front, free, low_band_microphones=(0, 1))


class TestSignalContract:
    """The records arrive as Signals: the rate and the calibration go with them."""

    def test_a_nine_channel_signal_is_one_grid_position(self) -> None:
        from phonometry.io import Signal

        front, free = _grid(reflection=0.5)
        bare = _index(front, free)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", prop.RoadDeviceWarning)
            result = prop.reflection_index(
                Signal(front, int(_FS)), Signal(free, int(_FS)), speed_of_sound=_C
            )
        np.testing.assert_array_equal(result.reflection_index, bare.reflection_index)
        np.testing.assert_array_equal(result.gain_corrections, bare.gain_corrections)

    def test_a_sequence_of_signals_is_one_per_position(self) -> None:
        from phonometry.io import Signal

        front, free = _grid(reflection=0.5)
        front2, free2 = _grid(reflection=0.3)
        bare = _index(np.stack([front, front2]), np.stack([free, free2]))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", prop.RoadDeviceWarning)
            result = prop.reflection_index(
                [Signal(front, int(_FS)), Signal(front2, int(_FS))],
                [free, free2],
                speed_of_sound=_C,
            )
        np.testing.assert_array_equal(result.position_values, bare.position_values)

    def test_the_calibration_is_applied_before_the_gain_check(self) -> None:
        # Raw samples 1/1.3 of the free-field ones, calibrated back by 1.3:
        # no gain changed between the two configurations, and none is found.
        from phonometry.io import Signal

        front, free = _grid(reflection=0.5)
        calibrated = Signal(front / 1.3, int(_FS), calibration_factor=1.3)
        with warnings.catch_warnings():
            warnings.simplefilter("error", prop.BarrierReflectionWarning)
            warnings.simplefilter("ignore", prop.RoadDeviceWarning)
            result = prop.reflection_index(calibrated, free, speed_of_sound=_C)
        np.testing.assert_allclose(result.gain_corrections, 1.0, rtol=1e-12)
        np.testing.assert_allclose(result.reflection_index, 0.25, atol=1e-6)

    def test_a_rate_that_disagrees_with_the_signal_is_refused(self) -> None:
        from phonometry.io import Signal

        front, free = _grid()
        records = Signal(front, int(_FS)), Signal(free, int(_FS))
        with pytest.raises(ValueError, match="conflicts with the Signal's own fs"):
            prop.reflection_index(*records, 2 * _FS, speed_of_sound=_C)

    def test_signals_at_two_rates_are_refused(self) -> None:
        from phonometry.io import Signal

        front, free = _grid()
        records = Signal(front, int(_FS)), Signal(free, int(2 * _FS))
        with pytest.raises(ValueError, match="are Signals recorded at different rates"):
            prop.reflection_index(*records, speed_of_sound=_C)

    def test_a_sequence_mixing_signals_and_numbers_is_refused(self) -> None:
        from phonometry.io import Signal

        front, free = _grid()
        mixed = [Signal(front, int(_FS)), 0.0]
        with pytest.raises(
            ValueError, match="'in_front_irs' mixes Signals with bare numbers"
        ):
            prop.reflection_index(mixed, free, speed_of_sound=_C)  # type: ignore[arg-type]

    def test_several_positions_of_eight_microphones_are_refused(self) -> None:
        front, free = _grid()
        fronts, frees = np.stack([front[:8]] * 2), np.stack([free[:8]] * 2)
        with pytest.raises(ValueError, match="'in_front_irs' must be shaped"):
            _index(fronts, frees)

    def test_bare_arrays_need_a_rate(self) -> None:
        front, free = _grid()
        with pytest.raises(
            ValueError, match="fs is required when 'in_front_irs' and 'free_field_irs'"
        ):
            prop.reflection_index(front, free, speed_of_sound=_C)

    def test_the_directivity_records_take_the_rate_from_a_signal(self) -> None:
        from phonometry.io import Signal

        _, free = _grid()
        bare = prop.source_directivity_corrections(free, 0.9 * free, _FS)
        result = prop.source_directivity_corrections(
            Signal(free, int(_FS)), Signal(0.9 * free, int(_FS))
        )
        np.testing.assert_array_equal(result, bare)

    def test_the_directivity_records_apply_their_calibration(self) -> None:
        from phonometry.io import Signal

        _, free = _grid()
        result = prop.source_directivity_corrections(
            free, Signal(free, int(_FS), calibration_factor=0.9)
        )
        np.testing.assert_allclose(result, 1.0 / 0.81, rtol=1e-9)

    def test_directivity_records_at_two_rates_are_refused(self) -> None:
        from phonometry.io import Signal

        _, free = _grid()
        records = Signal(free, int(_FS)), Signal(free, int(2 * _FS))
        with pytest.raises(
            ValueError,
            match="'microphone_irs' and 'specular_irs' are Signals recorded at different",
        ):
            prop.source_directivity_corrections(*records)


class TestDirectivity:
    """Formula (3)."""

    def test_the_same_record_twice_is_one(self) -> None:
        _, free = _grid()
        corrections = prop.source_directivity_corrections(free, free, _FS)
        np.testing.assert_allclose(corrections, 1.0, atol=1e-12)
        assert corrections.shape == (9, _BANDS)

    def test_a_weaker_specular_direction_is_its_energy_ratio(self) -> None:
        _, free = _grid()
        corrections = prop.source_directivity_corrections(free, 0.9 * free, _FS)
        np.testing.assert_allclose(corrections, 1.0 / 0.81, rtol=1e-9)

    def test_the_two_sets_must_match(self) -> None:
        _, free = _grid()
        with pytest.raises(
            ValueError,
            match="'microphone_irs' and 'specular_irs' must have the same shape",
        ):
            prop.source_directivity_corrections(free, free[:, :-1], _FS)


class TestAnnexB:
    """Tables B.1 and B.2."""

    def _positions(self) -> np.ndarray:
        return np.asarray(oracle.TABLE_B1_POSITIONS).T

    def test_the_average_column(self) -> None:
        result = prop.reflection_index_from_positions(self._positions())
        for band, mean, printed in zip(
            oracle.TABLE_B1_BANDS_HZ,
            result.reflection_index,
            oracle.TABLE_B1_AVERAGE,
            strict=True,
        ):
            if band in oracle.TABLE_B1_TIED_BANDS_HZ:
                assert abs(mean - printed) == pytest.approx(0.005, abs=1e-12)
            else:
                assert round(float(mean), 2) == pytest.approx(printed), band

    def test_the_rating_of_the_printed_averages(self) -> None:
        rating = prop.sound_reflection_rating(
            oracle.TABLE_B1_AVERAGE, lowest_band_hz=oracle.TABLE_B1_LOWEST_BAND_HZ
        )
        assert round(rating.rating, 2) == pytest.approx(oracle.TABLE_B2_RATING_DB)
        assert rating.reported == oracle.TABLE_B1_RATING_DB
        assert rating.category is None

    def test_the_rating_of_the_particular_values(self) -> None:
        # Formula (12) on the unrounded means of the particular values gives
        # 7,65 dB; Table B.2 prints 7,68 dB, which is Formula (12) on the
        # averages rounded to two decimals (5.11), as the test above shows.
        result = prop.reflection_index_from_positions(self._positions())
        assert round(result.rating.rating, 2) == pytest.approx(7.65)
        assert result.rating.reported == oracle.TABLE_B1_RATING_DB
        assert result.lowest_band_hz == pytest.approx(200.0)

    def test_table_b2_from_table_a1(self) -> None:
        result = prop.reflection_index_from_positions(self._positions())
        per_band, rating = result.expanded_uncertainty()
        high = [
            prop.REFLECTION_INDEX_PRECISION[band]["reproducibility"][2]
            for band in prop.TRAFFIC_NOISE_BANDS_HZ
        ]
        assert tuple(high) == oracle.TABLE_B2_REPRODUCIBILITY
        for band, value, printed in zip(
            oracle.TABLE_B1_BANDS_HZ, per_band, oracle.TABLE_B2_EXPANDED, strict=True
        ):
            if band in oracle.TABLE_B2_LOW_CELLS_HZ:
                # Printed a hundredth below the product, as unrounded sR
                # would give; the print does not say (docs/ERRATA.md).
                assert round(float(value), 2) == pytest.approx(printed + 0.01)
            else:
                assert round(float(value), 2) == pytest.approx(printed), band
        assert rating == pytest.approx(
            oracle.TABLE_B2_COVERAGE_FACTOR * oracle.TABLE_B2_RATING_REPRODUCIBILITY_DB
        )
        assert round(rating, 2) == pytest.approx(oracle.TABLE_B2_RATING_EXPANDED_DB)
        low, high_end = oracle.TABLE_B2_RATING_INTERVAL_DB
        assert round(oracle.TABLE_B2_RATING_DB - rating, 2) == pytest.approx(low)
        assert round(oracle.TABLE_B2_RATING_DB + rating, 2) == pytest.approx(high_end)

    def test_the_other_columns_of_table_a1(self) -> None:
        result = prop.reflection_index_from_positions(self._positions())
        median, rating = result.expanded_uncertainty(
            estimate="median", coverage_factor=2.0
        )
        assert median[0] == pytest.approx(2.0 * 0.27)
        assert rating == pytest.approx(2.0 * 0.68)

    def test_an_unknown_column_is_refused(self) -> None:
        result = prop.reflection_index_from_positions(self._positions())
        with pytest.raises(ValueError, match="'estimate' must be one of"):
            result.expanded_uncertainty(estimate="mean")  # type: ignore[arg-type]

    def test_a_band_left_unmeasured_is_left_out(self) -> None:
        values = self._positions().copy()
        values[0, 0] = np.nan
        result = prop.reflection_index_from_positions(values)
        assert result.reflection_index[0] == pytest.approx(np.mean(values[1:, 0]))

    def test_a_negative_index_is_refused(self) -> None:
        values = self._positions().copy()
        values[0, 5] = -0.1
        with pytest.raises(ValueError, match="'position_values' must be non-negative"):
            prop.reflection_index_from_positions(values)

    def test_seventeen_bands_are_refused(self) -> None:
        values = self._positions()[:, :17]
        with pytest.raises(ValueError, match="'position_values' must have"):
            prop.reflection_index_from_positions(values)


class TestRating:
    """Formula (12)."""

    def test_a_constant_index_rates_its_logarithm(self) -> None:
        rating = prop.sound_reflection_rating(np.full(_BANDS, 0.1))
        assert rating.rating == pytest.approx(10.0, abs=1e-12)
        assert rating.quantity == "reflection"

    def test_the_ratio_is_capped_at_0_99(self) -> None:
        with pytest.warns(prop.RoadDeviceWarning, match="0.99"):
            rating = prop.sound_reflection_rating(np.full(_BANDS, 1.2))
        assert rating.rating == pytest.approx(-10.0 * math.log10(0.99))

    @pytest.mark.parametrize("lowest_band_hz", [500.0, 630.0, 1250.0, 2000.0])
    def test_a_ratio_of_0_99_in_decimal_is_not_above_the_limit(
        self, lowest_band_hz: float
    ) -> None:
        # Every index read as 0,99 weighs to 0,99 exactly in decimal; from
        # these bands the energy mean comes out one or two units in the last
        # place above it in binary. Clause 5.8 limits the ratio to a maximum
        # of 0,99, which this ratio does not pass, so nothing is limited.
        values = np.full(_BANDS, 0.99)
        first = prop.TRAFFIC_NOISE_BANDS_HZ.index(lowest_band_hz)
        values[:first] = np.nan
        with warnings.catch_warnings():
            warnings.simplefilter("error", prop.RoadDeviceWarning)
            rating = prop.sound_reflection_rating(values, lowest_band_hz=lowest_band_hz)
        assert rating.rating == pytest.approx(-10.0 * math.log10(0.99))

    def test_a_ratio_a_thousandth_above_the_limit_is_limited(self) -> None:
        with pytest.warns(prop.RoadDeviceWarning, match="0.99 limit"):
            rating = prop.sound_reflection_rating(np.full(_BANDS, 0.991))
        assert rating.rating == pytest.approx(-10.0 * math.log10(0.99))

    def test_bands_below_the_lowest_may_be_missing(self) -> None:
        values = np.full(_BANDS, 0.2)
        values[:6] = np.nan
        rating = prop.sound_reflection_rating(values, lowest_band_hz=400.0)
        assert rating.rating == pytest.approx(-10.0 * math.log10(0.2))

    def test_a_missing_band_above_the_lowest_is_refused(self) -> None:
        values = np.full(_BANDS, 0.2)
        values[4] = np.nan
        with pytest.raises(ValueError, match="reflection_indices must be finite"):
            prop.sound_reflection_rating(values, lowest_band_hz=200.0)

    def test_the_lowest_band_is_a_band_centre(self) -> None:
        with pytest.raises(
            ValueError, match="lowest_band_hz must be one of the band centres"
        ):
            prop.sound_reflection_rating(np.full(_BANDS, 0.2), lowest_band_hz=210.0)

    @pytest.mark.parametrize("lowest_band_hz", [-200.0, 0.0, math.inf])
    def test_the_lowest_band_is_positive_before_any_logarithm(
        self, lowest_band_hz: float
    ) -> None:
        values = np.full(_BANDS, 0.2)
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            with pytest.raises(ValueError, match="'lowest_band_hz' must be positive"):
                prop.sound_reflection_rating(values, lowest_band_hz=lowest_band_hz)

    def test_a_perfect_absorber_has_no_finite_rating(self) -> None:
        with pytest.raises(ValueError, match="the weighted reflection ratio is zero"):
            prop.sound_reflection_rating(np.zeros(_BANDS))

    def test_eighteen_values_are_required(self) -> None:
        with pytest.raises(ValueError, match="reflection_indices must cover the"):
            prop.sound_reflection_rating(np.full(10, 0.2))


class TestLowFrequencyLimit:
    """5.5.7, by the construction of Garai and Guidorzi."""

    def test_microphone_5_of_a_4_m_sample_is_about_170_hz(self) -> None:
        limit = prop.reflection_low_frequency_limit(4.0, speed_of_sound=340.0)
        assert limit.low_frequency_limit_hz[4] == pytest.approx(
            oracle.LOW_FREQUENCY_LIMITS_4M_HZ[5], rel=0.02
        )
        assert limit.limiting_component[4] == "ground"

    def test_the_window_ends_at_the_ground_reflection(self) -> None:
        limit = prop.reflection_low_frequency_limit(4.0, speed_of_sound=340.0)
        ground = math.hypot(1.25, 4.0)
        assert limit.window_length_s[4] == pytest.approx(
            0.5e-3 + (ground - 1.75) / 340.0
        )

    def test_the_top_edge_sets_the_window_of_microphone_2(self) -> None:
        # Over the top edge of a 4 m device: 2 m above the loudspeaker, 1,6 m
        # above microphone 2, which is 0,4 m off the specular plane of 5.
        limit = prop.reflection_low_frequency_limit(4.0, speed_of_sound=340.0)
        top_edge = math.hypot(1.5, 2.0) + math.hypot(0.25, 1.6)
        specular = math.hypot(1.75, 0.4)
        assert limit.window_length_s[1] == pytest.approx(
            0.5e-3 + (top_edge - specular) / 340.0
        )

    def test_a_side_edge_sets_the_window_of_microphone_4(self) -> None:
        # A 2 m sample: its left edge is 1 m from the loudspeaker axis and
        # 0,6 m from microphone 4, at the loudspeaker's height.
        limit = prop.reflection_low_frequency_limit(
            6.0, speed_of_sound=343.0, device_length_m=2.0
        )
        side_edge = math.hypot(1.5, 1.0) + math.hypot(0.25, 0.6)
        specular = math.hypot(1.75, 0.4)
        assert limit.limiting_component[3] == "side edge"
        assert limit.window_length_s[3] == pytest.approx(
            0.5e-3 + (side_edge - specular) / 343.0
        )

    def test_the_4_m_sample_of_the_guide(self) -> None:
        limit = prop.reflection_low_frequency_limit(4.0, speed_of_sound=340.0)
        np.testing.assert_array_equal(
            limit.low_frequency_limit_hz[[1, 4, 7]].round(), [176.0, 167.0, 201.0]
        )

    def test_the_top_row_is_limited_by_the_top_edge(self) -> None:
        limit = prop.reflection_low_frequency_limit(4.0, speed_of_sound=340.0)
        assert limit.limiting_component[:3] == ("top edge",) * 3
        assert limit.limiting_component[6:] == ("ground",) * 3

    def test_the_bottom_row_is_the_highest_limit(self) -> None:
        limit = prop.reflection_low_frequency_limit(3.5, speed_of_sound=343.0)
        assert int(np.argmax(limit.low_frequency_limit_hz)) in (6, 8)

    def test_a_taller_device_measures_lower(self) -> None:
        low = prop.reflection_low_frequency_limit(6.0, speed_of_sound=343.0)
        high = prop.reflection_low_frequency_limit(3.0, speed_of_sound=343.0)
        assert np.all(low.low_frequency_limit_hz < high.low_frequency_limit_hz)

    def test_a_narrow_sample_is_limited_by_its_side_edges(self) -> None:
        limit = prop.reflection_low_frequency_limit(
            6.0, speed_of_sound=343.0, device_length_m=2.0
        )
        assert "side edge" in limit.limiting_component

    def test_a_device_too_small_for_the_grid_is_refused(self) -> None:
        with pytest.raises(
            ValueError, match="the grid, .* must fit between the ground"
        ):
            prop.reflection_low_frequency_limit(0.7, speed_of_sound=343.0)

    def test_a_device_whose_ground_reflection_comes_first_is_refused(self) -> None:
        # At 1,5 m the bottom row hears the ground before the device.
        with pytest.raises(ValueError, match="too low for the grid"):
            prop.reflection_low_frequency_limit(1.5, speed_of_sound=343.0)

    def test_a_sample_narrower_than_the_grid_is_refused(self) -> None:
        with pytest.raises(ValueError, match="sample is narrower than the"):
            prop.reflection_low_frequency_limit(
                4.0, speed_of_sound=343.0, device_length_m=0.6
            )


class TestFigure14:
    """The construction against the curves read off Figure 14 (5.5.7)."""

    @staticmethod
    def _gaps(microphone: int) -> list[tuple[float, float]]:
        """``(height, model / curve - 1)`` at each height read off the curve."""
        gaps = []
        for height, printed in oracle.FIGURE_14_HZ[microphone]:
            limit = prop.reflection_low_frequency_limit(height, speed_of_sound=340.0)
            gaps.append(
                (
                    height,
                    float(limit.low_frequency_limit_hz[microphone - 1]) / printed - 1.0,
                )
            )
        return gaps

    def test_microphone_5_follows_its_curve(self) -> None:
        for height, gap in self._gaps(5):
            if height >= 2.75:
                assert abs(gap) < 0.05, height
        assert self._gaps(5)[0][1] == pytest.approx(-0.055, abs=0.005)

    def test_microphone_2_comes_out_above_its_curve(self) -> None:
        gaps = [gap for _, gap in self._gaps(2)]
        assert min(gaps) > 0.02
        assert max(gaps) < 0.11

    def test_microphone_8_comes_out_below_its_curve(self) -> None:
        gaps = dict(self._gaps(8))
        assert gaps[2.5] == pytest.approx(-1.0 / 3.0, abs=0.03)
        assert gaps[4.5] == pytest.approx(-0.06, abs=0.01)
        for height, gap in gaps.items():
            assert gap < 0.0, height
            if height >= 6.0:
                assert gap > -0.035, height


class TestPositionChecks:
    """5.6.2.5 and 5.6.2.6 against Table 3."""

    def test_the_nominal_delays_pass(self) -> None:
        delays = np.array([dk for _, dk in oracle.TABLE_3]) / _C
        check = prop.check_reflection_grid_position(delays, speed_of_sound=_C)
        assert check.passes
        np.testing.assert_allclose(check.deviations_m, 0.0, atol=1e-12)

    def test_26_mm_off_fails(self) -> None:
        distances = np.array([dk for _, dk in oracle.TABLE_3])
        distances[6] += 0.026
        check = prop.check_reflection_grid_position(distances / _C, speed_of_sound=_C)
        assert not check.passes
        assert list(np.flatnonzero(~check.within)) == [6]

    def test_the_relative_check_leaves_out_microphone_5(self) -> None:
        distances = np.array([dk5 for dk5, _ in oracle.TABLE_3])
        distances[4] = 0.4
        check = prop.check_reflection_grid_position(
            distances / _C, speed_of_sound=_C, check="relative"
        )
        assert check.passes
        assert check.check == "relative"

    def test_the_verdict_has_no_truth_value(self) -> None:
        delays = np.array([dk for _, dk in oracle.TABLE_3]) / _C
        check = prop.check_reflection_grid_position(delays, speed_of_sound=_C)
        with pytest.raises(TypeError, match="has no truth value"):
            bool(check)

    def test_eight_delays_are_refused(self) -> None:
        with pytest.raises(
            ValueError, match="'time_delays_s' must hold nine finite delays"
        ):
            prop.check_reflection_grid_position(np.zeros(8), speed_of_sound=_C)


def test_the_module_publishes_what_it_says() -> None:
    for name in br.__all__:
        assert getattr(prop, name) is getattr(br, name)
