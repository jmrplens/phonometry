#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Noise reducing devices beside a road and beside a railway (EN 1793, EN 16272).

Two single-number ratings over one printed spectrum. The spectrum is the
oracle for itself, band by band from Table 1 of EN 1793-3; the two ratings
are checked against the closed forms their own formulas collapse to, which
is what a weighted average has to satisfy whatever the weights are: a
device that behaves the same in every band rates that behaviour, and the
cap of Clause 5 puts a ceiling of 20 dB on absorption however absorptive
the measurement says the device is.

The category ladders of the two Annexes A are read off the reported
integer, so their boundaries are checked where they bite.
"""

from __future__ import annotations

import warnings

import numpy as np

import phonometry as ph

from ..registry import Outcome, numeric, record, register

_ROAD_DEVICES = "Road traffic noise reducing devices (EN 1793)"
_RAIL_DEVICES = "Railway noise reducing devices (EN 16272)"
_BANDS = len(ph.environment.TRAFFIC_NOISE_BANDS_HZ)


def _ladder(printed: dict[int, str], computed: dict[int, str | None]) -> Outcome:
    """Compare a category ladder at the decibel values where it changes."""
    as_text = ", ".join(f"{value} dB -> {name}" for value, name in printed.items())
    got_text = ", ".join(f"{value} dB -> {name}" for value, name in computed.items())
    return Outcome(
        expected=as_text,
        computed=got_text,
        delta="0",
        passed=printed == computed,
    )


@register(
    _ROAD_DEVICES,
    "EN 1793-3:1997 Table 1 (normalised traffic noise spectrum)",
    "the eighteen printed levels, 100 Hz to 5 kHz",
)
def _chk_traffic_spectrum() -> Outcome:
    printed = {
        "100 Hz": -20.0,
        "1 kHz": -8.0,
        "5 kHz": -18.0,
    }
    levels = dict(
        zip(
            ph.environment.TRAFFIC_NOISE_BANDS_HZ,
            ph.environment.NORMALISED_TRAFFIC_NOISE_SPECTRUM_DB,
            strict=True,
        )
    )
    computed = {
        "100 Hz": levels[100.0],
        "1 kHz": levels[1000.0],
        "5 kHz": levels[5000.0],
    }
    return record(printed, computed, unit="dB")


@register(
    _ROAD_DEVICES,
    "EN 1793-1:2012 Clause 5 (DLalpha, constant absorption)",
    "a device absorbing 0,50 in every band rates -10 lg(1 - 0,50)",
)
def _chk_absorption_constant() -> Outcome:
    got = ph.environment.sound_absorption_rating(np.full(_BANDS, 0.5))
    return numeric(3.0103, got.rating, 1e-4, unit="dB")


@register(
    _ROAD_DEVICES,
    "EN 1793-1:2012 Clause 5 (DLalpha, the 0,99 ratio limit)",
    "a perfect absorber is capped at -10 lg(1 - 0,99) = 20 dB",
)
def _chk_absorption_cap() -> Outcome:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ph.environment.RoadDeviceWarning)
        got = ph.environment.sound_absorption_rating(np.ones(_BANDS))
    return numeric(20.0, got.rating, 1e-9, unit="dB")


@register(
    _ROAD_DEVICES,
    "EN 1793-1:2012 Table A.1 (categories of absorptive performance)",
    "the four boundaries A2/A3/A4/A5 read off the reported integer",
)
def _chk_absorption_categories() -> Outcome:
    printed = {4: "A2", 8: "A3", 12: "A4", 16: "A5"}
    computed = {}
    for reported in printed:
        alpha = 1.0 - 10.0 ** (-0.1 * reported)
        computed[reported] = ph.environment.sound_absorption_rating(
            np.full(_BANDS, alpha)
        ).category
    return _ladder(printed, computed)


@register(
    _ROAD_DEVICES,
    "EN 1793-2:2012 Clause 5.2 (DLR, constant sound reduction index)",
    "a wall with R = 32 dB in every band rates 32 dB",
)
def _chk_insulation_constant() -> Outcome:
    got = ph.environment.airborne_insulation_rating(np.full(_BANDS, 32.0))
    return numeric(32.0, got.rating, 1e-9, unit="dB")


@register(
    _ROAD_DEVICES,
    "EN 1793-2:2012 Clause 5.2 (DLR, spectrum weighting)",
    "one 10 dB band costs more at the 1 kHz peak than at the 100 Hz end",
)
def _chk_insulation_weighting() -> Outcome:
    loud, quiet = np.full(_BANDS, 40.0), np.full(_BANDS, 40.0)
    loud[10] = 10.0
    quiet[0] = 10.0
    at_peak = ph.environment.airborne_insulation_rating(loud).rating
    at_edge = ph.environment.airborne_insulation_rating(quiet).rating
    return Outcome(
        expected="DLR(weak at 1 kHz) < DLR(weak at 100 Hz)",
        computed=f"{at_peak:.2f} dB < {at_edge:.2f} dB",
        delta=f"{at_peak - at_edge:+.2f} dB",
        passed=at_peak < at_edge,
    )


@register(
    _ROAD_DEVICES,
    "EN 1793-2:2012 Table A.1 (categories of airborne sound insulation)",
    "the three boundaries B2/B3/B4 read off the reported integer",
)
def _chk_insulation_categories() -> Outcome:
    printed = {15: "B2", 25: "B3", 35: "B4"}
    computed = {
        reported: ph.environment.airborne_insulation_rating(
            np.full(_BANDS, float(reported))
        ).category
        for reported in printed
    }
    return _ladder(printed, computed)


@register(
    _RAIL_DEVICES,
    "EN 16272-3-1:2012 Table 1 (normalised railway noise spectrum)",
    "the printed levels at the ends and on the plateau",
)
def _chk_railway_spectrum() -> Outcome:
    levels = dict(
        zip(
            ph.environment.TRAFFIC_NOISE_BANDS_HZ,
            ph.environment.NORMALISED_RAILWAY_NOISE_SPECTRUM_DB,
            strict=True,
        )
    )
    printed = {"100 Hz": -27.0, "2 kHz": -9.0, "5 kHz": -17.0}
    computed = {
        "100 Hz": levels[100.0],
        "2 kHz": levels[2000.0],
        "5 kHz": levels[5000.0],
    }
    return record(printed, computed, unit="dB")


@register(
    _RAIL_DEVICES,
    "EN 16272-3-1:2012 Clause 6 (DLR on the railway spectrum)",
    "a wall with R = 26 dB in every band rates 26 dB",
)
def _chk_railway_insulation() -> Outcome:
    got = ph.environment.airborne_insulation_rating(
        np.full(_BANDS, 26.0), spectrum="railway"
    )
    return numeric(26.0, got.rating, 1e-9, unit="dB")


@register(
    _RAIL_DEVICES,
    "EN 16272-3-1:2012 Clause 5 (DLalpha on the railway spectrum)",
    "the same absorber rates higher against rolling noise than against a road",
)
def _chk_railway_absorption() -> Outcome:
    alpha = np.linspace(0.2, 0.9, _BANDS)
    road = ph.environment.sound_absorption_rating(alpha).rating
    rail = ph.environment.sound_absorption_rating(alpha, spectrum="railway").rating
    return Outcome(
        expected="DLalpha(railway) > DLalpha(road)",
        computed=f"{rail:.2f} dB > {road:.2f} dB",
        delta=f"{rail - road:+.2f} dB",
        passed=rail > road,
    )
