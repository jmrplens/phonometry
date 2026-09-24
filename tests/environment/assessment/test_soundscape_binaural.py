#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for :mod:`phonometry.environment.assessment.soundscape_binaural`.

ISO/TS 12913-3 Annex D is a recipe over metrics the library already
implements, so the oracle for each metric is the library function that owns
it, called on one ear: the analysis must return exactly what
:func:`~phonometry.signals.laeq`, :func:`~phonometry.psychoacoustics.loudness_zwicker`
or :func:`~phonometry.psychoacoustics.roughness_ecma` return for that channel.
What the annex adds is checked in closed form: the representative value is the
higher ear (D.2), the mean their average, the root mean cube of ISO/TS 12913-2
A.3 f) its printed formula, and the rows are those of Table D.1 as printed.
The hearing-model metrics with the heaviest chains (tonality, fluctuation
strength) are wired through stand-ins that return a known series, so that the
percentile taken from it can be written down; their own modules test the
chains.
"""

from __future__ import annotations

import math
import warnings

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from reference_data import ISO12913_3_TABLE_D1

from phonometry import environment, io, psychoacoustics, signals
from phonometry.environment.assessment import soundscape_binaural as sb
from phonometry.filters.weighting import weighting_filter

FS = 48_000


def _noise(seconds: float, rms_pa: float, seed: int) -> np.ndarray:
    """Band-limited noise with a slow level swing, so N5 and N95 differ."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    t = np.arange(n) / FS
    envelope = 1.0 + 0.6 * np.sin(2.0 * np.pi * 0.7 * t)
    x = rng.standard_normal(n) * envelope
    return rms_pa * x / np.sqrt(np.mean(x**2))


def _recording(seconds: float = 2.0) -> np.ndarray:
    left = _noise(seconds, 0.2, 1)
    right = 0.5 * left  # 6 dB quieter, same shape
    return np.vstack([left, right])


@pytest.fixture(scope="module")
def levels_and_loudness() -> sb.BinauralIndicators:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", sb.SoundscapeWarning)
        return sb.binaural_indicators(
            _recording(),
            FS,
            parameters=("sound_pressure_level", "loudness", "sharpness"),
        )


# ---------------------------------------------------------------------------
# Table D.1
# ---------------------------------------------------------------------------


def test_the_rows_are_table_d1() -> None:
    rows = list(sb.BINAURAL_PARAMETERS.values())
    assert len(rows) == len(ISO12913_3_TABLE_D1)
    for row, (parameter, metrics, average, reference) in zip(
        rows, ISO12913_3_TABLE_D1, strict=True
    ):
        assert row.parameter == parameter
        assert row.metrics == metrics
        assert row.average_allowed is average
        assert row.reference == reference


def test_the_table_is_read_only() -> None:
    table = sb.BINAURAL_PARAMETERS
    with pytest.raises(TypeError, match="does not support item assignment"):
        table["loudness"] = table["sharpness"]  # type: ignore[index]


# ---------------------------------------------------------------------------
# Each metric is the library's own, per ear
# ---------------------------------------------------------------------------


def test_levels_are_the_library_levels_of_each_ear(
    levels_and_loudness: sb.BinauralIndicators,
) -> None:
    x = _recording()
    metrics = levels_and_loudness.metrics
    for ear, channel in (("left", x[0]), ("right", x[1])):
        assert getattr(metrics["LAeq,T"], ear) == pytest.approx(
            float(signals.laeq(channel, FS)), abs=1e-9
        )
        assert getattr(metrics["LCeq,T"], ear) == pytest.approx(
            float(signals.leq(weighting_filter(channel, FS, "C"))), abs=1e-9
        )
        percentiles = signals.ln_levels(
            channel, FS, n=(5, 95), mode="fast", weighting="A"
        )
        assert getattr(metrics["LAF5,T"], ear) == pytest.approx(
            float(percentiles[5]), abs=1e-9
        )
        assert getattr(metrics["LAF95,T"], ear) == pytest.approx(
            float(percentiles[95]), abs=1e-9
        )


