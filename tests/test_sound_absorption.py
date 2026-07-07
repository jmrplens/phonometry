#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for BS EN ISO 354:2003 sound absorption in a reverberation room.

Normative anchors (ISO 354:2003):
- Eq. (5)/(7): A = 55,3*V/(c*T) - 4*V*m  (empty room A1 / with specimen A2).
- Eq. (6):     c = (331 + 0,6*t/degC) m/s, valid 15..30 degC.
- Eq. (8):     AT = A2 - A1 = 55,3*V*(1/(c2*T2) - 1/(c1*T1)) - 4*V*(m2 - m1).
- Eq. (9):     alpha_s = AT / S  (may exceed 1,0; clause 3.7 NOTE 2).
- m from ISO 9613-1 alpha (dB/m): m = alpha / (10*lg e).

Validation strategy: closed-form inversion of the Sabine equation, not
self-consistency. All tolerances are far below the standard's reporting
rounding (AT to 0,1 m2; alpha_s to 0,01; clause 8.3).
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

from phonometry import (
    AbsorptionWarning,
    absorption_area,
    absorption_coefficient,
    attenuation_from_alpha,
)
from phonometry.sound_absorption import _speed_of_sound


# --- Eq. (6): speed of sound ------------------------------------------------

def test_speed_of_sound_reference_20c() -> None:
    # c = 331 + 0,6*20 = 343 m/s.
    assert _speed_of_sound(20.0) == pytest.approx(343.0)


def test_default_temperature_is_20c() -> None:
    # absorption_area default temperature must give c = 343 m/s.
    a_default = absorption_area(5.0, 200.0)
    a_explicit = absorption_area(5.0, 200.0, speed_of_sound=343.0)
    assert np.asarray(a_default) == pytest.approx(np.asarray(a_explicit))


# --- Eq. (5)/(7): absorption area & exact T->A->T inversion -----------------

def test_absorption_area_formula() -> None:
    v, c, t = 200.0, 343.0, 3.5
    expected = 55.3 * v / (c * t)  # m = 0
    assert absorption_area(t, v, speed_of_sound=c) == pytest.approx(expected)


def test_exact_inversion_t_to_a_to_t() -> None:
    # A = 55,3 V/(c T)  =>  T = 55,3 V/(c A), exact round trip (m = 0).
    v, c = 200.0, 343.0
    t60 = np.array([1.5, 2.0, 3.7, 5.0, 8.2])
    a = absorption_area(t60, v, speed_of_sound=c)
    t_back = 55.3 * v / (c * np.asarray(a))
    np.testing.assert_allclose(t_back, t60, rtol=0, atol=1e-12)


def test_array_input_shape_preserved() -> None:
    a = absorption_area([2.0, 4.0, 6.0], 200.0)
    assert isinstance(a, np.ndarray)
    assert a.shape == (3,)


# --- Air-attenuation term ---------------------------------------------------

def test_air_correction_zero_when_m_zero() -> None:
    # -4 V m term vanishes at m = 0 (reference/zero condition).
    v, c, t = 200.0, 343.0, 4.0
    assert absorption_area(t, v, speed_of_sound=c, m=0.0) == pytest.approx(
        55.3 * v / (c * t)
    )


def test_air_correction_subtracts_4vm() -> None:
    v, c, t, m = 200.0, 343.0, 4.0, 0.003
    a = absorption_area(t, v, speed_of_sound=c, m=m)
    assert a == pytest.approx(55.3 * v / (c * t) - 4.0 * v * m)


def test_air_correction_per_band_array() -> None:
    v, c = 200.0, 343.0
    t = np.array([3.0, 3.0, 3.0])
    m = np.array([0.0, 0.001, 0.005])
    a = absorption_area(t, v, speed_of_sound=c, m=m)
    expected = 55.3 * v / (c * t) - 4.0 * v * m
    np.testing.assert_allclose(np.asarray(a), expected)


# --- m from ISO 9613-1 alpha (dB/m) -----------------------------------------

def test_attenuation_from_alpha_conversion() -> None:
    # m = alpha / (10 lg e); 10*lg(e) = 4,342944819...
    alpha = 4.342944819032518
    assert attenuation_from_alpha(alpha) == pytest.approx(1.0, rel=1e-9)
    assert attenuation_from_alpha(0.0) == 0.0


def test_attenuation_from_alpha_array() -> None:
    alpha = np.array([0.0, 4.342944819032518, 8.685889638065036])
    m = attenuation_from_alpha(alpha)
    np.testing.assert_allclose(np.asarray(m), [0.0, 1.0, 2.0], atol=1e-9)


# --- Eq. (8)/(9): absorption coefficient of a synthetic sample --------------

def test_recover_known_alpha() -> None:
    v, c, s, alpha_true = 200.0, 343.0, 10.0, 0.80
    t1 = 5.0
    a1 = 55.3 * v / (c * t1)
    a2 = a1 + alpha_true * s  # AT = alpha*S
    t2 = 55.3 * v / (c * a2)  # invert Eq. (7)
    alpha = absorption_coefficient(t1, t2, v, s, speed_of_sound1=c, speed_of_sound2=c)
    assert float(np.asarray(alpha)) == pytest.approx(alpha_true, abs=1e-9)


