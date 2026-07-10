#  Copyright (c) 2026. Jose M. Requena-Plens
"""One-cycle deprecation shims introduced by the phonometry 3.1 renames.

One :func:`pytest.warns` test per alias (CONTRIBUTING, "Deprecations"):
the renamed ``loudness`` module (PEP 562 shim), the legacy snake_case
function aliases and the renamed keyword arguments (scikit-learn
``"deprecated"`` sentinel). Every alias must warn with the NEP 23 message
and delegate to the canonical name. Remove alongside the aliases in 4.0.
"""

from __future__ import annotations

import sys

import numpy as np
import pytest

import phonometry as ph

RNG = np.random.default_rng(1234)
SIGNAL = RNG.standard_normal(4800)
FS = 48_000.0


# --------------------------------------------------------------------------- #
# Renamed module: phonometry.loudness -> phonometry.loudness_zwicker
# --------------------------------------------------------------------------- #
def test_loudness_module_attribute_access_warns_and_delegates() -> None:
    import phonometry.loudness  # noqa: F401  (PEP 562 shim; import is silent)

    shim = sys.modules["phonometry.loudness"]
    target = sys.modules["phonometry.loudness_zwicker"]
    with pytest.warns(DeprecationWarning, match="loudness_zwicker"):
        cls = shim.ZwickerLoudness
    assert cls is target.ZwickerLoudness
    with pytest.warns(DeprecationWarning, match="deprecated since phonometry 3.1"):
        func = shim.loudness_zwicker
    assert func is ph.loudness_zwicker
    # __dir__ delegates (and does not warn).
    assert "loudness_zwicker_from_spectrum" in dir(shim)
    with pytest.raises(AttributeError, match="phonometry.loudness"):
        _ = shim.does_not_exist


# --------------------------------------------------------------------------- #
# Legacy snake_case function aliases
# --------------------------------------------------------------------------- #
def test_octavefilter_warns_and_delegates() -> None:
    canonical_spl, canonical_freq = ph.octave_filter(SIGNAL, 48000)
    with pytest.warns(DeprecationWarning, match=r"octave_filter\(\)"):
        spl, freq = ph.octavefilter(SIGNAL, 48000)
    np.testing.assert_allclose(spl, canonical_spl)
    assert freq == canonical_freq


def test_getansifrequencies_warns_and_delegates() -> None:
    canonical = ph.nominal_frequencies(3, [100, 5000])
    with pytest.warns(DeprecationWarning, match=r"nominal_frequencies\(\)"):
        legacy = ph.getansifrequencies(3, [100, 5000])
    assert legacy == canonical


def test_normalizedfreq_warns_and_delegates() -> None:
    canonical = ph.normalized_frequencies(1)
    with pytest.warns(DeprecationWarning, match=r"normalized_frequencies\(\)"):
        legacy = ph.normalizedfreq(1)
    assert legacy == canonical


def test_calculate_sensitivity_warns_and_delegates() -> None:
    tone = np.sin(2 * np.pi * 1000.0 * np.arange(4800) / FS)
    canonical = ph.sensitivity(tone, target_spl=94.0)
    with pytest.warns(DeprecationWarning, match=r"sensitivity\(\)"):
        legacy = ph.calculate_sensitivity(tone, target_spl=94.0)
    assert legacy == canonical


# --------------------------------------------------------------------------- #
# Renamed keyword: road_absorption sample_rate -> fs
# --------------------------------------------------------------------------- #
def test_adrienne_window_sample_rate_warns_and_forwards() -> None:
    canonical = ph.adrienne_window(FS)
    with pytest.warns(DeprecationWarning, match="'sample_rate' keyword"):
        legacy = ph.adrienne_window(sample_rate=FS)
    np.testing.assert_allclose(legacy, canonical)
    with pytest.warns(DeprecationWarning), pytest.raises(ValueError, match="both"):
        ph.adrienne_window(FS, sample_rate=FS)
    with pytest.raises(ValueError, match="missing required argument: 'fs'"):
        ph.adrienne_window()


def test_insitu_reflection_factor_sample_rate_warns_and_forwards() -> None:
    hi = np.zeros(256)
    hi[8] = 1.0
    hr = 0.5 * np.roll(hi, 16)
    delay = 16 / FS
    canonical = ph.insitu_reflection_factor(hi, hr, fs=FS, delay=delay)
    with pytest.warns(DeprecationWarning, match="'sample_rate' keyword"):
        legacy = ph.insitu_reflection_factor(hi, hr, sample_rate=FS, delay=delay)
    np.testing.assert_allclose(legacy, canonical)
    with pytest.warns(DeprecationWarning), pytest.raises(ValueError, match="both"):
        ph.insitu_reflection_factor(hi, hr, fs=FS, sample_rate=FS)