def test_the_representative_value_is_the_higher_ear(
    levels_and_loudness: sb.BinauralIndicators,
) -> None:
    """D.2: the right ear is 6 dB down, so the left ear represents both."""
    laeq = levels_and_loudness.metrics["LAeq,T"]
    assert laeq.left - laeq.right == pytest.approx(20.0 * math.log10(2.0), abs=1e-6)
    assert laeq.representative == laeq.left
    assert laeq.mean == pytest.approx(0.5 * (laeq.left + laeq.right))
    assert levels_and_loudness.representative("LAeq,T") == laeq.left
    for metric in levels_and_loudness.metrics.values():
        assert metric.representative == max(metric.left, metric.right)


def test_loudness_is_iso_532_1_of_each_ear(
    levels_and_loudness: sb.BinauralIndicators,
) -> None:
    """N5 is the library's; N95, Naverage and Nrmc are read off its trace."""
    left = _recording()[0]
    zwicker = psychoacoustics.loudness_zwicker(left, FS)
    trace = np.asarray(zwicker.loudness_vs_time)
    metrics = levels_and_loudness.metrics
    assert metrics["N5"].left == pytest.approx(zwicker.n5, rel=1e-12)
    assert metrics["Naverage"].left == pytest.approx(float(np.mean(trace)), rel=1e-12)
    # ISO/TS 12913-2 A.3 f) NOTE: the cube root of the mean of the cubes.
    assert metrics["Nrmc"].left == pytest.approx(
        float(np.mean(trace**3)) ** (1.0 / 3.0), rel=1e-12
    )
    ordered = np.sort(trace)
    k = int(0.05 * ordered.size)
    assert metrics["N95"].left == pytest.approx(
        0.5 * (ordered[k - 1] + ordered[k]), rel=1e-12
    )
    ratio = metrics["N5/N95"]
    assert ratio.left == pytest.approx(
        metrics["N5"].left / metrics["N95"].left, rel=1e-12
    )
    assert ratio.unit == "1"


def test_loudness_statistics_are_ordered(
    levels_and_loudness: sb.BinauralIndicators,
) -> None:
    """Naverage <= Nrmc always, by the power-mean inequality.

    On this swinging noise the two percentiles bracket both: N95 below, N5
    above.
    """
    m = levels_and_loudness.metrics
    for ear in ("left", "right"):
        n95, average, rmc, n5 = (
            getattr(m[s], ear) for s in ("N95", "Naverage", "Nrmc", "N5")
        )
        assert n95 <= average <= rmc <= n5
        assert getattr(m["N5/N95"], ear) > 1.0


def test_sharpness_is_reported_as_not_implemented(
    levels_and_loudness: sb.BinauralIndicators,
) -> None:
    missing = levels_and_loudness.not_implemented
    assert set(missing) == {"S5", "Saverage", "S95"}
    assert "sharpness_din" in missing["S5"]
    assert "S5" not in levels_and_loudness.metrics
    with pytest.raises(KeyError, match="specific loudness over time"):
        levels_and_loudness.representative("S5")


def test_a_row_not_requested_says_so(
    levels_and_loudness: sb.BinauralIndicators,
) -> None:
    with pytest.raises(KeyError, match="not requested"):
        levels_and_loudness.representative("R10")


def test_the_reporting_results_are_a3_f(
    levels_and_loudness: sb.BinauralIndicators,
) -> None:
    results = levels_and_loudness.reporting_results()
    assert set(results) == {
        "LAeq,T",
        "LCeq,T",
        "LAF5,T",
        "LAF95,T",
        "N5",
        "N95",
        "Nrmc",
    }
    assert results["N5"] == levels_and_loudness.representative("N5")
    record = environment.SoundscapeAcousticEnvironment(
        environment_type="real",
        sound_sources="traffic",
        weather_and_wind="dry",
        time_of_year_and_day="May, noon",
        measurement_points="one point, 1,6 m",
        measurement_results=results,
        site_description="street",
    )
    assert record.measurement_results["LAeq,T"] == results["LAeq,T"]