def test_recover_known_alpha_per_band() -> None:
    v, c, s = 200.0, 343.0, 10.0
    alpha_true = np.array([0.15, 0.45, 0.9, 1.15])
    t1 = np.full(4, 5.0)
    a1 = 55.3 * v / (c * t1)
    a2 = a1 + alpha_true * s
    t2 = 55.3 * v / (c * a2)
    alpha = absorption_coefficient(t1, t2, v, s, speed_of_sound1=c, speed_of_sound2=c)
    np.testing.assert_allclose(np.asarray(alpha), alpha_true, atol=1e-9)


def test_alpha_can_exceed_one_no_warning() -> None:
    # Clause 3.7 NOTE 2: alpha_s > 1 is valid and must not be clamped/warned.
    v, c, s = 200.0, 343.0, 10.0
    t1 = 6.0
    a1 = 55.3 * v / (c * t1)
    a2 = a1 + 1.3 * s
    t2 = 55.3 * v / (c * a2)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        alpha = absorption_coefficient(t1, t2, v, s, speed_of_sound1=c, speed_of_sound2=c)
    assert float(np.asarray(alpha)) == pytest.approx(1.3, abs=1e-9)


def test_two_temperature_correction_eq8() -> None:
    # c1 != c2: AT built with per-measurement speeds of sound.
    v, s = 200.0, 10.0
    t1, t2 = 5.0, 3.0
    c1, c2 = _speed_of_sound(18.0), _speed_of_sound(22.0)
    expected_at = 55.3 * v * (1.0 / (c2 * t2) - 1.0 / (c1 * t1))
    alpha = absorption_coefficient(
        t1, t2, v, s, temperature1=18.0, temperature2=22.0
    )
    assert float(np.asarray(alpha)) == pytest.approx(expected_at / s, abs=1e-9)


def test_temperature2_defaults_to_temperature1() -> None:
    v, s = 200.0, 10.0
    a = absorption_coefficient(5.0, 3.0, v, s, temperature1=25.0)
    b = absorption_coefficient(5.0, 3.0, v, s, temperature1=25.0, temperature2=25.0)
    assert float(np.asarray(a)) == pytest.approx(float(np.asarray(b)))


# --- Non-physical result warning (A2 <= A1, i.e. T2 >= T1) ------------------

def test_warns_when_alpha_non_positive() -> None:
    # Adding an absorber must reduce T; T2 >= T1 gives alpha_s <= 0.
    with pytest.warns(AbsorptionWarning):
        absorption_coefficient(3.0, 3.5, 200.0, 10.0)


def test_no_warning_for_positive_alpha() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        absorption_coefficient(5.0, 3.0, 200.0, 10.0)


# --- Range / input validation ----------------------------------------------

def test_negative_volume_raises() -> None:
    with pytest.raises(ValueError):
        absorption_area(3.0, -1.0)


def test_zero_reverberation_time_raises() -> None:
    with pytest.raises(ValueError):
        absorption_area(0.0, 200.0)


def test_negative_m_raises() -> None:
    with pytest.raises(ValueError):
        absorption_area(3.0, 200.0, m=-0.001)


def test_negative_sample_area_raises() -> None:
    with pytest.raises(ValueError):
        absorption_coefficient(5.0, 3.0, 200.0, -10.0)


def test_negative_t1_raises() -> None:
    with pytest.raises(ValueError):
        absorption_coefficient(-5.0, 3.0, 200.0, 10.0)


def test_temperature_outside_eq6_range_warns() -> None:
    # Eq. (6) is valid 15..30 degC; outside that range we still compute but warn.
    with pytest.warns(AbsorptionWarning):
        absorption_area(3.0, 200.0, temperature=5.0)


def test_no_temperature_warning_when_speed_supplied() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        absorption_area(3.0, 200.0, temperature=5.0, speed_of_sound=340.0)


# --- Synergy with room_parameters -------------------------------------------

def test_synergy_with_room_parameters() -> None:
    from phonometry import room_parameters

    fs = 48000
    # Synthesise a decaying reverberant impulse response so T is well-defined.
    rng = np.random.default_rng(0)
    t60_target = 1.2
    n = int(fs * 2.5)
    decay = np.exp(-3.0 * np.log(10.0) * np.arange(n) / (t60_target * fs))
    ir = rng.standard_normal(n) * decay
    res = room_parameters(ir, fs, limits=(250.0, 2000.0), fraction=1)
    a = absorption_area(res.t20, 200.0)
    assert isinstance(a, np.ndarray)
    assert a.shape == res.t20.shape
    # Finite where T20 is finite and positive.
    finite = np.isfinite(res.t20) & (res.t20 > 0)
    assert np.all(np.isfinite(np.asarray(a)[finite]))
