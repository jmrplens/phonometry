#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ECMA-418-2:2025 (Sottek Hearing Model) loudness conformance tests.

The primary oracle is the standard's own calibration (Clause 5.1.8): a
1 kHz sinusoid at 40 dB SPL yields 1 sone_HMS via the Clause 8 method. The
standard ships no reference WAVs and its Annex A is graphical only, so the
remaining checks are internal consistency properties the standard implies
(monotonicity in level, silence, field/resampling handling, structure).

The total basis loudness N_basis of Formula 26 has no printed value either.
It is held to a closed form instead: for a steady tone whose period is a
whole number of samples, every block of every band holds whole periods, so
the RMS of Formula 22 is the band output's RMS exactly and N'_basis(z) of
Formula 25 follows from the steady-state response of the printed filters.
:func:`_steady_state_basis_loudness` computes it from the printed tables and
formulas alone, never from the code under test.
"""

import cmath
import math
from collections.abc import Sequence

import numpy as np
import pytest
from reference_data import (
    ECMA418_2_BANDWIDTH_C,
    ECMA418_2_DELTA_F0_HZ,
    ECMA418_2_DZ,
    ECMA418_2_EAR_FILTER_FREE_FIELD,
    ECMA418_2_FILTER_E,
    ECMA418_2_FILTER_ORDER,
    ECMA418_2_LOUDNESS_C_N,
    ECMA418_2_LTQ,
    ECMA418_2_NONLINEARITY_ALPHA,
    ECMA418_2_NONLINEARITY_EXPONENTS,
    ECMA418_2_NONLINEARITY_LEVELS_DB,
)

from phonometry import psychoacoustics

FS = 48000


def _tone(freq: float, level: float, seconds: float = 1.2) -> np.ndarray:
    """Pure tone at an SPL (dB re 20 uPa), pressure in pascals."""
    t = np.arange(int(FS * seconds)) / FS
    amp = np.sqrt(2.0) * 2e-5 * 10 ** (level / 20.0)
    return amp * np.sin(2.0 * np.pi * freq * t)


@pytest.fixture(scope="module")
def ref_1k_40() -> psychoacoustics.EcmaLoudness:
    """The calibration signal result, computed once for the module."""
    return psychoacoustics.loudness_ecma(_tone(1000.0, 40.0), FS)


# --------------------------------------------------------------------------
# Primary reference value (Clause 5.1.8 calibration)
# --------------------------------------------------------------------------


@pytest.mark.xdist_group("ecma-loudness-ref")
def test_calibration_1khz_40db_is_one_sone(
    ref_1k_40: psychoacoustics.EcmaLoudness,
) -> None:
    # c_N is defined so the 1 kHz / 40 dB tone gives 1 sone_HMS. With the
    # full Clause 6.2.3 band averaging this chain computes 0.9845 sone_HMS;
    # the -1.55 % residual (outside the +/-0.25 % c_N allowance) comes from
    # the mandated averaging around the block-size-boundary bands and is
    # documented in the module docstring -- c_N stays the verbatim constant.
    assert ref_1k_40.loudness == pytest.approx(1.0, abs=0.03)
    # Regression pin of the deterministic chain value (not a standard target).
    assert ref_1k_40.loudness == pytest.approx(0.9845, abs=0.005)


def test_calibration_constant_is_the_tabulated_c_n() -> None:
    # Clause 5.1.8 tabulates c_N = 0.0211964; the implementation must use the
    # standard's value verbatim (shared oracle in tests/reference_data/).
    from reference_data import ECMA418_2_LOUDNESS_C_N

    from phonometry.psychoacoustics.loudness.ecma import _C_N

    assert _C_N == ECMA418_2_LOUDNESS_C_N


# --------------------------------------------------------------------------
# Internal cross-checks
# --------------------------------------------------------------------------


def test_monotonic_in_level() -> None:
    # Monotonicity is level-driven, not duration-driven: 0.6 s segments and
    # three levels suffice (the 0.6 s / 40 dB anchor also holds 1 sone within
    # 3 % in the CI conformance check, which uses the same duration).
    values = [
        psychoacoustics.loudness_ecma(_tone(1000.0, lvl, seconds=0.6), FS).loudness
        for lvl in (20, 40, 80)
    ]
    assert values[0] < values[1] < values[2]
    # 40 dB is the 1-sone anchor; higher levels are clearly louder.
    assert values[1] == pytest.approx(1.0, abs=0.03)
    assert values[2] > 5.0


def test_silence_is_zero() -> None:
    # Pure-property check: zero in, zero out at any length past the
    # transient-discard window, so 0.6 s is enough.
    result = psychoacoustics.loudness_ecma(np.zeros(int(FS * 0.6)), FS)
    assert result.loudness == 0.0
    assert np.all(result.specific_loudness == 0.0)
    assert np.all(result.basis_loudness_vs_time == 0.0)


def test_subthreshold_tone_is_inaudible() -> None:
    # A 1 kHz tone at -10 dB SPL is well below the threshold in quiet, and
    # its total basis loudness stays below the audibility criterion of
    # Clause 5.1.9 in every block.
    result = psychoacoustics.loudness_ecma(_tone(1000.0, -10.0, seconds=0.6), FS)
    assert result.loudness < 0.01
    assert np.all(
        result.basis_loudness_vs_time <= psychoacoustics.AUDIBILITY_THRESHOLD_SONE_HMS
    )


@pytest.mark.xdist_group("ecma-loudness-ref")
def test_specific_loudness_peaks_near_tone(
    ref_1k_40: psychoacoustics.EcmaLoudness,
) -> None:
    peak_band = int(np.argmax(ref_1k_40.specific_loudness))
    assert ref_1k_40.frequencies[peak_band] == pytest.approx(1000.0, rel=0.15)


# --------------------------------------------------------------------------
# Field handling and resampling
# --------------------------------------------------------------------------


def test_free_and_diffuse_fields_differ() -> None:
    # Property check (ear-filter difference), not a calibration: 0.6 s is
    # enough for a stable value in both fields.
    x = _tone(1000.0, 60.0, seconds=0.6)
    free = psychoacoustics.loudness_ecma(x, FS, field="free").loudness
    diffuse = psychoacoustics.loudness_ecma(x, FS, field="diffuse").loudness
    # Both plausible loudspeaker-range values, but the ear filter differs.
    assert free > 1.0
    assert diffuse > 1.0
    assert free != diffuse


def test_resampling_matches_native_rate() -> None:
    fs_alt = 44100
    t = np.arange(int(fs_alt * 0.6)) / fs_alt
    amp = np.sqrt(2.0) * 2e-5 * 10 ** (40.0 / 20.0)
    x = amp * np.sin(2.0 * np.pi * 1000.0 * t)
    resampled = psychoacoustics.loudness_ecma(x, fs_alt).loudness
    assert resampled == pytest.approx(1.0, abs=0.05)


# --------------------------------------------------------------------------
# Result structure and validation
# --------------------------------------------------------------------------


@pytest.mark.xdist_group("ecma-loudness-ref")
def test_result_structure(ref_1k_40: psychoacoustics.EcmaLoudness) -> None:
    assert ref_1k_40.specific_loudness.shape == (53,)
    assert ref_1k_40.bark.shape == (53,)
    assert ref_1k_40.bark[0] == pytest.approx(0.5)
    assert ref_1k_40.bark[-1] == pytest.approx(26.5)
    assert ref_1k_40.frequencies.shape == (53,)
    assert ref_1k_40.times.shape == ref_1k_40.loudness_vs_time.shape
    assert ref_1k_40.times.shape == ref_1k_40.basis_loudness_vs_time.shape
    # l_end of Formula 40 for the 1.2 s tone: ceil(57600 / 48000 * 187.5).
    assert ref_1k_40.last_evaluated_block == 225
    assert ref_1k_40.last_evaluated_block < ref_1k_40.times.size - 1
    assert ref_1k_40.field == "free"
    # Time-dependent loudness is sampled at 187.5 Hz (Clause 6.2.6).
    dt = np.diff(ref_1k_40.times)
    assert np.allclose(dt, 1.0 / 187.5)


@pytest.mark.xdist_group("ecma-loudness-ref")
def test_a_basis_loudness_that_disagrees_with_its_time_axis_is_refused(
    ref_1k_40: psychoacoustics.EcmaLoudness,
) -> None:
    """N_basis(l) is read against ``times`` index for index, so both are one axis."""
    import dataclasses

    trace = ref_1k_40.basis_loudness_vs_time
    for wrong in (trace[:-1], np.append(trace, trace[-1])):
        with pytest.raises(
            ValueError,
            match=r"'basis_loudness_vs_time' \(\d+\) must each carry one value",
        ):
            dataclasses.replace(ref_1k_40, basis_loudness_vs_time=wrong)


@pytest.mark.xdist_group("ecma-loudness-ref")
def test_a_last_evaluated_block_off_the_time_axis_is_refused(
    ref_1k_40: psychoacoustics.EcmaLoudness,
) -> None:
    """l_end indexes ``times``: one past its end would read the padding too."""
    import dataclasses

    last = ref_1k_40.times.size - 1
    kept = dataclasses.replace(ref_1k_40, last_evaluated_block=last)
    assert kept.last_evaluated_block == last
    for wrong in (last + 1, -1):
        with pytest.raises(ValueError, match=r"'last_evaluated_block'"):
            dataclasses.replace(ref_1k_40, last_evaluated_block=wrong)
    with pytest.raises(TypeError, match=r"'last_evaluated_block' must be a whole"):
        dataclasses.replace(ref_1k_40, last_evaluated_block=True)


def test_invalid_field() -> None:
    tone = _tone(1000.0, 40.0, seconds=0.5)
    with pytest.raises(ValueError, match="'field' must be one of"):
        psychoacoustics.loudness_ecma(tone, FS, field="reverberant")


def test_invalid_fs() -> None:
    tone = _tone(1000.0, 40.0, seconds=0.5)
    with pytest.raises(ValueError, match="fs must be positive"):
        psychoacoustics.loudness_ecma(tone, 0.0)


def test_empty_signal() -> None:
    empty = np.array([])
    with pytest.raises(ValueError, match="'x' must not be empty"):
        psychoacoustics.loudness_ecma(empty, FS)


def test_non_finite_signal_raises() -> None:
    # A poisoned sample must raise, not silently truncate the signal at the
    # poison index (NaN fails the half-wave rectification comparison).
    tone = _tone(1000.0, 40.0, seconds=0.5)
    tone[100] = np.nan
    with pytest.raises(ValueError, match="'x' must contain only finite samples"):
        psychoacoustics.loudness_ecma(tone, FS)


def test_resample_length_clamps_to_one_sample() -> None:
    # 1 sample at 96 kHz resamples to round(1 * 48000 / 96000) = round(0.5),
    # which banker's rounding takes to 0 samples without the clamp; the
    # clamped 1-sample signal must process cleanly.
    res = psychoacoustics.loudness_ecma(np.zeros(1), 96000.0)
    assert res.loudness == 0.0


@pytest.mark.xdist_group("ecma-loudness-ref")
def test_plot_smoke(ref_1k_40: psychoacoustics.EcmaLoudness) -> None:
    import matplotlib as mpl

    mpl.use("Agg")
    axes = ref_1k_40.plot()
    assert len(axes) == 2


# --------------------------------------------------------------------------
# Vectorized-kernel equivalence (bitwise) against retained reference loops
# --------------------------------------------------------------------------


def _reference_band_acf(rect: np.ndarray, s_b: int) -> np.ndarray:
    """Per-lag loop form of the unbiased normalized ACF (Formulae 27-29).

    Retained reference for the column-vectorized ``_band_acf``: the
    production kernel must reproduce this loop bit for bit.
    """
    from phonometry.psychoacoustics.loudness.ecma import _EPS

    n_fft = 2 * s_b
    spec = np.fft.fft(rect, n=n_fft, axis=1)
    unscaled = np.real(np.fft.ifft(np.abs(spec) ** 2, axis=1))
    energy = rect**2
    csum = np.cumsum(energy[:, ::-1], axis=1)[:, ::-1]
    m_max = (3 * s_b) // 4
    out = np.zeros_like(unscaled)
    total = csum[:, 0:1]
    for m in range(m_max):
        left = total[:, 0] - (csum[:, s_b - m] if (s_b - m) < s_b else 0.0)
        right = csum[:, m] if m < s_b else 0.0
        denom = np.sqrt(left * right + _EPS)
        out[:, m] = unscaled[:, m] / denom
    return out


def _short_band_signals() -> tuple[list, int]:
    """Clause 5 front-end band-pass signals for a short two-tone signal."""
    from scipy import signal as sp_signal

    from phonometry.psychoacoustics.loudness.ecma import (
        _CBF,
        _auditory_bandpass,
        _ear_filter_sos,
        _preprocess,
    )

    t = np.arange(int(FS * 0.15)) / FS
    x = 0.02 * np.sin(2.0 * np.pi * 1000.0 * t) + 0.01 * np.sin(
        2.0 * np.pi * 4000.0 * t
    )
    padded, _, n_new = _preprocess(x)
    p_om = sp_signal.sosfilt(_ear_filter_sos("free"), padded)
    return [_auditory_bandpass(p_om, band) for band in range(_CBF)], n_new


def test_band_acf_matches_reference_loop_bitwise() -> None:
    # The vectorized lag normalization must be bit-identical to the per-lag
    # reference loop for all four block sizes (8192/4096/2048/1024).
    from phonometry.psychoacoustics.loudness.ecma import (
        _S_B,
        _band_acf,
        _segment_bs,
    )

    p_bands, n_new = _short_band_signals()
    for band in (0, 10, 20, 30, 52):
        s_b = int(_S_B[band])
        seg = _segment_bs(p_bands[band], s_b, n_new)
        rect = np.where(seg > 0.0, seg, 0.0)
        got = _band_acf(rect, s_b, rect**2)
        ref = _reference_band_acf(rect, s_b)
        assert np.array_equal(got, ref), band


def test_average_bands_matches_stacked_mean_bitwise() -> None:
    # The sequential neighbour accumulation of _average_bands_full must be
    # bit-identical to the stacked np.mean formulation it replaced.
    import importlib

    le = importlib.import_module("phonometry.psychoacoustics.loudness.ecma")

    p_bands, n_new = _short_band_signals()
    got = le._average_bands_full(p_bands, n_new)

    cache: dict = {}
    for band in range(le._CBF):
        block_size = int(le._S_B[band])
        n_b = le._N_B_BY_SB[block_size]
        native = le._scaled_acf_at(p_bands, band, block_size, n_new, cache)
        if n_b == 0:
            ref = native
        elif band == 0:
            other = le._scaled_acf_at(p_bands, 1, block_size, n_new, cache)
            ref = 0.5 * (native + other)
        else:
            reach = min(n_b, band, le._CBF - 1 - band)
            if reach == 0:
                ref = native
            else:
                stack = [
                    le._scaled_acf_at(p_bands, band + off, block_size, n_new, cache)
                    for off in range(-reach, reach + 1)
                ]
                ref = np.mean(np.stack(stack, axis=0), axis=0)
        assert np.array_equal(got[band], ref), band


# --------------------------------------------------------------------------
# Total basis loudness N_basis (Clause 5.1.9, Formulae 25 and 26)
# --------------------------------------------------------------------------


def _polynomial(coefficients: Sequence[complex], omega: float) -> complex:
    """``sum_m c_m e^(-j omega m)``, a transfer function's numerator or denominator."""
    return sum(
        (c * cmath.exp(-1j * omega * m) for m, c in enumerate(coefficients)),
        start=0j,
    )


