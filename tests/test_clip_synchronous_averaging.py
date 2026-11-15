#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What the synchronous averaging clip draws, held to the library and the print.

``anim_synchronous_averaging`` averages one record over 1 to 128 of its
periods and draws, for each count, the averaged period, its error and the
comb the average has applied. The guide that embeds it reads numbers off
those three panels, so these tests hold the data behind them from two sides.

The print: McFadden (1987), *Mechanical Systems and Signal Processing* 1(1),
page 85, gives the comb of N averages as Eq. (8),
``C(f) = 1/N sin(pi N T_R f) / sin(pi T_R f)``, and says of it that "the
peaks of the teeth of the comb have unit amplitude regardless of N" (Eq. (9));
page 86, that "increasing the number of averages N narrows the teeth of the
comb and also reduces the amplitude of the side lobes between the teeth". The
expected values below are derived from that closed form, not from the clip.

The library: the record is the one the guide's own figure code averages, and
every curve of the clip is what ``time_synchronous_average`` and
``comb_filter_response`` return for it.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from figures import schematics

from phonometry import signals

# The clip tooling is tied to the pinned figure stack its frames are drawn
# with, so the minimum-versions job deselects this module.
pytestmark = pytest.mark.pinned_stack

#: The counts the guide's still marks, and the clip marks as it passes them.
_COUNTS = (1, 2, 4, 8, 16, 32, 64, 128)


@pytest.fixture(scope="module")
def data() -> dict[str, object]:
    return schematics._synchronous_averaging_data()


def _guide_errors() -> list[float]:
    """The eight errors of the guide's own code for ``tsa_noise_reduction``."""
    fs = 8192.0
    samples = 256
    period_s = samples / fs
    m = np.arange(samples) / fs
    true = (
        np.cos(2 * np.pi * m / period_s)
        + 0.5 * np.cos(2 * np.pi * 3 * m / period_s + 0.7)
        + 0.25 * np.cos(2 * np.pi * 5 * m / period_s + 1.1)
    )
    rng = np.random.default_rng(5)
    recording = np.tile(true, 128) + rng.standard_normal(128 * samples)
    errors = []
    for n in _COUNTS:
        res = signals.time_synchronous_average(
            recording[: n * samples], fs, period_s=period_s, n_averages=n
        )
        errors.append(float(np.sqrt(np.mean((res.period_waveform - true) ** 2))))
    return errors


def test_the_clip_averages_the_record_of_the_guides_still(
    data: dict[str, object],
) -> None:
    errors = np.asarray(data["errors"])
    assert errors.shape == (128,)
    np.testing.assert_allclose(
        errors[np.asarray(_COUNTS) - 1], _guide_errors(), rtol=0.0, atol=1e-12
    )


def test_the_error_follows_the_square_root_law(data: dict[str, object]) -> None:
    errors = np.asarray(data["errors"])
    n = np.arange(1, 129)
    # Unit-variance noise: the ideal error is 1/sqrt(N). One realisation of
    # 256 samples scatters about it by a few per cent.
    assert np.all(np.abs(errors * np.sqrt(n) - 1.0) < 0.07)
    # The two ends the guide quotes.
    assert round(float(errors[0]), 2) == 0.97
    assert round(float(errors[127]), 3) == 0.090
    assert round(float(1.0 / np.sqrt(128.0)), 3) == 0.088


