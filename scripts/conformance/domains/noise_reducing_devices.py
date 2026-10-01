#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Noise reducing devices beside a road and beside a railway (EN 1793, EN 16272).

Single-number ratings over one printed spectrum. The spectrum is the
oracle for itself, band by band from Table 1 of EN 1793-3; the two ratings
are checked against the closed forms their own formulas collapse to, which
is what a weighted average has to satisfy whatever the weights are: a
device that behaves the same in every band rates that behaviour, and the
cap of Clause 5 puts a ceiling of 20 dB on absorption however absorptive
the measurement says the device is.

The category ladders of the two Annexes A are read off the reported
integer, so their boundaries are checked where they bite.

EN 1793-5 measures the reflection in place, and it prints more to check
against: the geometry of the grid in Tables 2 and 3, the sampled area of
5.6.1, the three windows, and the worked example of Annex B, twelve grid
positions averaged in Table B.1 and their uncertainty in Table B.2. The
processing itself is checked on synthetic records where the answer is known
in closed form: a perfect flat reflector returns 1, a reflection of amplitude
0,5 returns 0,25 whatever gain change the gain factor has to undo, the
subtraction finds a shift a fraction of a sample long, a reflection of two
impulses returns the comb each band integrates between its own edges, and an
impulse the 6,0 ms window leaves out and the 7,9 ms one takes in moves the
three lowest bands and none of the others.
"""

from __future__ import annotations

import warnings

import numpy as np
from reference_data import barrier_reflection as ref_reflection

import phonometry as ph

from ..registry import Outcome, count, numeric, record, register

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


# ---------------------------------------------------------------------------
# EN 1793-5:2016, the sound reflection measured in place
# ---------------------------------------------------------------------------
def _reflector_records(
    *, reflection: float, gain: float = 1.0, shift: float = 0.0
) -> tuple[np.ndarray, np.ndarray]:
    """Nine records of a flat reflector of amplitude ``reflection``, 48 kHz."""
    fs, speed, samples, start = 48000.0, 343.0, 4096, 300.0
    t = np.arange(samples)

    def pulse(at: float, amplitude: float) -> np.ndarray:
        dt = (t - at) / fs
        return (
            amplitude
            * np.exp(-0.5 * (dt / 0.05e-3) ** 2)
            * np.cos(2 * np.pi * 3000.0 * dt)
        )

    front = np.zeros((9, samples))
    free = np.zeros((9, samples))
    for k, (direct, reflected) in enumerate(ph.environment.reflection_grid_paths_m()):
        at = start + direct / speed * fs
        free[k] = pulse(at + shift, 1.0 / direct)
        front[k] = gain * (
            pulse(at, 1.0 / direct)
            + reflection * pulse(start + reflected / speed * fs, 1.0 / reflected)
        )
    return front, free


def _impulse_records(
    *, taps: tuple[int, ...] = (0,), late_s: float | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """One-sample direct sounds and a reflection of 0,5 on whole samples, 48 kHz.

    Every impulse but the late one lies in the flat part of its window, so
    the band energies of Formula (1) are closed forms.
    """
    fs, speed, samples, start = 48000.0, 343.0, 4096, 300.0
    front = np.zeros((9, samples))
    free = np.zeros((9, samples))
    for k, (direct, reflected) in enumerate(ph.environment.reflection_grid_paths_m()):
        at = round(start + direct / speed * fs)
        back = at + round((reflected - direct) / speed * fs)
        free[k, at] = front[k, at] = 1.0 / direct
        for tap in taps:
            front[k, back + tap] += 0.5 / reflected
        if late_s is not None:
            front[k, back + round(late_s * fs)] += 0.25 / reflected
    return front, free


def _reflection(front: np.ndarray, free: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ph.environment.RoadDeviceWarning)
        result = ph.environment.reflection_index(
            front, free, 48000.0, speed_of_sound=343.0
        )
    return np.asarray(result.reflection_index)


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 Table 2 (paths and Cgeo,k of the nine microphones)",
    "dS = 1,50 m, dM = 0,25 m and s = 0,40 m give the printed two decimals",
)
def _chk_reflection_table_2() -> Outcome:
    paths = ph.environment.reflection_grid_paths_m()
    corrections = ph.environment.geometric_divergence_corrections()
    matching = 0
    for k, (d_i, d_r, c_geo) in enumerate(ref_reflection.TABLE_2):
        computed = (
            round(float(paths[k, 0]), 2),
            round(float(paths[k, 1]), 2),
            round(float(corrections[k]), 2),
        )
        matching += sum(
            abs(a - b) < 1e-9 for a, b in zip(computed, (d_i, d_r, c_geo), strict=True)
        )
    return count(matching, 27, subject="printed cells")


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 Table 3 (nominal path differences of the position checks)",
    "the direct-to-microphone-5 and direct-to-reflected differences, to the millimetre",
)
def _chk_reflection_table_3() -> Outcome:
    paths = ph.environment.reflection_grid_paths_m()
    matching = 0
    for k, (dk5, dk) in enumerate(ref_reflection.TABLE_3):
        computed = (
            round(float(paths[k, 0] - paths[4, 0]), 3),
            round(float(paths[k, 1] - paths[k, 0]), 3),
        )
        matching += sum(
            abs(a - b) < 1e-9 for a, b in zip(computed, (dk5, dk), strict=True)
        )
    return count(matching, 18, subject="printed cells")


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 5.6.1 NOTE 1 (maximum sampled area, Formula (8))",
    "a 4 m by 4 m sample, the 7,9 ms window and 340 m/s give 1,96 m",
)
def _chk_reflection_sampled_area() -> Outcome:
    radius = ph.environment.reflection_sampled_area_radius_m(
        ref_reflection.SAMPLED_AREA_WINDOW_S,
        speed_of_sound=ref_reflection.SAMPLED_AREA_SPEED_M_S,
    )
    return numeric(ref_reflection.SAMPLED_AREA_RADIUS_M, radius, 0.005, unit="m")


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 5.5.5 and 5.5.1 (the three Adrienne windows)",
    "leading edge, flat part and trailing edge of the 7,9 ms, 6,0 ms and 1,3 ms windows",
)
def _chk_reflection_windows() -> Outcome:
    fs = 100_000.0
    printed: dict[str, float] = {}
    computed: dict[str, float] = {}
    for length, parts in ref_reflection.WINDOW_PARTS_S.items():
        window = ph.environment.adrienne_reflection_window(fs, length)
        lead = round(parts[0] * fs)
        flat = int(np.sum(window >= 1.0))
        trail = window.size - lead - flat
        for name, value, got in zip(
            ("lead", "flat", "trail"), parts, (lead, flat, trail), strict=True
        ):
            key = f"{length * 1e3:.1f} ms {name}"
            printed[key] = round(value * 1e3, 2)
            computed[key] = round(got / fs * 1e3, 2)
    return record(printed, computed, unit="ms")


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 Formula (1) (a perfect flat reflector)",
    "RI = 1 in all eighteen bands once Cgeo,k restores the longer path",
)
def _chk_reflection_perfect() -> Outcome:
    front, free = _reflector_records(reflection=1.0)
    worst = float(np.max(np.abs(_reflection(front, free) - 1.0)))
    return numeric(0.0, worst, 1e-6, expected_label="max |RI - 1| = 0")


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 Formulas (1) and (4) (a gain change between configurations)",
    "a reflection of amplitude 0,5 rates RI = 0,25 whatever the gain did",
)
def _chk_reflection_gain() -> Outcome:
    front, free = _reflector_records(reflection=0.5, gain=1.08, shift=0.4)
    worst = float(np.max(np.abs(_reflection(front, free) - 0.25)))
    return numeric(0.0, worst, 1e-5, expected_label="max |RI - 0,25| = 0")


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 Formula (1) (the one-third octave bands of a comb)",
    "two impulses 0,5 ms apart: 0,25 (2 + 2 cos 2 pi f tau) averaged over each band's base-ten edges",
)
def _chk_reflection_comb() -> Outcome:
    fs, delay = 48000.0, 24
    front, free = _impulse_records(taps=(0, delay))
    centres = 1000.0 * 10.0 ** (
        np.round(
            10.0 * np.log10(np.asarray(ph.environment.TRAFFIC_NOISE_BANDS_HZ) / 1e3)
        )
        / 10.0
    )
    lower, upper = centres * 10.0**-0.05, centres * 10.0**0.05
    phase = 2.0 * np.pi * delay / fs
    mean_cos = (np.sin(phase * upper) - np.sin(phase * lower)) / (
        phase * (upper - lower)
    )
    worst = float(
        np.max(np.abs(_reflection(front, free) - 0.25 * (2.0 + 2.0 * mean_cos)))
    )
    return numeric(0.0, worst, 1e-6, expected_label="max |RI - comb| = 0")


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 5.5.5 (which window serves which bands)",
    "an impulse 6 ms after the reflection moves 100 Hz to 160 Hz and no band from 200 Hz",
)
def _chk_reflection_window_bands() -> Outcome:
    front, free = _impulse_records(late_s=6.0e-3)
    index = _reflection(front, free)
    upper = float(np.max(np.abs(index[3:] - 0.25)))
    lower = float(np.min(np.abs(index[:3] - 0.25)))
    if lower < 1e-3:
        return Outcome(
            expected="the three lowest bands move",
            computed=f"min |RI - 0,25| = {lower:.2e} below 200 Hz",
            delta="unmoved",
            passed=False,
        )
    return numeric(0.0, upper, 1e-9, expected_label="max |RI - 0,25| from 200 Hz = 0")


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 5.5.4 (subtraction to a fiftieth of a sample)",
    "a free-field record 0,36 samples late is found 0,36 samples late",
)
def _chk_reflection_subtraction() -> Outcome:
    front, free = _reflector_records(reflection=0.5, shift=0.36)
    result = ph.environment.subtract_direct_sound(front[4], free[4], 48000.0)
    return numeric(-0.36, result.shift_samples, 1e-9, unit="")


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 Table B.1 (average of twelve grid positions)",
    "the printed average of every band, two of them exact ties at the half",
)
def _chk_reflection_table_b1() -> Outcome:
    positions = np.asarray(ref_reflection.TABLE_B1_POSITIONS).T
    result = ph.environment.reflection_index_from_positions(positions)
    matching = 0
    for band, mean, printed in zip(
        ref_reflection.TABLE_B1_BANDS_HZ,
        result.reflection_index,
        ref_reflection.TABLE_B1_AVERAGE,
        strict=True,
    ):
        if band in ref_reflection.TABLE_B1_TIED_BANDS_HZ:
            matching += abs(abs(float(mean) - printed) - 0.005) < 1e-9
        else:
            matching += abs(round(float(mean), 2) - printed) < 1e-9
    return count(matching, 18, subject="printed averages")


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 Table B.2 (DLRI before rounding) and Table B.1 (DLRI = 8 dB)",
    "Formula (12) on the printed averages from the 200 Hz band",
)
def _chk_reflection_rating() -> Outcome:
    rating = ph.environment.sound_reflection_rating(
        ref_reflection.TABLE_B1_AVERAGE,
        lowest_band_hz=ref_reflection.TABLE_B1_LOWEST_BAND_HZ,
    )
    if rating.reported != ref_reflection.TABLE_B1_RATING_DB:
        return Outcome(
            expected=f"{ref_reflection.TABLE_B1_RATING_DB} dB reported",
            computed=f"{rating.reported} dB reported",
            delta="differ",
            passed=False,
        )
    return numeric(ref_reflection.TABLE_B2_RATING_DB, rating.rating, 0.005, unit="dB")


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 Table B.2 (expanded uncertainty of DLRI)",
    "1,96 times the high reproducibility of Table A.1, 0,81 dB",
)
def _chk_reflection_rating_uncertainty() -> Outcome:
    positions = np.asarray(ref_reflection.TABLE_B1_POSITIONS).T
    _, expanded = ph.environment.reflection_index_from_positions(
        positions
    ).expanded_uncertainty()
    return numeric(
        ref_reflection.TABLE_B2_RATING_EXPANDED_DB, expanded, 0.005, unit="dB"
    )


@register(
    _ROAD_DEVICES,
    "EN 1793-5:2016 Table B.2 (expanded uncertainty per band)",
    "the eleven cells 1,96 times the printed sR gives; the other seven are a hundredth lower, as unrounded sR would give",
)
def _chk_reflection_band_uncertainty() -> Outcome:
    positions = np.asarray(ref_reflection.TABLE_B1_POSITIONS).T
    per_band, _ = ph.environment.reflection_index_from_positions(
        positions
    ).expanded_uncertainty()
    cells = [
        (value, printed)
        for band, value, printed in zip(
            ref_reflection.TABLE_B1_BANDS_HZ,
            per_band,
            ref_reflection.TABLE_B2_EXPANDED,
            strict=True,
        )
        if band not in ref_reflection.TABLE_B2_LOW_CELLS_HZ
    ]
    matching = sum(abs(round(float(v), 2) - p) < 1e-9 for v, p in cells)
    return count(matching, len(cells), subject="printed cells")