def _ear_filter_response(frequency_hz: float) -> complex:
    """Formula 4: the eight sections of Formula 5 with Table 1, cascaded."""
    omega = 2.0 * math.pi * frequency_hz / FS
    response = 1.0 + 0j
    for b0, b1, b2, a1, a2 in ECMA418_2_EAR_FILTER_FREE_FIELD:
        response *= _polynomial((b0, b1, b2), omega) / _polynomial((1.0, a1, a2), omega)
    return response


def _auditory_gain(z: float, frequency_hz: float) -> float:
    """Gain of band ``z`` for a sinusoid, from Formulae 8-10 and 13-17.

    The complex filter of Formulae 16-17 meets the positive and the negative
    frequency of a real sinusoid, and Clause 5.1.4.2 takes twice the real part
    of its output: the real band signal is the sinusoid scaled by
    ``|H(f) + conj(H(-f))|``.
    """
    k = ECMA418_2_FILTER_ORDER
    df0, c = ECMA418_2_DELTA_F0_HZ, ECMA418_2_BANDWIDTH_C
    centre = df0 / c * math.sinh(c * z)  # Formula 9
    bandwidth = math.sqrt(df0**2 + (c * centre) ** 2)  # Formula 10
    tau = math.comb(2 * k - 2, k - 1) / (2 ** (2 * k - 1) * bandwidth)  # F. 8
    d = math.exp(-1.0 / (FS * tau))
    e = ECMA418_2_FILTER_E
    scale = (1.0 - d) ** k / sum(e[i] * d**i for i in range(1, k))
    b = [scale * d**m * e[m] for m in range(k)]  # Formula 15
    shift = 2.0 * math.pi * centre / FS  # the modulation of Formulae 16 and 17
    omega = 2.0 * math.pi * frequency_hz / FS

    def response(w: float) -> complex:
        # Formulae 16 and 17 turn e^(-jwm) into x^m with x = e^(-j(w - shift)),
        # and the a_m = (-d)^m C(k, m) of Formula 14 sum to (1 - d x)^k by the
        # binomial theorem: the denominator is written as that product, since
        # summed term by term it cancels to a few parts in a million in the
        # lowest bands.
        x = cmath.exp(-1j * (w - shift))
        numerator = sum((b[m] * x**m for m in range(k)), start=0j)
        return numerator / (1.0 - d * x) ** k

    return abs(response(omega) + response(-omega).conjugate())


