#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for aircraft one-third-octave-band atmospheric absorption (SAE ARP 5534, 866A).

Oracles (independent of the implementation): the ISO 9613-1 pure-tone
coefficient, which ARP 5534 Eqs. 1-3 repeat, evaluated at the molar
concentration of water vapour that ARP 5534 Eqs. 4-6 give; the SAE-Method
piecewise continuity at 150 dB, and the SAE-Method regression evaluated by hand
from the published constants. For SAE ARP 866A, the formula of ISO 3891:1978
A.2 evaluated by hand at one band, and its Tables 1 and 2. Both routes are held
to the printed ECAC Doc 29 Vol. 2 Tables D-3b and D-3c in ``test_npd_atmosphere``.
"""

from __future__ import annotations

from dataclasses import replace

import matplotlib as mpl

mpl.use("Agg")
import numpy as np
import pytest
from iso3891_tables_data import (
    FREQUENCIES_HZ,
    TABLE_9,
    TABLE_9_MISPRINTED,
    TABLE_10,
    TEMPERATURES_C,
)

from phonometry.aircraft.atmospheric_absorption import (
    AircraftBandAttenuation,
    Arp866aAttenuation,
    arp866a_attenuation,
    sae_band_attenuation,
)
from phonometry.aircraft.certification import NOY_BANDS
from phonometry.environment.propagation.air_absorption import air_attenuation

# Published SAE-Method constants (ARP 5534 §3.2.2), for the independent oracle.
_A, _B, _C, _D, _E, _F, _G = 0.867942, 0.111761, 0.95824, 0.008191, 1.6, 9.2, 0.765


def _sae_oracle(delta_t: float) -> float:
    if delta_t < 150.0:
        return _A * delta_t * (1.0 + _B * (_C - _D * delta_t)) ** _E
    return _F + _G * delta_t


def _arp5534_eq6(temperature_k: float) -> float:
    """ARP 5534 Eqs. 5-6, typed from page 8 of the 2021 reaffirmation."""
    t01 = 273.16
    v = (
        10.79586 * (1.0 - t01 / temperature_k)
        - 5.02808 * np.log10(temperature_k / t01)
        + 1.50474e-4 * (1.0 - 10.0 ** (-8.29692 * (temperature_k / t01 - 1.0)))
        + 0.42873e-3 * (-1.0 + 10.0 ** (4.76955 * (1.0 - t01 / temperature_k)))
        - 2.2195983
    )
    return float(10.0**v)


def _iso9613_annex_b(temperature_k: float) -> float:
    """ISO 9613-1 Annex B saturation vapour pressure over the reference pressure."""
    return float(10.0 ** (-6.8346 * (273.16 / temperature_k) ** 1.261 + 4.6151))


def test_coefficient_is_iso9613_at_the_arp5534_molar_concentration() -> None:
    # ARP 5534 Eqs. 1-3 are ISO 9613-1's; Eq. 6 writes the saturation vapour
    # pressure in another form. ISO 9613-1 at the relative humidity that gives
    # the same molar concentration is therefore the ARP 5534 coefficient.
    f = np.array([50.0, 500.0, 1000.0, 8000.0])
    res = sae_band_attenuation(
        f, 500.0, temperature_c=15.0, relative_humidity_percent=60.0
    )
    assert isinstance(res, AircraftBandAttenuation)
    t_k = 288.15
    same_h = 60.0 * _arp5534_eq6(t_k) / _iso9613_annex_b(t_k)
    expected = air_attenuation(
        f,
        temperature_c=15.0,
        relative_humidity_percent=same_h,
        atmospheric_pressure_kpa=101.325,
        exact_midband=True,
    )
    assert np.allclose(res.coefficient, expected, rtol=1e-12, atol=0.0)
    assert np.allclose(res.midband_attenuation, expected * 500.0, rtol=1e-12)


def test_saturation_pressure_is_eq6_not_iso9613_annex_b() -> None:
    # The two forms part by 4.5 parts in 100 000 at 10 degC, which is what
    # moves 57 cells of ECAC Doc 29 Table D-3c by up to 0.036 dB.
    from phonometry.aircraft.atmospheric_absorption import _arp5534_saturation_ratio

    t_k = 283.15
    assert _arp5534_saturation_ratio(t_k) == pytest.approx(_arp5534_eq6(t_k), rel=1e-14)
    ratio = _arp5534_eq6(t_k) / _iso9613_annex_b(t_k)
    assert ratio == pytest.approx(1.0 - 4.5e-5, abs=0.2e-5)
    iso = air_attenuation([10000.0], temperature_c=10.0, relative_humidity_percent=80.0)
    arp = sae_band_attenuation(
        [10000.0], 1.0, temperature_c=10.0, relative_humidity_percent=80.0
    ).coefficient
    assert float(arp[0]) != pytest.approx(float(iso[0]), rel=1e-5)


def test_band_attenuation_matches_regression_oracle() -> None:
    f = np.array([100.0, 1000.0, 4000.0, 8000.0])
    res = sae_band_attenuation(
        f, 2000.0, temperature_c=25.0, relative_humidity_percent=70.0
    )
    for i in range(f.size):
        assert res.band_attenuation[i] == pytest.approx(
            _sae_oracle(float(res.midband_attenuation[i])), abs=1e-9
        )


def test_piecewise_continuity_at_150_db() -> None:
    # The two SAE-Method branches meet at δ_t = 150 dB (rounding of the published
    # constants leaves a ~0.003 dB gap).
    lo = _A * 150.0 * (1.0 + _B * (_C - _D * 150.0)) ** _E
    hi = _F + _G * 150.0
    assert abs(lo - hi) < 0.01


def test_small_absorption_band_close_to_pure_tone() -> None:
    # For small δ_t the band attenuation is within a few percent of pure-tone.
    res = sae_band_attenuation(
        [200.0], 100.0, temperature_c=25.0, relative_humidity_percent=70.0
    )
    ratio = float(res.band_attenuation[0] / res.midband_attenuation[0])
    assert 1.0 <= ratio < 1.05


def test_zero_path_length_gives_zero() -> None:
    res = sae_band_attenuation([1000.0, 4000.0], 0.0)
    assert np.allclose(res.band_attenuation, 0.0)
    assert np.allclose(res.midband_attenuation, 0.0)


def test_attenuation_increases_with_frequency_and_distance() -> None:
    near = sae_band_attenuation(
        [2000.0], 500.0, temperature_c=25.0, relative_humidity_percent=70.0
    )
    far = sae_band_attenuation(
        [2000.0], 5000.0, temperature_c=25.0, relative_humidity_percent=70.0
    )
    assert far.band_attenuation[0] > near.band_attenuation[0]
    spec = sae_band_attenuation([500.0, 8000.0], 2000.0)
    assert spec.band_attenuation[1] > spec.band_attenuation[0]


def test_large_attenuation_no_nan_or_warning() -> None:
    # Very long path at high frequency drives δ_t far past the 150 dB split; the
    # result must stay finite (the discarded low branch must not emit NaN).
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        res = sae_band_attenuation(
            [8000.0, 10000.0],
            50_000.0,
            temperature_c=25.0,
            relative_humidity_percent=70.0,
        )
    assert np.all(np.isfinite(res.band_attenuation))
    # Above 150 dB the linear branch applies: δ_B = 9.2 + 0.765·δ_t.
    assert np.all(
        res.band_attenuation == pytest.approx(9.2 + 0.765 * res.midband_attenuation)
    )


def test_invalid_inputs_rejected() -> None:
    with pytest.raises(ValueError, match=r"'frequencies' must be strictly positive"):
        sae_band_attenuation([-1.0], 100.0)
    with pytest.raises(ValueError, match=r"'path_length' must be non-negative"):
        sae_band_attenuation([1000.0], -5.0)


def test_per_band_arrays_must_agree() -> None:
    # The coefficient is the silent field: no figure draws it and nothing here
    # reads it, so it leaves as dB/m for the caller to multiply by a path
    # length, and collapsed to a single value numpy broadcasts it over every
    # band of that spectrum. The other three stop the figure instead.
    res = sae_band_attenuation([500.0, 1000.0, 2000.0, 4000.0], 1000.0)
    collapsed = res.coefficient[:1]
    with pytest.raises(ValueError, match=r"'coefficient' \(1\)"):
        replace(res, coefficient=collapsed)
    scalar = float(res.coefficient[0])
    with pytest.raises(ValueError, match=r"'coefficient' must have one axis"):
        replace(res, coefficient=scalar)
    short = res.band_attenuation[:-1]
    with pytest.raises(ValueError, match=r"'band_attenuation' \(3\)"):
        replace(res, band_attenuation=short)


def test_per_band_array_must_carry_one_axis() -> None:
    # A column of the same coefficients counts one entry per band on its first
    # axis, so every length agrees and the length check alone lets it through;
    # the caller who multiplies it by a path length and subtracts it from a
    # spectrum gets a band-by-band matrix instead of a spectrum.
    res = sae_band_attenuation([500.0, 1000.0, 2000.0, 4000.0], 1000.0)
    column = res.coefficient.reshape(-1, 1)
    with pytest.raises(ValueError, match="'coefficient' must have one axis"):
        replace(res, coefficient=column)


def test_plot_smoke() -> None:
    res = sae_band_attenuation(
        np.array([50.0, 100.0, 500.0, 1000.0, 5000.0, 10000.0]), 3000.0
    )
    assert res.plot() is not None


# --------------------------------------------------------------------------- #
# SAE ARP 866A, as ISO 3891:1978 Annex A gives it
# --------------------------------------------------------------------------- #


def _iso3891_a2(f0: float, theta: float, rh: float, eta: float) -> float:
    """ISO 3891 A.2, typed from the page, with ``eta`` supplied by the caller."""
    return 10.0 ** (
        2.05 * np.log10(f0 / 1000.0) + 1.1394e-3 * theta - 1.916984
    ) + eta * 10.0 ** (np.log10(f0) + 8.42994e-3 * theta - 2.755624)


def _iso3891_delta(f0: float, theta: float, rh: float) -> float:
    exponent = (
        np.log10(rh)
        - 1.328924
        + 3.179768e-2 * theta
        - 2.173716e-4 * theta**2
        + 1.7496e-6 * theta**3
    )
    return float(np.sqrt(1010.0 / f0) * 10.0**exponent)


def test_arp866a_formula_at_1_khz() -> None:
    # At 10 degC and 80 % the 1 kHz band has delta = 7.49, past the last
    # change of Table 1 at 6.50, so eta = 0.200 and the formula is closed.
    res = arp866a_attenuation(
        [1000.0], temperature_c=10.0, relative_humidity_percent=80.0
    )
    assert isinstance(res, Arp866aAttenuation)
    assert float(res.delta[0]) == pytest.approx(
        _iso3891_delta(1000.0, 10.0, 80.0), rel=1e-12
    )
    assert float(res.eta[0]) == pytest.approx(0.200)
    expected = _iso3891_a2(1000.0, 10.0, 80.0, 0.200)
    assert float(res.coefficient_db_per_100m[0]) == pytest.approx(expected, rel=1e-12)
    # ECAC Doc 29 Table D-3b, 1000 Hz at 1000 ft: 1.337 dB.
    assert float(res.path_attenuation_db(304.8)[0]) == pytest.approx(1.337, abs=5e-4)


def test_arp866a_evaluates_table_2_frequencies() -> None:
    res = arp866a_attenuation(
        NOY_BANDS, temperature_c=15.0, relative_humidity_percent=70.0
    )
    assert np.array_equal(res.frequencies_hz, NOY_BANDS)
    assert tuple(res.evaluation_frequencies_hz[-5:]) == (
        4000.0,
        4500.0,
        5600.0,
        7100.0,
        9000.0,
    )
    assert np.array_equal(res.evaluation_frequencies_hz[:20], NOY_BANDS[:20])
    exact = 1000.0 * 10.0 ** (np.array([-12.0, 7.0]) / 10.0)  # 63.0957, 5011.87
    by_exact = arp866a_attenuation(
        exact, temperature_c=15.0, relative_humidity_percent=70.0
    )
    assert tuple(by_exact.frequencies_hz) == (63.0, 5000.0)
    assert tuple(by_exact.evaluation_frequencies_hz) == (63.0, 4500.0)


def test_arp866a_dry_air_leaves_the_first_term() -> None:
    res = arp866a_attenuation(
        [2000.0], temperature_c=20.0, relative_humidity_percent=0.0
    )
    assert float(res.delta[0]) == pytest.approx(0.0)
    assert float(res.eta[0]) == pytest.approx(0.0)
    assert float(res.coefficient_db_per_100m[0]) == pytest.approx(
        _iso3891_a2(2000.0, 20.0, 0.0, 0.0), rel=1e-12
    )


def test_arp866a_path_attenuation_shapes() -> None:
    res = arp866a_attenuation(
        [500.0, 4000.0], temperature_c=10.0, relative_humidity_percent=80.0
    )
    one = res.path_attenuation_db(1000.0)
    assert one.shape == (2,)
    assert np.allclose(one, res.coefficient_db_per_100m * 10.0)
    many = res.path_attenuation_db([100.0, 1000.0, 5000.0])
    assert many.shape == (2, 3)
    with pytest.raises(ValueError, match="'path_length_m' must be one"):
        res.path_attenuation_db(-1.0)
    grid = [[1.0, 2.0]]
    with pytest.raises(ValueError, match="'path_length_m' must be one"):
        res.path_attenuation_db(grid)


def test_arp866a_refuses_what_the_formula_cannot_take() -> None:
    with pytest.raises(ValueError, match="'frequencies_hz' must name"):
        arp866a_attenuation([40.0], temperature_c=10.0, relative_humidity_percent=80.0)
    with pytest.raises(ValueError, match="'frequencies_hz' must name"):
        arp866a_attenuation(
            [12500.0], temperature_c=10.0, relative_humidity_percent=80.0
        )
    with pytest.raises(ValueError, match="'relative_humidity_percent' must be within"):
        arp866a_attenuation(
            [1000.0], temperature_c=10.0, relative_humidity_percent=120.0
        )
    with pytest.raises(ValueError, match="temperature_c"):
        arp866a_attenuation(
            [1000.0], temperature_c=-300.0, relative_humidity_percent=50.0
        )


def test_arp866a_arrays_must_agree() -> None:
    res = arp866a_attenuation(
        [500.0, 1000.0], temperature_c=10.0, relative_humidity_percent=80.0
    )
    short = res.eta[:1]
    with pytest.raises(ValueError, match="'eta' \\(1\\)"):
        replace(res, eta=short)


def test_arp866a_plot_smoke() -> None:
    res = arp866a_attenuation(
        NOY_BANDS, temperature_c=10.0, relative_humidity_percent=80.0
    )
    ax = res.plot(language="es")
    assert ax.get_ylabel().startswith("Coeficiente")
    assert "866A" in ax.get_legend().get_texts()[0].get_text()
    assert np.array_equal(ax.lines[0].get_xdata(), res.frequencies_hz)
    assert np.array_equal(ax.lines[0].get_ydata(), res.coefficient_db_per_100m)


def _coefficients(humidity: float, interpolation: str) -> np.ndarray:
    """ISO 3891 Tables 9 and 10 laid out: bands down, temperatures across."""
    return np.column_stack(
        [
            arp866a_attenuation(
                NOY_BANDS,
                temperature_c=t,
                relative_humidity_percent=humidity,
                eta_interpolation=interpolation,
            ).coefficient_db_per_100m
            for t in TEMPERATURES_C
        ]
    )


def test_quadratic_eta_reproduces_iso3891_table_10() -> None:
    # All 264 cells from -10 degC to 40 degC at 80 %, to the printed digit;
    # linear interpolation misses 11 of them, below 0 degC and in the bands
    # above 2 kHz, where delta falls in the curved part of Table 1.
    printed = np.array(TABLE_10)
    quadratic = _coefficients(80.0, "quadratic")
    assert np.all(np.abs(quadratic - printed) <= 0.05 + 1e-9)
    linear = _coefficients(80.0, "linear")
    assert np.count_nonzero(np.abs(linear - printed) > 0.05 + 1e-9) == 11


def test_quadratic_eta_is_the_parabola_through_three_entries() -> None:
    # delta between the entries 2.30 and 2.50 reads the parabola through
    # 2.00, 2.30 and 2.50 (0.570, 0.495, 0.450).
    res = arp866a_attenuation(
        [10000.0], temperature_c=10.0, relative_humidity_percent=80.0
    )
    d = float(res.delta[0])
    assert 2.30 < d < 2.50
    x, y = (2.00, 2.30, 2.50), (0.570, 0.495, 0.450)
    expected = sum(
        y[i] * np.prod([(d - x[j]) / (x[i] - x[j]) for j in range(3) if j != i])
        for i in range(3)
    )
    assert float(res.eta[0]) == pytest.approx(expected, abs=1e-12)


def test_quadratic_eta_holds_0_200_from_6_50() -> None:
    # Table 1 prints 0.200 at 6.50, 7.00 and 10.00. The parabola through
    # 6.05, 6.50 and 7.00 would dip to 0.1993 between the last two; eta stays
    # at 0.200 instead, as the linear reading does. 1250 Hz at 10 degC and
    # 80 % falls in that interval.
    res = arp866a_attenuation(
        [1250.0], temperature_c=10.0, relative_humidity_percent=80.0
    )
    assert 6.50 < float(res.delta[0]) < 7.00
    assert float(res.eta[0]) == pytest.approx(0.200, abs=1e-12)
    linear = arp866a_attenuation(
        [1250.0],
        temperature_c=10.0,
        relative_humidity_percent=80.0,
        eta_interpolation="linear",
    )
    assert float(res.coefficient_db_per_100m[0]) == pytest.approx(
        float(linear.coefficient_db_per_100m[0]), abs=1e-12
    )


def test_iso3891_table_9_misses_are_the_seven_errata_and_eight_near_boundaries() -> (
    None
):
    # Table 9 (70 %) is not reproduced as Table 10 is: the quadratic misses
    # 15 of its cells by one printed unit. Seven contradict Table 10 (see the
    # next test and the errata register); the other eight sit within
    # 0.014 dB/100 m of a rounding boundary, where no reading of Table 1
    # reproduces them all. Counting them keeps the documentation honest.
    printed = np.array(TABLE_9)
    computed = _coefficients(70.0, "quadratic")
    missed = np.argwhere(np.abs(computed - printed) > 0.05 + 1e-9)
    cells = {(FREQUENCIES_HZ[k], TEMPERATURES_C[j]) for k, j in missed}
    assert set(TABLE_9_MISPRINTED) <= cells
    others = cells - set(TABLE_9_MISPRINTED)
    assert sorted(others) == [
        (800.0, 5.0),
        (1250.0, 0.0),
        (1250.0, 5.0),
        (2000.0, 10.0),
        (4000.0, 0.0),
        (6300.0, 10.0),
        (6300.0, 20.0),
        (8000.0, 5.0),
    ]
    for band, temperature in others:
        value = computed[FREQUENCIES_HZ.index(band), TEMPERATURES_C.index(temperature)]
        boundary = np.floor(value * 10.0) / 10.0 + 0.05
        assert abs(value - boundary) < 0.014


def test_iso3891_table_9_contradicts_table_10_where_humidity_drops_out() -> None:
    # Where delta is past 6.5 at both 70 % and 80 %, eta is 0.200 at both and
    # the coefficient does not depend on the humidity: Tables 9 and 10 have to
    # print the same value. In seven cells Table 9 prints one unit more.
    t9, t10 = np.array(TABLE_9), np.array(TABLE_10)
    bands, temps = list(FREQUENCIES_HZ), list(TEMPERATURES_C)
    for band, temperature in TABLE_9_MISPRINTED:
        k, j = bands.index(band), temps.index(temperature)
        at70 = arp866a_attenuation(
            [band], temperature_c=temperature, relative_humidity_percent=70.0
        )
        at80 = arp866a_attenuation(
            [band], temperature_c=temperature, relative_humidity_percent=80.0
        )
        assert min(float(at70.delta[0]), float(at80.delta[0])) >= 6.5
        value = float(at70.coefficient_db_per_100m[0])
        assert value == pytest.approx(float(at80.coefficient_db_per_100m[0]))
        assert abs(value - t10[k, j]) <= 0.05
        assert t9[k, j] == pytest.approx(t10[k, j] + 0.1)


def test_unknown_eta_interpolation_is_refused() -> None:
    with pytest.raises(ValueError, match="'eta_interpolation' must be one of"):
        arp866a_attenuation(
            [1000.0],
            temperature_c=10.0,
            relative_humidity_percent=80.0,
            eta_interpolation="cubic",
        )
