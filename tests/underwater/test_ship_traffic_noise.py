#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for predicted ship-traffic source-level spectra.

Oracle for JOMOPANS-ECHO: the authors' own Excel reference implementation
(File S1 of MacGillivray & de Jong 2021), cached values for a Bulker sailing at
13.5 kn with length 211 m, in decidecade bands. RANDI and Wales-Heitmeyer are
checked for their qualitative source-model behaviour.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

from phonometry.underwater.ship_traffic_noise import (
    VESSEL_CLASSES,
    ShipTrafficSpectrum,
    ship_source_spectrum,
)

# Excel File S1 cached values: (frequency Hz, source PSD, decidecade band SL)
# for a Bulker, V = 13.5 kn, l = 211 m.
_ECHO_ORACLE = [
    (10.0, 157.234, 160.870),
    (12.5893, 158.4025, 163.0386),
    (39.8107, 166.8859, 176.5221),  # hump rising edge
    (50.119, 167.282, 177.918),  # low-frequency cargo hump peak
    (63.0957, 164.2368, 175.8729),  # hump falling edge
    (100.0, 155.736, 169.372),
    (158.4893, 153.3360, 168.9722),
    (1000.0, 137.758, 161.394),
    (3162.2777, 127.5927, 156.2288),
    (19952.6231, 111.5170, 148.1531),  # high-frequency tail
    (31622.777, 107.512, 146.148),
]


def _at(spectrum: ShipTrafficSpectrum, freq: float) -> tuple[float, float]:
    idx = int(np.argmin(np.abs(spectrum.frequency - freq)))
    return float(spectrum.source_psd[idx]), float(spectrum.band_level[idx])


def test_jomopans_echo_matches_reference_calculator() -> None:
    s = ship_source_spectrum(13.5, 211.0, vessel_class="bulker", model="jomopans-echo")
    assert isinstance(s, ShipTrafficSpectrum)
    for freq, psd_o, band_o in _ECHO_ORACLE:
        psd, band = _at(s, freq)
        assert psd == pytest.approx(psd_o, abs=1e-2)
        assert band == pytest.approx(band_o, abs=1e-2)


def test_jomopans_echo_faster_ship_is_louder() -> None:
    slow = ship_source_spectrum(10.0, 200.0, vessel_class="containership")
    fast = ship_source_spectrum(20.0, 200.0, vessel_class="containership")
    # 60*log10(V/Vc): +60*log10(2) ~ 18 dB louder at double the speed.
    assert np.all(fast.source_psd > slow.source_psd)
    assert float(np.mean(fast.source_psd - slow.source_psd)) == pytest.approx(
        60.0 * np.log10(2.0), abs=1e-6
    )


def test_cargo_low_frequency_hump_present() -> None:
    # Cargo vessels have an extra LF peak below 100 Hz; a tug (non-cargo) does not.
    bulker = ship_source_spectrum(13.9, 200.0, vessel_class="bulker")
    # Peak of the spectrum sits below 100 Hz for the cargo hump.
    peak_f = float(bulker.frequency[int(np.argmax(bulker.source_psd))])
    assert peak_f < 100.0


def test_randi_and_wales_heitmeyer_run() -> None:
    r = ship_source_spectrum(15.0, 250.0, model="randi")
    w = ship_source_spectrum(model="wales-heitmeyer")
    assert r.vessel_class is None
    assert w.speed_knots is None and w.length_m is None
    # Both give physically plausible source PSD near 100-160 dB at 1 kHz.
    assert 100.0 < _at(r, 1000.0)[0] < 200.0
    assert 100.0 < _at(w, 1000.0)[0] < 200.0


def test_wales_heitmeyer_ignores_speed_and_length() -> None:
    a = ship_source_spectrum(5.0, 100.0, model="wales-heitmeyer")
    b = ship_source_spectrum(25.0, 400.0, model="wales-heitmeyer")
    assert np.allclose(a.source_psd, b.source_psd)


def test_vessel_classes_exposed() -> None:
    assert "bulker" in VESSEL_CLASSES
    assert "containership" in VESSEL_CLASSES
    assert len(VESSEL_CLASSES) == 13


def test_unknown_class_and_model_rejected() -> None:
    with pytest.raises(ValueError, match="vessel_class"):
        ship_source_spectrum(12.0, 100.0, vessel_class="submarine")
    with pytest.raises(ValueError, match="model"):
        ship_source_spectrum(12.0, 100.0, model="urick")


def test_ship_traffic_plot_smoke() -> None:
    s = ship_source_spectrum(18.0, 300.0, vessel_class="containership")
    assert s.plot() is not None


# RANDI 3.1 Physics Description (Breeding et al., NRL/FR/7176--95-9628,
# approved for public release; Table 2): representative source levels, dB re
# 1 uPa at 1 m, computed from Eq. (2)-(5) with the average length and speed of
# each Table 1 class. The module reproduces the Large Tanker and Super Tanker
# rows to 0.06 dB at every tabulated frequency, and the Merchant/Tanker rows
# at all but one cell each (25 Hz and 300 Hz respectively, where the printed
# table deviates ~1-3 dB from its own equations; those cells and the Fishing
# row, whose assumed average is not reproducible, are excluded).
_RANDI_TABLE2 = [
    # (length ft, speed kn, {frequency: level})
    (337.5, 12.5, {10.0: 160.9, 50.0: 162.6, 100.0: 153.5, 300.0: 137.1}),   # Merchant
    (450.0, 14.0, {10.0: 167.0, 25.0: 170.8, 50.0: 168.6, 100.0: 159.2}),    # Tanker
    (600.0, 16.5, {10.0: 174.8, 25.0: 178.6, 50.0: 176.0, 100.0: 166.3,
                   300.0: 149.3}),                                           # Large Tanker
    (1000.0, 18.5, {10.0: 185.0, 25.0: 188.8, 50.0: 185.4, 100.0: 174.6,
                    300.0: 156.8}),                                          # Super Tanker
]


@pytest.mark.parametrize(("length_ft", "speed_kn", "levels"), _RANDI_TABLE2)
def test_randi_reproduces_report_table_2(
    length_ft: float, speed_kn: float, levels: dict,
) -> None:
    from phonometry.underwater.ship_traffic_noise import _randi

    f = np.array(sorted(levels))
    got = _randi(f, speed_kn, length_ft * 0.3048)
    for freq, ref in sorted(levels.items()):
        idx = int(np.argmin(np.abs(f - freq)))
        assert float(got[idx]) == pytest.approx(ref, abs=0.1), freq