def _specific_basis_loudness(rms_pa: float, z_index: int) -> float:
    """Formulae 23-25 with Table 2, Table 3 and c_N for one band's RMS."""
    p0 = 2e-5
    alpha = ECMA418_2_NONLINEARITY_ALPHA
    product = 1.0
    previous = 1.0  # v_0
    for level, exponent in zip(
        ECMA418_2_NONLINEARITY_LEVELS_DB,
        ECMA418_2_NONLINEARITY_EXPONENTS,
        strict=True,
    ):
        threshold = p0 * 10.0 ** (level / 20.0)
        product *= (1.0 + (rms_pa / threshold) ** alpha) ** (
            (exponent - previous) / alpha
        )
        previous = exponent
    loudness = ECMA418_2_LOUDNESS_C_N * (rms_pa / p0) * product  # Formula 23
    return max(loudness - ECMA418_2_LTQ[z_index], 0.0)  # Formula 25


def _steady_state_basis_loudness(
    frequency_hz: float, level_db: float
) -> tuple[float, list[float]]:
    """N_basis (Formula 26) and N'_basis(z) of a steady free-field tone.

    With a whole number of samples per period, a half-wave rectified block
    holds exactly half the energy of the band signal, so Formula 22 returns
    its RMS: the tone's RMS times the gains of the ear filter and the band.
    """
    rms_in = 2e-5 * 10.0 ** (level_db / 20.0)
    ear = abs(_ear_filter_response(frequency_hz))
    specific = [
        _specific_basis_loudness(
            rms_in * ear * _auditory_gain(ECMA418_2_DZ * (i + 1), frequency_hz), i
        )
        for i in range(len(ECMA418_2_LTQ))
    ]
    return sum(specific) * ECMA418_2_DZ, specific