def test_the_metrics_mapping_is_read_only(
    levels_and_loudness: sb.BinauralIndicators,
) -> None:
    metrics = levels_and_loudness.metrics
    with pytest.raises(TypeError, match="does not support item assignment"):
        metrics["T"] = metrics["N5"]  # type: ignore[index]


def test_identical_ears_have_one_value() -> None:
    mono = _noise(1.0, 0.1, 7)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", sb.SoundscapeWarning)
        result = sb.binaural_indicators(
            np.vstack([mono, mono]), FS, parameters="sound_pressure_level"
        )
    for metric in result.metrics.values():
        assert metric.left == metric.right == metric.representative == metric.mean


def test_a_calibrated_signal_is_read_in_pascals() -> None:
    """A two-channel Signal brings its rate and factor; the array does not."""
    x = _recording(1.0)
    record = io.Signal(x / 2.0, FS, calibration_factor=2.0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", sb.SoundscapeWarning)
        from_signal = sb.binaural_indicators(record, parameters="sound_pressure_level")
        from_array = sb.binaural_indicators(x, FS, parameters="sound_pressure_level")
    assert from_signal.representative("LAeq,T") == pytest.approx(
        from_array.representative("LAeq,T"), abs=1e-9
    )
    assert from_signal.fs == FS


# ---------------------------------------------------------------------------
# The hearing-model metrics
# ---------------------------------------------------------------------------


def test_roughness_r10_is_the_ecma_single_value() -> None:
    """R10 is the value exceeded 10 % of the time, which ECMA-418-2 calls R."""
    t = np.arange(int(0.6 * FS)) / FS
    tone = (
        0.02 * (1.0 + np.sin(2.0 * np.pi * 70.0 * t)) * np.sin(2.0 * np.pi * 1000.0 * t)
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", sb.SoundscapeWarning)
        result = sb.binaural_indicators(
            np.vstack([tone, tone]), FS, parameters="roughness"
        )
    reference = psychoacoustics.roughness_ecma(tone, FS)
    assert result.metrics["R10"].left == pytest.approx(reference.roughness, rel=1e-12)
    assert result.metrics["R10"].right == pytest.approx(reference.roughness, rel=1e-12)
    assert result.metrics["R50"].left <= result.metrics["R10"].left
    assert result.metrics["R10"].unit == "asper"


def test_fluctuation_percentiles_leave_out_the_settling_frames(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F10 and F50 are taken over the frames ECMA-418-2 keeps for its F."""
    settling = sb._FLUCTUATION_SETTLING_FRAMES
    series = np.concatenate([np.full(settling, 100.0), np.arange(1.0, 101.0)])

    class _Fake:
        fluctuation_strength_vs_time = series

    monkeypatch.setattr(sb, "fluctuation_strength_ecma", lambda *a, **k: _Fake())
    x = np.zeros((2, FS // 10))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", sb.SoundscapeWarning)
        result = sb.binaural_indicators(x, FS, parameters="fluctuation_strength")
    kept = np.arange(1.0, 101.0)
    assert result.metrics["F10"].left == pytest.approx(float(np.percentile(kept, 90)))
    assert result.metrics["F50"].left == pytest.approx(float(np.percentile(kept, 50)))


def test_tonality_is_the_ecma_single_value_of_each_ear(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[float] = []

    class _Fake:
        def __init__(self, value: float) -> None:
            self.tonality = value

    def fake(channel: np.ndarray, fs: float, field: str = "free") -> _Fake:
        calls.append(float(np.max(np.abs(channel))))
        return _Fake(0.1 * len(calls))

    monkeypatch.setattr(sb, "tonality_ecma", fake)
    x = np.vstack([np.full(FS // 10, 0.3), np.full(FS // 10, 0.1)])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", sb.SoundscapeWarning)
        result = sb.binaural_indicators(x, FS, parameters="tonality")
    assert calls == [pytest.approx(0.3), pytest.approx(0.1)]
    assert result.metrics["T"].left == pytest.approx(0.1)
    assert result.metrics["T"].right == pytest.approx(0.2)
    assert result.metrics["T"].representative == pytest.approx(0.2)


# ---------------------------------------------------------------------------
# ISO/TS 12913-2 Annex D and the input
# ---------------------------------------------------------------------------


def test_a_recording_under_three_minutes_is_flagged() -> None:
    x = _recording(0.5)
    with pytest.warns(sb.SoundscapeWarning, match="at least 3 min"):
        sb.binaural_indicators(x, FS, parameters="sound_pressure_level")


def test_a_low_sampling_frequency_is_flagged() -> None:
    x = np.vstack([_noise(0.5, 0.1, 3)[::2], _noise(0.5, 0.1, 4)[::2]])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", sb.SoundscapeWarning)
        sb.binaural_indicators(x, 24_000, parameters="sound_pressure_level")
    messages = [str(w.message) for w in caught if w.category is sb.SoundscapeWarning]
    assert any("44.1 kHz" in message for message in messages)
    assert any("at least 3 min" in message for message in messages)


def test_a_single_channel_is_refused() -> None:
    mono = _noise(0.2, 0.1, 5)
    with pytest.raises(ValueError, match="binaural recording"):
        sb.binaural_indicators(mono, FS)


def test_three_channels_are_refused() -> None:
    x = np.zeros((3, 100))
    with pytest.raises(ValueError, match="binaural recording"):
        sb.binaural_indicators(x, FS)


def test_an_unknown_row_is_refused() -> None:
    x = _recording(0.2)
    with pytest.raises(ValueError, match="parameters"):
        sb.binaural_indicators(x, FS, parameters=("loudness", "annoyance"))


def test_no_row_is_refused() -> None:
    x = _recording(0.2)
    with pytest.raises(ValueError, match="at least one row"):
        sb.binaural_indicators(x, FS, parameters=())


def test_an_unknown_field_is_refused() -> None:
    x = _recording(0.2)
    with pytest.raises(ValueError, match="field"):
        sb.binaural_indicators(x, FS, field="pressure")  # type: ignore[arg-type]


def test_a_silent_recording_leaves_the_ratio_undefined() -> None:
    silence = np.zeros((2, FS // 2))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", sb.SoundscapeWarning)
        with pytest.raises(ValueError, match="N5/N95"):
            sb.binaural_indicators(silence, FS, parameters="loudness")


def test_a_non_finite_ear_value_is_refused() -> None:
    with pytest.raises(ValueError, match="'left' must be finite"):
        sb.BinauralMetric("T", "tonality", math.nan, 0.1, "tu_HMS", "ECMA-418-2")


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------


def test_the_plot_draws_one_row_at_both_ears(
    levels_and_loudness: sb.BinauralIndicators,
) -> None:
    ax = levels_and_loudness.plot()
    assert len(ax.patches) == 8  # four levels, two ears
    assert "Sound pressure level" in ax.get_title()
    plt.close("all")
    ax = levels_and_loudness.plot(parameter="loudness", language="es")
    assert len(ax.patches) == 8  # N5, Naverage, Nrmc, N95 at two ears
    assert "N_5/N_{95}" in ax.get_title()
    plt.close("all")


def test_the_plot_refuses_a_row_not_computed(
    levels_and_loudness: sb.BinauralIndicators,
) -> None:
    with pytest.raises(ValueError, match="'parameter'"):
        levels_and_loudness.plot(parameter="roughness")


def test_names_are_published_on_the_environment_package() -> None:
    for name in sb.__all__:
        assert getattr(environment, name) is getattr(sb, name)