def test_the_noise_reduction_is_ten_log_n(data: dict[str, object]) -> None:
    reductions = np.asarray(data["reductions"])
    np.testing.assert_allclose(reductions, 10.0 * np.log10(np.arange(1, 129)))


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 8, 20, 32, 127, 128])
def test_the_comb_keeps_unit_teeth_and_n_minus_one_nodes(
    data: dict[str, object], n: int
) -> None:
    combs = data["combs"]
    assert isinstance(combs, list)
    orders, comb = combs[n - 1]
    per = schematics._TSA_PER_LOBE
    # The grid holds every tooth and every node of this N.
    teeth = comb[:: n * per]
    np.testing.assert_allclose(teeth, 1.0, rtol=0.0, atol=1e-12)
    assert teeth.size == schematics._TSA_ORDERS + 1
    grid_nodes = comb[::per]
    is_tooth = np.arange(grid_nodes.size) % n == 0
    np.testing.assert_allclose(grid_nodes[~is_tooth], 0.0, rtol=0.0, atol=1e-9)
    # N - 1 nodes between each pair of neighbouring teeth, the first of them
    # 1/N of an order from its tooth.
    assert np.count_nonzero(~is_tooth) == schematics._TSA_ORDERS * (n - 1)
    if n > 1:
        assert orders[per] == pytest.approx(1.0 / n)
    # Eq. (8) in magnitude, away from the teeth.
    inner = np.ones(orders.size, dtype=bool)
    inner[:: n * per] = False
    x = np.pi * orders[inner]
    np.testing.assert_allclose(
        comb[inner], np.abs(np.sin(n * x) / (n * np.sin(x))), rtol=0.0, atol=1e-9
    )


@pytest.mark.parametrize("n", [1, 2, 3, 7, 16, 128])
def test_the_comb_passes_one_nth_of_white_noise(n: int) -> None:
    # The mean of |C|^2 over one order is 1/N: the sigma^2/N of the law. The
    # midpoint rule is exact for a trigonometric polynomial of degree N - 1
    # once it has more than N - 1 points.
    points = 64 * n
    orders = (np.arange(points) + 0.5) / points
    comb = signals.comb_filter_response(orders * 32.0, 1.0 / 32.0, n)
    assert float(np.mean(comb**2)) == pytest.approx(1.0 / n, rel=1e-12)


@pytest.mark.parametrize("n", [3, 4, 8, 32, 128, 1024])
def test_the_lobe_next_to_a_tooth_stays_above_0_217(n: int) -> None:
    orders = np.linspace(1.0 / n, 2.0 / n, 4001)
    comb = signals.comb_filter_response(orders * 32.0, 1.0 / 32.0, n)
    first_lobe = float(comb.max())
    assert first_lobe > 0.217
    # And every lobe sits under the envelope 1/(N |sin(pi f T)|), which is
    # 1/N midway between two teeth.
    wide = np.linspace(0.01, 0.99, 9801)
    envelope = 1.0 / (n * np.abs(np.sin(np.pi * wide)))
    assert np.all(
        signals.comb_filter_response(wide * 32.0, 1.0 / 32.0, n) <= envelope + 1e-12
    )
    assert float(1.0 / (n * np.sin(np.pi * 0.5))) == pytest.approx(1.0 / n)


def test_the_clock_gives_each_count_of_the_still_a_frame() -> None:
    frames = [schematics._tsa_count(k) for k in range(240)]
    assert frames[0] == 1
    assert frames == sorted(frames)
    per = schematics._TSA_FRAMES_PER_OCTAVE
    assert [frames[per * k] for k in range(8)] == list(_COUNTS)
    # From the last doubling on, the clip holds N = 128 for the closing two
    # seconds and more.
    assert set(frames[7 * per :]) == {128}
    assert 240 - 7 * per >= 40
    # Every N whose nodes can be counted on the panel has a frame of its own.
    assert set(range(1, 47)) <= set(frames)


def test_the_guides_side_lobe_at_32_05_orders() -> None:
    # Section 3 of the guide: N = 32 leaves 0.19 of a tone at 32.05 orders,
    # 14 dB down, and N = 20 puts a node on it.
    period_s = 1.0 / 32.0
    f = np.array([32.05 / period_s])
    c32 = float(signals.comb_filter_response(f, period_s, 32)[0])
    c20 = float(signals.comb_filter_response(f, period_s, 20)[0])
    assert round(c32, 2) == 0.19
    assert round(20.0 * np.log10(c32)) == -14
    assert c20 < 1e-12