def test_the_front_end_holds_the_printed_tables() -> None:
    """The code's copies of Tables 1-3 and the Clause 5.1.4 constants are the print's.

    The closed form below reads the tables transcribed apart in
    ``tests/reference_data``, and this holds the code's own transcription to
    them, value for value. It is the only check of Table 3 in bands 48 to
    52: no steady tone the closed-form tests use reaches the threshold in
    quiet there, so a wrong LTQ in those bands would pass them.
    """
    from phonometry.psychoacoustics.loudness import ecma

    assert np.array_equal(ecma._LTQ, ECMA418_2_LTQ)
    assert np.array_equal(ecma._EAR_FREE, ECMA418_2_EAR_FILTER_FREE_FIELD)
    assert np.array_equal(ecma._NL_LEVELS, ECMA418_2_NONLINEARITY_LEVELS_DB)
    assert np.array_equal(ecma._NL_NU, ECMA418_2_NONLINEARITY_EXPONENTS)
    assert ecma._NL_ALPHA == ECMA418_2_NONLINEARITY_ALPHA
    assert ecma._DF0 == ECMA418_2_DELTA_F0_HZ
    assert ecma._C == ECMA418_2_BANDWIDTH_C
    assert ecma._K == ECMA418_2_FILTER_ORDER
    assert np.array_equal(ecma._E_K5, ECMA418_2_FILTER_E)
    assert ecma._DZ == ECMA418_2_DZ
    assert np.array_equal(ecma._Z, ECMA418_2_DZ * np.arange(1, len(ECMA418_2_LTQ) + 1))