def test_insitu_absorption_spectrum_sample_rate_warns_and_forwards() -> None:
    hi = np.zeros(4096)
    hi[16] = 1.0
    hr = 0.5 * np.roll(hi, 32)
    canonical = ph.insitu_absorption_spectrum(hi, hr, FS)
    with pytest.warns(DeprecationWarning, match="'sample_rate' keyword"):
        legacy = ph.insitu_absorption_spectrum(hi, hr, sample_rate=FS)
    np.testing.assert_allclose(legacy.absorption, canonical.absorption)
    with pytest.raises(ValueError, match="missing required argument: 'fs'"):
        ph.insitu_absorption_spectrum(hi, hr)


# --------------------------------------------------------------------------- #
# Renamed keyword: outdoor_propagation humidity -> relative_humidity
# --------------------------------------------------------------------------- #
def test_atmospheric_absorption_humidity_warns_and_forwards() -> None:
    canonical = ph.atmospheric_absorption(200.0, [1000.0], relative_humidity=50.0)
    with pytest.warns(DeprecationWarning, match="'humidity' keyword"):
        legacy = ph.atmospheric_absorption(200.0, [1000.0], humidity=50.0)
    np.testing.assert_allclose(legacy, canonical)
    with pytest.warns(DeprecationWarning), pytest.raises(ValueError, match="both"):
        ph.atmospheric_absorption(
            200.0, [1000.0], relative_humidity=50.0, humidity=50.0
        )


def test_outdoor_propagation_attenuation_humidity_warns_and_forwards() -> None:
    canonical = ph.outdoor_propagation_attenuation(
        100.0, 2.0, 4.0, [500.0], relative_humidity=50.0
    )
    with pytest.warns(DeprecationWarning, match="'humidity' keyword"):
        legacy = ph.outdoor_propagation_attenuation(
            100.0, 2.0, 4.0, [500.0], humidity=50.0
        )
    np.testing.assert_allclose(legacy.a_total, canonical.a_total)


def test_predicted_receiver_level_humidity_warns_and_forwards() -> None:
    canonical = ph.predicted_receiver_level(
        [95.0], 100.0, 2.0, 4.0, [500.0], relative_humidity=50.0
    )
    with pytest.warns(DeprecationWarning, match="'humidity' keyword"):
        legacy = ph.predicted_receiver_level(
            [95.0], 100.0, 2.0, 4.0, [500.0], humidity=50.0
        )
    np.testing.assert_allclose(legacy, canonical)


# --------------------------------------------------------------------------- #
# Renamed keyword: sound_power room_volume -> volume
# --------------------------------------------------------------------------- #
def test_environmental_correction_room_volume_warns_and_forwards() -> None:
    canonical = ph.environmental_correction(
        40.0, reverberation_time=1.2, volume=300.0
    )
    with pytest.warns(DeprecationWarning, match="'room_volume' keyword"):
        legacy = ph.environmental_correction(
            40.0, reverberation_time=1.2, room_volume=300.0
        )
    assert legacy == canonical
    with pytest.warns(DeprecationWarning), pytest.raises(ValueError, match="both"):
        ph.environmental_correction(
            40.0, reverberation_time=1.2, volume=300.0, room_volume=300.0
        )


def test_sound_power_pressure_room_volume_warns_and_forwards() -> None:
    levels = np.tile(np.array([90.0, 92.0, 95.0]), (10, 1))
    canonical = ph.sound_power_pressure(
        levels, "hemisphere", radius=2.0, reverberation_time=1.0, volume=2000.0
    )
    with pytest.warns(DeprecationWarning, match="'room_volume' keyword"):
        legacy = ph.sound_power_pressure(
            levels,
            "hemisphere",
            radius=2.0,
            reverberation_time=1.0,
            room_volume=2000.0,
        )
    np.testing.assert_allclose(
        legacy.sound_power_level, canonical.sound_power_level
    )


def test_room_volume_explicit_none_stays_silent() -> None:
    # None was the old default; passing it through the deprecated alias must
    # not warn (only a real value does).
    import warnings

    import phonometry as ph

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        ph.environmental_correction(50.0, absorption_area=10.0, room_volume=None)
