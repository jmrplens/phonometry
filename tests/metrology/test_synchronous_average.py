#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for time synchronous averaging (McFadden 1987).

Clean-room oracles derived from P. D. McFadden, "A revised model for the
extraction of periodic waveforms by time domain averaging", *Mechanical
Systems and Signal Processing* 1(1) 1987, 83-95, with synthesised signals
whose periodic part is known exactly:

* the comb-filter closed form ``|C(f)| = |sin(N·π·f·T)/(N·sin(π·f·T))|``
  (Eq. 8): unit teeth at the harmonics (Eq. 9), the mid-bin closed forms,
  and zeros at the nodes;
* the revised-model correction, that a non-harmonic interfering tone is
  best rejected by placing a comb node on it (McFadden's 32.05-order
  example: ``N = 20`` beats the power-of-two ``N = 32``);
* exact recovery of a noiseless periodic signal with an integer number of
  samples per period;
* recovery within a band-limited interpolation bound for a non-integer
  number of samples per period;
* the ``1/√N`` fall of the residual asynchronous-noise standard deviation.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

import phonometry as ph  # noqa: E402
from phonometry.metrology.synchronous_average import comb_filter_response

FS = 8192.0
#: One revolution spanning exactly 256 samples (32 revolutions per second).
PERIOD = 1.0 / 32.0
M = int(round(FS * PERIOD))  # 256 samples per period


def _periodic(period: float, m: int, orders: tuple[float, ...]) -> np.ndarray:
    """A smooth signal periodic in ``period`` sampled on ``m`` points/period."""
    phase = np.arange(m) * (period / m) / period
    out = np.zeros(m, dtype=np.float64)
    for k, order in enumerate(orders):
        out += (1.0 / (k + 1)) * np.cos(2.0 * np.pi * order * phase + 0.3 * k)
    return out


def _repeat(one_period: np.ndarray, n: int) -> np.ndarray:
    return np.tile(one_period, n)


# ---------------------------------------------------------------------------
# Comb-filter closed form (McFadden Eq. 8 / Eq. 9)
# ---------------------------------------------------------------------------


def test_comb_unit_teeth_at_harmonics() -> None:
    """|C| = 1 at every harmonic k/T, independent of N (Eq. 9)."""
    harmonics = np.array([k / PERIOD for k in range(1, 9)])
    for n in (1, 2, 4, 8, 20):
        response = comb_filter_response(harmonics, PERIOD, n)
        assert np.allclose(response, 1.0, atol=1e-9)


def test_comb_midbin_closed_forms() -> None:
    """Closed-form values between the teeth."""
    quarter = comb_filter_response(np.array([0.25 / PERIOD]), PERIOD, 2)[0]
    assert quarter == pytest.approx(1.0 / np.sqrt(2.0), abs=1e-12)
    half_n3 = comb_filter_response(np.array([0.5 / PERIOD]), PERIOD, 3)[0]
    assert half_n3 == pytest.approx(1.0 / 3.0, abs=1e-12)


def test_comb_node_between_teeth() -> None:
    """|C| = 0 at the mid-node j/(N·T) with j not a multiple of N."""
    node = comb_filter_response(np.array([0.5 / PERIOD]), PERIOD, 2)[0]
    assert node < 1e-12


def test_comb_response_is_bounded() -> None:
    """The comb magnitude never exceeds unity on a dense grid."""
    freqs = np.linspace(0.0, 8.0 / PERIOD, 4000)
    response = comb_filter_response(freqs, PERIOD, 7)
    assert float(np.max(response)) <= 1.0 + 1e-9


# ---------------------------------------------------------------------------
# McFadden's revised-model correction: choosing N to place a node
# ---------------------------------------------------------------------------


def test_mcfadden_node_selection_closed_form() -> None:
    """A 32.05-order tone: N=20 lands on a node, N=32 (power of 2) does not."""
    freq = np.array([32.05 / PERIOD])
    c20 = comb_filter_response(freq, PERIOD, 20)[0]
    c32 = comb_filter_response(freq, PERIOD, 32)[0]
    assert c20 < 1e-10  # 20 * 32.05 = 641 -> exact node
    assert c32 > 0.15  # 32 * 32.05 = 1025.6 -> passed with a side lobe
    assert c32 > 1e6 * max(c20, 1e-300)  # >100 dB better rejection with N=20


def test_mcfadden_node_selection_end_to_end() -> None:
    """The averaged waveform confirms the node: N=20 removes the interferer."""
    n_span = 40
    phase = np.arange((n_span + 1) * M) / FS / PERIOD
    true = np.cos(2.0 * np.pi * 8.0 * phase)
    interferer = 0.7 * np.cos(2.0 * np.pi * 32.05 * phase + 0.4)
    signal = true + interferer
    true_one = np.cos(2.0 * np.pi * 8.0 * np.arange(M) / M)

    leak_20 = np.max(
        np.abs(
            ph.time_synchronous_average(
                signal, FS, PERIOD, n_averages=20
            ).period_waveform
            - true_one
        )
    )
    leak_32 = np.max(
        np.abs(
            ph.time_synchronous_average(
                signal, FS, PERIOD, n_averages=32
            ).period_waveform
            - true_one
        )
    )
    assert leak_20 < 1e-9
    assert leak_32 > 0.1


# ---------------------------------------------------------------------------
# Exact recovery (integer samples per period)
# ---------------------------------------------------------------------------