@pytest.mark.parametrize(
    ("frequency_hz", "level_db"),
    [(93.75, 70.0), (1500.0, 60.0), (6000.0, 50.0)],
    ids=["93.75Hz-70dB", "1500Hz-60dB", "6000Hz-50dB"],
)
def test_total_basis_loudness_of_a_steady_tone_is_formula_26(
    monkeypatch: pytest.MonkeyPatch, frequency_hz: float, level_db: float
) -> None:
    """N_basis(l) of a steady tone is the printed chain by hand, band by band.

    The tones have 512, 32 and 8 samples per period, so every block size of
    Table 4 holds whole periods; the low one drives the 8192- and
    4096-sample bands, whose values reach the common grid by the linear
    interpolation of Clause 6.2.6. Blocks 64 to 136 of the 0.8 s signal lie
    where every band, interpolated or not, reads the tone alone.

    The band values agree to a part in a million or better, and the lowest
    bands set that floor: their recursion (Formula 13) has a five-fold pole a
    hundredth from the unit circle, so the double precision Clause 5.1.4.2
    asks for leaves its response off the exact one by about 1.5e-6 at
    93.75 Hz. The tolerances sit a few times above that floor.
    """
    import phonometry.psychoacoustics.loudness.ecma as ecma

    split = ecma._tonal_noise_split
    captured: list[np.ndarray] = []

    def spy(
        x: np.ndarray, field: str
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, int, int, np.ndarray]:
        out = split(x, field)
        captured.append(out[5])
        return out

    monkeypatch.setattr(ecma, "_tonal_noise_split", spy)
    result = psychoacoustics.loudness_ecma(
        _tone(frequency_hz, level_db, seconds=0.8), FS
    )
    expected_total, expected_specific = _steady_state_basis_loudness(
        frequency_hz, level_db
    )
    steady = slice(64, 137)
    specific = captured[0]
    assert specific.shape == (result.times.size, 53)
    assert np.allclose(specific[steady], expected_specific, rtol=1e-5, atol=1e-12)
    assert np.allclose(result.basis_loudness_vs_time[steady], expected_total, rtol=1e-6)
    # Formula 26 is the sum over the 53 bands times dz, block by block.
    assert np.array_equal(
        result.basis_loudness_vs_time,
        np.sum(specific, axis=1) * ECMA418_2_DZ,
    )
    # Every block is kept: the transient blocks 0 to 56 that Formulae 115 and
    # 117 leave out of N, and the blocks after l_end of Formula 40.
    l_end = math.ceil(38400 / 48000 * 187.5)
    assert result.last_evaluated_block == l_end
    assert result.basis_loudness_vs_time[:57].max() > 0.0
    assert result.basis_loudness_vs_time[l_end + 1 :].max() > 0.0


