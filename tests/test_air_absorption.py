#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for ISO 9613-1:1993 atmospheric sound absorption.

Normative anchors (ISO 9613-1:1993):
- Eq. (3): frO = (pa/pr)[24 + 4,04e4 h (0,02+h)/(0,391+h)]  (oxygen relaxation).
- Eq. (4): frN = (pa/pr)(T/T0)^-1/2 [9 + 280 h exp{-4,170[(T/T0)^-1/3 - 1]}].
- Eq. (5): alpha = 8,686 f^2 { 1,84e-11 (pa/pr)^-1 (T/T0)^1/2
                              + (T/T0)^-5/2 [0,012 75 e^(-2239,1/T)(frO+f^2/frO)^-1
                                            + 0,106 8 e^(-3352,0/T)(frN+f^2/frN)^-1] }.
- Eq. (6): fm = 1000*10^(k/10) exact midband frequencies (Table 1 uses these).
- Clause 4.2: T0 = 293,15 K, pr = 101,325 kPa; Annex B: T01 = 273,16 K.

Primary oracle: Table 1 (a)-(h), digit-exact, shared via
``reference_data.ISO9613_1_TABLE1``. The implementation reproduces every point
to < 0,4 %; tests assert agreement to within 1 in the last printed (3-sig-fig)
digit -- far tighter than the standard's own +/- 10 % claim (clause 7.1).
"""

from __future__ import annotations

import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

from phonometry import (
    AtmosphericAbsorptionWarning,
    air_attenuation,
    air_attenuation_m,
    attenuation_from_alpha,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reference_data as ref  # noqa: E402


# --- Table 1 oracle ---------------------------------------------------------

def _last_digit_ulp(value: float) -> float:
    """1 in the last printed digit of a 3-significant-figure value."""
    return 10.0 ** (math.floor(math.log10(value)) - 2)


@pytest.mark.parametrize("temp,rh,freq,alpha_km", ref.ISO9613_1_TABLE1)
def test_table1_digit_exact(
    temp: float, rh: float, freq: float, alpha_km: float
) -> None:
    # air_attenuation returns dB/m; Table 1 is dB/km. Use exact midbands (Note 5).
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", AtmosphericAbsorptionWarning)
        computed_km = float(air_attenuation(freq, temp, rh, exact_midband=True)) * 1e3
    assert computed_km == pytest.approx(alpha_km, abs=_last_digit_ulp(alpha_km))


def test_table1_agreement_is_tight() -> None:
    # The whole grid reproduces to well under 0,5 % (rounding-limited).
    worst = 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", AtmosphericAbsorptionWarning)
        for temp, rh, freq, alpha_km in ref.ISO9613_1_TABLE1:
            got = float(air_attenuation(freq, temp, rh, exact_midband=True)) * 1e3
            worst = max(worst, abs(got - alpha_km) / alpha_km)
    assert worst < 0.005


# --- Reference conditions (clause 4.2 / Annex B) ----------------------------

def test_reference_condition_constants() -> None:
    from phonometry.air_absorption import _PR, _T0, _T01

    assert _T0 == 293.15  # 20 degC
    assert _PR == 101.325  # one standard atmosphere, kPa
    assert _T01 == 273.16  # triple point of water, K


def test_reference_condition_finite_positive() -> None:
    # At the reference T0 = 20 degC the model must stay finite and positive.
    alpha = air_attenuation([1000.0], temperature=20.0, relative_humidity=50.0)
    assert np.all(np.isfinite(alpha)) and np.all(alpha > 0.0)


# --- Low-frequency f^2 growth (classical + rotational) ----------------------

def test_low_frequency_grows_as_f_squared() -> None:
    # Well below both relaxation frequencies alpha ~ f^2, so doubling f
    # quadruples alpha.
    f = np.array([10.0, 20.0, 40.0])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", AtmosphericAbsorptionWarning)
        a = air_attenuation(f, temperature=20.0, relative_humidity=60.0)
    assert a[1] / a[0] == pytest.approx(4.0, rel=0.05)
    assert a[2] / a[1] == pytest.approx(4.0, rel=0.05)


def test_alpha_strictly_increases_with_frequency() -> None:
    # Table 1 is monotone in frequency at fixed T, RH.
    f = np.array([50.0, 100.0, 250.0, 500.0, 1000.0, 2000.0, 5000.0, 10000.0])
    a = air_attenuation(f, temperature=15.0, relative_humidity=50.0)
    assert np.all(np.diff(a) > 0.0)


# --- Relaxation behaviour (frO/frN peaks) -----------------------------------

def test_relaxation_absorption_per_f2_rolls_off() -> None:
    # alpha/f^2 = const + relaxation terms frO/(frO^2+f^2) + frN/(frN^2+f^2),
    # both strictly decreasing in f: the vibrational relaxation roll-off.
    f = np.array([100.0, 500.0, 1000.0, 4000.0, 10000.0])
    a = air_attenuation(f, temperature=20.0, relative_humidity=70.0)
    per_f2 = a / f**2
    assert np.all(np.diff(per_f2) < 0.0)


def test_humidity_sweep_has_interior_peak() -> None:
    # At fixed T and f, raising humidity sweeps the oxygen relaxation frequency
    # frO(h) through f, so alpha rises to a peak then falls (cf. Table 1 (a),
    # 1 kHz, -20 degC: peaks near 80 % RH). This is the relaxation signature.
    rhs = np.array([10.0, 30.0, 50.0, 70.0, 80.0, 90.0, 100.0])
    alphas = np.array(
        [float(air_attenuation(1000.0, -20.0, rh, exact_midband=True)) for rh in rhs]
    )
    peak = int(np.argmax(alphas))
    assert 0 < peak < len(rhs) - 1  # interior maximum


# --- Validity ranges: warnings and errors -----------------------------------

@pytest.mark.parametrize(
    "kwargs",
    [
        {"temperature": -30.0},  # below -20 degC tabulated range
        {"temperature": 60.0},  # above +50 degC
        {"relative_humidity": 5.0},  # below 10 %
        {"pressure": 250.0},  # above 200 kPa envelope (clause 7)
    ],
)
def test_out_of_range_warns(kwargs: dict[str, float]) -> None:
    with pytest.warns(AtmosphericAbsorptionWarning):
        air_attenuation(1000.0, **kwargs)


def test_out_of_range_frequency_warns() -> None:
    with pytest.warns(AtmosphericAbsorptionWarning):
        air_attenuation([20.0, 1000.0])  # 20 Hz below the 50 Hz tabulated edge


@pytest.mark.parametrize(
    "args,kwargs",
    [
        (([0.0, 1000.0],), {}),  # non-positive frequency
        ((1000.0,), {"temperature": -273.15}),  # absolute zero
        ((1000.0,), {"relative_humidity": -1.0}),  # negative RH
        ((1000.0,), {"relative_humidity": 120.0}),  # > 100 %
        ((1000.0,), {"pressure": 0.0}),  # non-positive pressure
    ],
)
def test_invalid_inputs_raise(args: tuple, kwargs: dict) -> None:
    with pytest.raises(ValueError):
        air_attenuation(*args, **kwargs)


# --- Vectorization ----------------------------------------------------------

def test_vectorized_matches_scalar() -> None:
    freqs = [63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0]
    vec = air_attenuation(freqs, temperature=25.0, relative_humidity=45.0)
    for i, f in enumerate(freqs):
        one = air_attenuation(f, temperature=25.0, relative_humidity=45.0)
        assert float(one) == pytest.approx(vec[i], rel=1e-12)
    assert vec.shape == (len(freqs),)


def test_exact_midband_snaps_nominal_to_midband() -> None:
    # Nominal 50 Hz snaps to fm = 1000*10^(-13/10) = 50.1187... Hz.
    fm = 1000.0 * 10.0 ** (-13.0 / 10.0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", AtmosphericAbsorptionWarning)
        snapped = float(air_attenuation(50.0, exact_midband=True))
        direct = float(air_attenuation(fm, exact_midband=False))
    assert snapped == pytest.approx(direct, rel=1e-12)


# --- ISO 354 synergy: air_attenuation_m -------------------------------------

def test_air_attenuation_m_is_alpha_over_10_lg_e() -> None:
    freqs = [125.0, 500.0, 1000.0, 4000.0]
    alpha = air_attenuation(freqs, temperature=20.0, relative_humidity=50.0)
    m = air_attenuation_m(freqs, temperature=20.0, relative_humidity=50.0)
    np.testing.assert_allclose(m, attenuation_from_alpha(alpha), rtol=1e-12)
    # m = alpha / (10 lg e) ~ alpha / 4.3429.
    np.testing.assert_allclose(m, alpha / (10.0 * math.log10(math.e)), rtol=1e-12)
    assert np.all(m > 0.0)