def test_exact_recovery_integer_period() -> None:
    """Noiseless periodic signal, integer M, recovered to machine precision."""
    one = _periodic(PERIOD, M, (1.0, 3.0, 5.0))
    signal = _repeat(one, 24)
    result = ph.time_synchronous_average(signal, FS, PERIOD)

    assert result.interpolated is False
    assert result.samples_per_period == M
    assert result.n_averages == 24
    assert np.max(np.abs(result.period_waveform - one)) < 1e-12
    assert result.residual_rms < 1e-12


def test_times_span_one_period() -> None:
    one = _periodic(PERIOD, M, (2.0,))
    result = ph.time_synchronous_average(_repeat(one, 10), FS, PERIOD)
    assert result.times.size == M
    assert result.times[0] == pytest.approx(0.0, abs=1e-15)
    assert result.times[-1] < PERIOD


# ---------------------------------------------------------------------------
# Non-integer samples per period: fractional-delay alignment
# ---------------------------------------------------------------------------


def test_noninteger_period_recovered_within_bound() -> None:
    """A non-integer M is aligned by band-limited fractional delay."""
    period = 1.0 / 31.7  # FS * period is not an integer
    m_int = int(round(FS * period))
    phase = np.arange(30 * m_int) / FS / period
    signal = np.cos(2.0 * np.pi * phase) + 0.4 * np.cos(
        2.0 * np.pi * 2.0 * phase + 0.3
    )
    result = ph.time_synchronous_average(signal, FS, period)

    assert result.interpolated is True
    reference = np.cos(
        2.0 * np.pi * np.arange(m_int) * (period / m_int) / period
    ) + 0.4 * np.cos(
        2.0 * np.pi * 2.0 * np.arange(m_int) * (period / m_int) / period + 0.3
    )
    assert np.max(np.abs(result.period_waveform - reference)) < 0.05


# ---------------------------------------------------------------------------
# Noise reduction: 1/sqrt(N) law
# ---------------------------------------------------------------------------


def test_noise_reduction_sqrt_n_law() -> None:
    """Residual asynchronous-noise std falls as 1/sqrt(N) (statistical)."""
    one = _periodic(PERIOD, M, (1.0, 4.0))
    rng = np.random.default_rng(2024)
    n_avg = 64
    sigma = 1.0
    signal = _repeat(one, n_avg) + rng.standard_normal(n_avg * M) * sigma
    result = ph.time_synchronous_average(signal, FS, PERIOD, n_averages=n_avg)

    residual_of_average = result.period_waveform - one
    measured = float(np.std(residual_of_average))
    predicted = sigma / np.sqrt(n_avg)
    # 256 samples estimate the std of a zero-mean Gaussian to a relative
    # error ~ 1/sqrt(2*256) ~ 4.4 %; 15 % is a comfortable statistical band.
    assert measured == pytest.approx(predicted, rel=0.15)


def test_noise_reduction_db_matches_n() -> None:
    one = _periodic(PERIOD, M, (1.0,))
    result = ph.time_synchronous_average(_repeat(one, 100), FS, PERIOD)
    assert result.noise_reduction_db == pytest.approx(20.0, abs=1e-9)
    assert result.amplitude_snr_gain == pytest.approx(10.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Validation and plotting
# ---------------------------------------------------------------------------


def test_default_n_averages_uses_whole_record() -> None:
    one = _periodic(PERIOD, M, (1.0,))
    result = ph.time_synchronous_average(_repeat(one, 12), FS, PERIOD)
    assert result.n_averages == 12


def test_requested_n_averages_over_available_raises() -> None:
    signal = _repeat(_periodic(PERIOD, M, (1.0,)), 5)
    with pytest.raises(ValueError, match="exceeds"):
        ph.time_synchronous_average(signal, FS, PERIOD, n_averages=6)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"n_averages": 0}, "positive integer"),
        ({"n_harmonics": 0}, "positive integer"),
    ],
)
def test_invalid_parameters_raise(kwargs: dict, match: str) -> None:
    signal = _repeat(_periodic(PERIOD, M, (1.0,)), 4)
    with pytest.raises(ValueError, match=match):
        ph.time_synchronous_average(signal, FS, PERIOD, **kwargs)


def test_period_too_short_raises() -> None:
    signal = _repeat(_periodic(PERIOD, M, (1.0,)), 4)
    tiny_period = 1.0 / FS  # spans a single sample
    with pytest.raises(ValueError, match="at least 2 samples"):
        ph.time_synchronous_average(signal, FS, tiny_period)


def test_record_shorter_than_one_period_raises() -> None:
    short = np.zeros(M // 2, dtype=np.float64)
    with pytest.raises(ValueError, match="shorter than one period"):
        ph.time_synchronous_average(short, FS, PERIOD)


def test_comb_filter_response_validation() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        comb_filter_response(np.array([1.0]), PERIOD, 0)
    with pytest.raises(ValueError, match="positive"):
        comb_filter_response(np.array([1.0]), -1.0, 2)


def test_plot_returns_axes() -> None:
    one = _periodic(PERIOD, M, (1.0, 3.0))
    result = ph.time_synchronous_average(_repeat(one, 8), FS, PERIOD)

    axes = result.plot()
    assert axes.shape == (2,)
    plt.close("all")

    _, ax = plt.subplots()
    returned = result.plot(ax=ax, language="es")
    assert returned is ax
    plt.close("all")


def test_plot_rejects_unknown_language() -> None:
    result = ph.time_synchronous_average(
        _repeat(_periodic(PERIOD, M, (1.0,)), 4), FS, PERIOD
    )
    with pytest.raises(ValueError):
        result.plot(language="fr")
    plt.close("all")