def test_a_tone_near_threshold_is_read_against_the_audibility_criterion() -> None:
    """A 1 kHz tone crosses 0.01 sone_HMS of N_basis between -1 and 0 dB SPL.

    A 1 kHz tone has 48 samples per period, which no block size of Table 4
    holds a whole number of times, so the closed form is no longer exact here
    (the blocks scatter about it by 0.2 %); it still puts 0 dB above the
    audibility criterion of Clause 5.1.9 and -1 dB below it, and so does
    every block of the result.
    """
    criterion = psychoacoustics.AUDIBILITY_THRESHOLD_SONE_HMS
    for level_db, audible in ((0.0, True), (-1.0, False)):
        result = psychoacoustics.loudness_ecma(_tone(1000.0, level_db, seconds=0.8), FS)
        expected, _ = _steady_state_basis_loudness(1000.0, level_db)
        steady = result.basis_loudness_vs_time[64:137]
        assert (expected > criterion) is audible
        assert steady == pytest.approx(np.full(steady.shape, expected), rel=5e-3)
        assert bool(np.all(steady > criterion)) is audible
        evaluated = result.basis_loudness_vs_time[: result.last_evaluated_block + 1]
        assert bool(np.any(evaluated > criterion)) is audible


def test_the_blocks_after_l_end_leave_the_audibility_reading() -> None:
    """A tone cut off mid-cycle is inaudible in every block up to l_end.

    A 63 Hz tone at 36 dB SPL stays under the threshold in quiet in every
    band, so N_basis is zero in every block that holds it. Cut off abruptly
    at 48128 samples, a multiple of 256, it leaves the auditory filters
    ringing in the blocks after l_end of Formula 40, which hold the zero
    padding Clause 6.2.6 removes; there N_basis passes 0.01 sone_HMS, so a
    comparison over every block would call the tone audible.
    """
    criterion = psychoacoustics.AUDIBILITY_THRESHOLD_SONE_HMS
    t = np.arange(48128) / FS
    tone = np.sqrt(2.0) * 2e-5 * 10 ** (36.0 / 20.0) * np.sin(2.0 * np.pi * 63.0 * t)
    result = psychoacoustics.loudness_ecma(tone, FS)
    l_end = math.ceil(48128 / 48000 * 187.5)
    assert result.last_evaluated_block == l_end
    evaluated = result.basis_loudness_vs_time[: l_end + 1]
    assert np.all(evaluated == 0.0)
    assert not bool(np.any(evaluated > criterion))
    assert result.basis_loudness_vs_time[l_end + 1 :].max() > criterion


def test_a_tone_at_the_edge_of_hearing_has_a_loudness() -> None:
    """Formula 113 gives a 1 kHz tone at 0 dB SPL a loudness above zero.

    There the exponent of Formula 114 passes a hundred, and the power of a
    specific loudness of a few thousandths falls below the smallest double:
    evaluated as printed, Formula 113 would read zero, whereas its value is
    at least the larger of its two terms. The loudness stays below the
    audibility criterion while N_basis clears it.
    """
    criterion = psychoacoustics.AUDIBILITY_THRESHOLD_SONE_HMS
    result = psychoacoustics.loudness_ecma(_tone(1000.0, 0.0, seconds=0.6), FS)
    assert result.loudness == pytest.approx(0.00345, rel=2e-2)
    assert result.loudness < criterion
    evaluated = result.basis_loudness_vs_time[: result.last_evaluated_block + 1]
    assert evaluated.max() > criterion


def test_every_band_starts_on_the_block_that_first_holds_the_sound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The bands of every block size line up on the common grid of Clause 6.2.6.

    Block l of a band with block size s_b and hop s_h ends at sample
    l s_h - 1 of the signal, just before sample l s_h (Formulae 18 and 19,
    block 0 at 0 ms), and Clause 6.2.6 puts it at index l s_h / 256 of the
    grid, filling the gaps by linear interpolation (Table 6). A sound that
    starts at a sample n_0 that every hop divides leaves every block that
    ends before n_0 silent, so in every band N'_basis(l, z) is exactly zero
    up to l = n_0 / 256 and above zero at the next index, where the first
    block that holds some of the sound, or the interpolation towards it,
    begins. Between that silent block and the next native block of a band
    the grid holds the straight line between the two, which a hold of either
    value would break. The sound is noise at 80 dB SPL with a 46.875 Hz tone
    at 90 dB SPL, which lifts the lowest band, whose threshold in quiet is
    the highest of Table 3, above it in its first partial block.
    """
    import phonometry.psychoacoustics.loudness.ecma as ecma

    split = ecma._tonal_noise_split
    captured: list[np.ndarray] = []

    def spy(
        x: np.ndarray, field: str
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, int, int, np.ndarray]:
        out = split(x, field)
        captured.append(out[5])
        return out

    monkeypatch.setattr(ecma, "_tonal_noise_split", spy)
    onset = 10 * 2048  # a multiple of every hop of Table 4
    sound = np.random.default_rng(418).standard_normal(int(0.8 * FS) - onset)
    sound *= 2e-5 * 10 ** (80.0 / 20.0) / np.sqrt(np.mean(sound**2))
    sound += _tone(46.875, 90.0, seconds=sound.size / FS)
    result = psychoacoustics.loudness_ecma(np.concatenate([np.zeros(onset), sound]), FS)
    specific = captured[0]
    last_silent = onset // 256
    assert np.all(specific[: last_silent + 1] == 0.0)
    assert np.all(specific[last_silent + 1] > 0.0)
    assert np.all(result.basis_loudness_vs_time[: last_silent + 1] == 0.0)
    assert result.basis_loudness_vs_time[last_silent + 1] > 0.0
    # Table 6: the (i - 1) inserted samples lie on the line between the silent
    # native block at index n_0 / 256 (every factor divides 80) and the next
    # native block, i indices on.
    for band in range(53):
        factor = int(ecma._INTERP[band])
        if factor > 1:
            assert np.allclose(
                specific[last_silent : last_silent + factor + 1, band],
                np.arange(factor + 1) / factor * specific[last_silent + factor, band],
                rtol=1e-12,
                atol=0.0,
            ), band
