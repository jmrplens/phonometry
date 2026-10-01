#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Audio-frequency induction loops: IEC 60118-4:2014+A1 and IEC 62489-1:2010+A1.

The installed system and its components, each row against a value printed on
the rasterised page or a closed form the page states. IEC 60118-4 prints its
limits (3.1, 4.3, 7.2, 8.3.7, 8.4.3, Table 2, Table 3) and, through Amendment
1:2017, the small-volume limits of 9.5, the commissioning window of 10.2, the
overload test of 10.3 with Table 4 and the noise rule of 10.4.7; Annex E gives
the centre field of a square loop, the telecoil's cosine law, the corner of the
loop impedance and the magnetic units. IEC 62489-1 gives Table B.1, a loop's
resistance, inductance and impedance for six loops, the quadrature example of
5.4.14.1, the compliance voltage of 5.4.8 and the maximum output current of
5.4.7; its draft Amendment 2 gives the two neck-loop types of Annex D, cited as
a draft.

Two figures are read off their curves at 300 dots per inch against their own
gridlines, and the tolerance of those rows is the read, not a choice: Figure
H.1, the current that gives 400 mA/m 1,4 m above a loop's centre, at the end of
each curve (one pixel is 0,007 A and the lines are 3 to 5 pixels wide, so
+/-0,03 A), and Figure E.2 b), the two components of the field of a 15 by 10
loop 1,2 units above it (+/-0,5 dB: the vertical curve sits some 0,2 dB to
0,3 dB below a filament's field all along). The E.2 b) curves are the traverse
across the loop's width, as E.1 describes them; the figure's panel a) draws the
vertical-field line along the length, which ``docs/ERRATA.md`` records.

Three rows pin the value the page's own definitions give where the page prints
another: the band-limit responses of 6.4 NOTE 2 (printed exchanged), the fall
of 5.4.14.1 (printed as the rise) and the counter loop of Table B.1, whose
resistance needs the 1,6 m perimeter its sides give, not the printed 1,5 m. A
fourth compares the flux density of 1 A/m with the 1,256 µT E.6 prints, where
4 pi 10^-7 rounds to 1,257, within the last printed digit. All four are in
``docs/ERRATA.md``.

Oracle: IEC 60118-4:2014 read in BS EN 60118-4:2015 (PDF page = folio + 2):
3.1 (folio 9), 4.3 (11), 6.4 (13), Table 2 (14), 7.2 (15), 8.2.1 (16), 8.2.7
and Table 3 (17), 8.3.7 and 8.4.3 (19), E.1 (36), E.2 (37), Figure E.2 (38),
E.3 (43), E.6 (44), Figure H.1 (49). Amendment 1:2017 read in UNE-EN IEC
60118-4:2016/A1:2018 (PDF page = folio): Figure 2 (7), Figure 3 (9), 9.4 and
9.5 (10), 10.2 (11), 10.3.2 and Table 4 (12), 10.3.3 and 10.4.7 (13). IEC
62489-1:2010+A1:2014 read in BS EN 62489-1:2010+A1:2015 (PDF page = folio +
2): 5.4.7 (10, 11), 5.4.8 (11), 5.4.10.2 (13), 5.4.14.1 (14, 15), Table B.1
(22). E DIN EN 62489-1/A2:2017-10, the English CDV, D.1.2 and D.1.3 on PDF page
9 (CDV folio 5). IEC 60028:1925, clause I, PDF page 7 (folio 5).
"""

from __future__ import annotations

import functools
import math

import numpy as np
import reference_data as ref

from phonometry import electroacoustics as ea

from ..registry import Outcome, mask, numeric, record, register

_AFILS = "Audio-frequency induction loops (IEC 60118-4:2014+A1, IEC 62489-1:2010+A1)"

_60118 = "IEC 60118-4:2014"
_60118_A1 = "IEC 60118-4:2014+A1"
_62489 = "IEC 62489-1:2010+A1"
_A2_DRAFT = "E DIN EN 62489-1/A2:2017-10"


_FS = 48000


def _pass_fail(passes: bool) -> float:  # noqa: FBT001 - a verdict is a flag
    """A verdict as the 1 or 0 a record compares."""
    return 1.0 if passes else 0.0


# ---------------------------------------------------------------------------
# IEC 60118-4:2014: the reference, the signals and the limits
# ---------------------------------------------------------------------------


@register(
    _AFILS, f"{_60118} 3.1", "Level of 400 mA/m, the reference magnetic field strength"
)
def _chk_reference() -> Outcome:
    level = float(ea.field_strength_level(ref.IEC60118_4_REFERENCE_A_PER_M))
    return numeric(0.0, level, 1e-12, unit="dB", places=3)


@register(
    _AFILS, f"{_60118} 4.3", "Level of 100 mA/m, the long-term average of 70 dB SPL"
)
def _chk_long_term_level() -> Outcome:
    level = float(ea.field_strength_level(ref.IEC60118_4_LONG_TERM_A_PER_M))
    return numeric(ref.IEC60118_4_LONG_TERM_LEVEL_DB, level, 0.05, unit="dB", places=2)


def _band_limit_row(frequency: float) -> Outcome:
    computed = float(ea.band_limit_response([frequency])[0])
    printed = ref.IEC60118_4_BAND_LIMIT_PRINTED_DB[frequency]
    return numeric(
        ref.IEC60118_4_BAND_LIMIT_COMPUTED_DB[frequency],
        computed,
        5e-4,
        unit="dB",
        places=3,
        expected_label=(
            f"{ref.IEC60118_4_BAND_LIMIT_COMPUTED_DB[frequency]:.3f} dB from the 6.4 "
            f"filters (NOTE 2 prints {printed:.1f} dB, see ERRATA)"
        ),
    )


@register(
    _AFILS,
    f"{_60118} 6.4 NOTE 2",
    "Third-order Butterworth band limit at 100 Hz (-3 dB at 75 Hz and 6,5 kHz)",
)
def _chk_band_limit_100() -> Outcome:
    return _band_limit_row(100.0)


@register(
    _AFILS,
    f"{_60118} 6.4 NOTE 2",
    "Third-order Butterworth band limit at 5 kHz (-3 dB at 75 Hz and 6,5 kHz)",
)
def _chk_band_limit_5k() -> Outcome:
    return _band_limit_row(5000.0)


@register(
    _AFILS,
    f"{_60118} 6.4",
    "Band-limited pink noise flat within 1 dB from 100 Hz to 5 kHz",
)
def _chk_band_limit_flatness() -> Outcome:
    f = np.array([100.0, 125.0, 160.0, 200.0, 1000.0, 3150.0, 4000.0, 5000.0])
    response = ea.band_limit_response(f)
    worst = int(np.argmax(np.abs(response)))
    return mask(
        expected="within +/-1 dB from 100 Hz to 5 kHz",
        computed=f"worst {response[worst]:.3f} dB at {f[worst]:g} Hz",
        deviation=float(response[worst]),
        lower=-1.0,
        upper=1.0,
        frequency_hz=float(f[worst]),
        unit="dB",
    )


@register(
    _AFILS,
    f"{_60118} 6.4",
    "Peak-to-peak over RMS of the pink noise, at least 18 dB (crest factor 4)",
)
def _chk_pink_noise_crest() -> Outcome:
    x = ea.loop_test_noise(_FS, 30.0, seed=20260925)
    rms = math.sqrt(float(np.mean(x * x)))
    ratio = 20.0 * math.log10(float(np.max(x) - np.min(x)) / rms)
    return mask(
        expected="at least 18 dB (IEC 62489-1 5.4.8.2 b): 18 dB +/-2 dB)",
        computed=f"{ratio:.3f} dB",
        deviation=ratio,
        lower=ref.IEC60118_4_NOISE_PEAK_TO_PEAK_DB,
        upper=ref.IEC60118_4_NOISE_PEAK_TO_PEAK_DB
        + ref.IEC62489_1_NOISE_PEAK_TO_PEAK_TOL_DB,
        unit="dB",
    )


def _combi_parts() -> tuple[np.ndarray, np.ndarray]:
    x = ea.combi_signal(_FS, seed=20260925)
    return x[:_FS], x[_FS:]


@register(
    _AFILS, f"{_60118} Table 2", "Combi signal: RMS of the pink noise re the sine"
)
def _chk_combi_noise_level() -> Outcome:
    sine, noise = _combi_parts()
    ramp = round(ref.IEC60118_4_COMBI_RAMP_MS * 1e-3 * _FS)
    body = sine[ramp:-ramp]
    relative = 20.0 * math.log10(
        math.sqrt(float(np.mean(noise * noise)))
        / math.sqrt(float(np.mean(body * body)))
    )
    return numeric(
        ref.IEC60118_4_COMBI_NOISE_RELATIVE_DB, relative, 0.02, unit="dB", places=3
    )


@register(
    _AFILS,
    f"{_60118} Table 2",
    "Combi signal: sine peaks below the maximum peak of the noise",
)
def _chk_combi_peaks() -> Outcome:
    sine, noise = _combi_parts()
    below = -20.0 * math.log10(
        float(np.max(np.abs(sine))) / float(np.max(np.abs(noise)))
    )
    return numeric(
        ref.IEC60118_4_COMBI_SINE_PEAK_BELOW_NOISE_PEAK_DB,
        below,
        0.05,
        unit="dB",
        places=3,
    )


@register(
    _AFILS,
    f"{_60118} 7.2",
    "Reference signal-to-noise ratio classed at 47, 32 and 22 dB",
)
def _chk_background_noise_classes() -> Outcome:
    cases = {
        "above 47 dB": (-ref.IEC60118_4_SNR_IDEAL_DB - 0.01, "ideal"),
        "47 dB": (-ref.IEC60118_4_SNR_IDEAL_DB, "acceptable"),
        "32 dB": (-ref.IEC60118_4_SNR_MINIMUM_DB, "acceptable"),
        "below 32 dB": (
            -ref.IEC60118_4_SNR_MINIMUM_DB + 0.01,
            "tolerable_for_short_periods",
        ),
        "22 dB": (-ref.IEC60118_4_SNR_SHORT_PERIODS_DB, "tolerable_for_short_periods"),
        "below 22 dB": (-ref.IEC60118_4_SNR_SHORT_PERIODS_DB + 0.01, "below_tolerable"),
    }
    expected = dict.fromkeys(cases, 1.0)
    computed = {
        name: _pass_fail(ea.assess_background_noise([level]).category == category)
        for name, (level, category) in cases.items()
    }
    return record(expected, computed, label="each boundary in its 7.2 class")


def _window_row(verdict_at: dict[str, tuple[bool, bool]]) -> Outcome:
    expected = {name: _pass_fail(want) for name, (want, _) in verdict_at.items()}
    computed = {name: _pass_fail(got) for name, (_, got) in verdict_at.items()}
    return record(expected, computed)


@register(
    _AFILS, f"{_60118} 8.4.3", "Field strength at every point within 3 dB of 8.2.7"
)
def _chk_field_window() -> Outcome:
    tol = ref.IEC60118_4_FIELD_TOL_DB

    def verdict(level: float, specified: float = 0.0) -> bool:
        # The second point holds the 400 mA/m 8.2.7 asks for at one point.
        return ea.verify_induction_loop_system(
            [level, specified], specified_level_db=specified
        ).passes

    return _window_row(
        {
            "+3 dB": (True, verdict(tol)),
            "-3 dB": (True, verdict(-tol)),
            "+3,01 dB": (False, verdict(tol + 0.01)),
            "-3,01 dB": (False, verdict(-tol - 0.01)),
            # -5,9 + 3 is -2,900 000 000 000 000 4 in binary.
            "-2,9 dB on a meter reading 400 mA/m as -5,9 dB": (
                True,
                verdict(-2.9, -5.9),
            ),
        }
    )


@register(
    _AFILS,
    f"{_60118} 8.2.7",
    "Maximum field of 400 mA/m reached at one point at least",
)
def _chk_field_reached() -> Outcome:
    def verdict(levels: list[float], specified: float = 0.0) -> bool:
        return ea.verify_induction_loop_system(
            levels, specified_level_db=specified
        ).passes

    pink = ref.IEC60118_4_TABLE3["pink_noise"][0]
    return _window_row(
        {
            "0 dB at one point, -3 dB elsewhere": (True, verdict([-3.0, 0.0])),
            "-0,01 dB at best": (False, verdict([-3.0, -0.01])),
            "pink noise: -6 dB at one point (Table 3)": (
                True,
                verdict([-9.0, pink], pink),
            ),
            "pink noise: -6,01 dB at best": (
                False,
                verdict([-9.0, pink - 0.01], pink),
            ),
        }
    )


@register(
    _AFILS,
    f"{_60118} 8.3.7",
    "Frequency response within 3 dB of 1 kHz from 100 Hz to 5 kHz",
)
def _chk_response_window() -> Outcome:
    tol = ref.IEC60118_4_RESPONSE_TOL_DB
    low, high = ref.IEC60118_4_RESPONSE_BAND_HZ
    f = [50.0, low, 1000.0, high, 8000.0]

    def verdict(
        at_low: float, at_high: float, outside: float, at_1k: float = 0.0
    ) -> bool:
        return ea.verify_induction_loop_system(
            [0.0],
            frequencies_hz=f,
            response_db=[outside, at_low, at_1k, at_high, outside],
        ).passes

    return _window_row(
        {
            "-3 dB at 100 Hz, +3 dB at 5 kHz": (True, verdict(-tol, tol, 0.0)),
            "-3,01 dB at 100 Hz": (False, verdict(-tol - 0.01, 0.0, 0.0)),
            "+3,01 dB at 5 kHz": (False, verdict(0.0, tol + 0.01, 0.0)),
            "-20 dB outside the band": (True, verdict(0.0, 0.0, -20.0)),
            # Read as decimals, the edges are 3,000 000 000 000 001 8 dB down
            # and 3,000 000 000 000 003 6 dB up in binary.
            "-18,6 dB at 100 Hz against -15,6 dB at 1 kHz": (
                True,
                verdict(-18.6, -15.6, -15.6, -15.6),
            ),
            "-31,7 dB at 5 kHz against -34,7 dB at 1 kHz": (
                True,
                verdict(-34.7, -31.7, -34.7, -34.7),
            ),
        }
    )


# ---------------------------------------------------------------------------
# Amendment 1:2017: small volumes, commissioning, overload, system noise
# ---------------------------------------------------------------------------


@register(
    _AFILS,
    f"{_60118_A1} 9.5",
    "Small-volume limits: 6 dB range, 0 dB reached, +8 dB area",
)
def _chk_small_volume() -> Outcome:
    span = ref.IEC60118_4_A1_SMALL_VOLUME_RANGE_DB
    area = ref.IEC60118_4_A1_STANDING_AREA_MAX_DB

    def verdict(levels: np.ndarray, survey: list[float] | None = None) -> bool:
        return ea.verify_small_volume_system(
            levels, layout="counter", standing_area_levels_db=survey
        ).passes

    edges = np.array([[-span, 0.0, span]] * 3)
    over = edges.copy()
    over[1, 2] = span + 0.01
    under = np.full((3, 3), -0.01)
    return _window_row(
        {
            "+/-6 dB with 0 dB reached": (True, verdict(edges)),
            "+6,01 dB at one point": (False, verdict(over)),
            "every point below 0 dB": (False, verdict(under)),
            "+8 dB in the standing area": (True, verdict(edges, [area])),
            "+8,01 dB in the standing area": (False, verdict(edges, [area + 0.01])),
        }
    )


@register(
    _AFILS,
    f"{_60118_A1} Figures 2 and 3",
    "Measurement points of a refuge and a counter, in millimetres",
)
def _chk_measurement_points() -> Outcome:
    small = ea.small_volume_measurement_points("refuge_small")[0]
    large = ea.small_volume_measurement_points("refuge_large")[0]
    counter = ea.small_volume_measurement_points("counter")
    radii = np.hypot(small[:, 0], small[:, 1]) * 1e3
    expected = {
        "2 a) inner radius": ref.IEC60118_4_A1_FIGURE2A_MM["inner_radius"],
        "2 a) outer radius": ref.IEC60118_4_A1_FIGURE2A_MM["outer_radius"],
        "2 b) l4": ref.IEC60118_4_A1_FIGURE2B_MM["l4"],
        "2 b) l5": ref.IEC60118_4_A1_FIGURE2B_MM["l5"],
        "3 a) radius": ref.IEC60118_4_A1_FIGURE3_MM["radius"],
        "3 a) l4": ref.IEC60118_4_A1_FIGURE3_MM["lateral"],
        "3 b) top height": 1e3 * ref.IEC60118_4_A1_COUNTER_HEIGHTS_M[-1],
    }
    computed = {
        "2 a) inner radius": round(float(radii[1]), 6),
        "2 a) outer radius": round(float(radii[4]), 6),
        "2 b) l4": round(float(np.ptp(large[:3, 0])) * 1e3, 6),
        "2 b) l5": round(float(np.ptp(large[3:, 0])) * 1e3, 6),
        "3 a) radius": round(float(np.hypot(*counter[0, 0, :2])) * 1e3, 6),
        "3 a) l4": round(float(counter[0, 2, 0]) * 1e3, 6),
        "3 b) top height": round(float(counter[-1, 0, 2]) * 1e3, 6),
    }
    return record(expected, computed, unit="mm")


@register(
    _AFILS, f"{_60118_A1} 10.2", "Lower end of the 3 dB commissioning window, mA/m"
)
def _chk_commissioning_low() -> Outcome:
    low = float(ea.field_strength(-3.0)) * 1e3
    return numeric(
        ref.IEC60118_4_A1_COMMISSIONING_MA_PER_M[0], low, 0.5, unit="mA/m", places=1
    )


@register(
    _AFILS, f"{_60118_A1} 10.2", "Upper end of the 3 dB commissioning window, mA/m"
)
def _chk_commissioning_high() -> Outcome:
    high = float(ea.field_strength(3.0)) * 1e3
    return numeric(
        ref.IEC60118_4_A1_COMMISSIONING_MA_PER_M[1],
        high,
        1.0,
        unit="mA/m",
        places=1,
        expected_label="566 mA/m (+/-1: printed as 400 sqrt(2), 565 at +3 dB)",
    )


@register(
    _AFILS, f"{_60118_A1} Table 4", "Programme material and overload test frequency"
)
def _chk_table4() -> Outcome:
    expected: dict[str, float] = {}
    computed: dict[str, float] = {}
    for key, limit, test in ref.IEC60118_4_A1_TABLE4:
        row = ea.OVERLOAD_TEST_FREQUENCIES[key]
        expected[f"{key} limit"] = limit
        expected[f"{key} test"] = test
        computed[f"{key} limit"] = row.power_bandwidth_limit_hz
        computed[f"{key} test"] = row.test_frequency_hz
    return record(expected, computed, unit="Hz")


@register(
    _AFILS,
    f"{_60118_A1} 10.3.2",
    "Overload test current 7 dB below the one for the required field",
)
def _chk_overload_offset() -> Outcome:
    result = ea.verify_amplifier_overload(3.0, ea.loop_impedance(0.69, 109e-6), 20.0)
    offset = 20.0 * math.log10(result.test_current_a / 3.0)
    return numeric(
        ref.IEC60118_4_A1_OVERLOAD_OFFSET_DB, offset, 1e-9, unit="dB", places=3
    )


@register(
    _AFILS,
    f"{_60118_A1} 10.3.2",
    "Sweep end where the voltage of a 0,69 ohm, 109 uH loop doubles, Hz",
)
def _chk_overload_doubling() -> Outcome:
    resistance, inductance = 0.69, 109e-6
    result = ea.verify_amplifier_overload(
        3.0, ea.loop_impedance(resistance, inductance), 20.0, programme="speech"
    )
    w1 = 2.0 * math.pi * 1000.0 * inductance
    closed = math.sqrt(3.0 * resistance**2 + 4.0 * w1**2) / (2.0 * math.pi * inductance)
    return numeric(
        closed,
        result.doubling_frequency_hz,
        1e-6,
        unit="Hz",
        places=3,
        expected_label=f"{closed:.3f} Hz, where |Z| is twice its 1 kHz value",
    )


@register(
    _AFILS,
    f"{_60118_A1} 10.3.3",
    "No clipping at the Table 4 frequency, judged there when the sweep runs past",
)
def _chk_overload_verdict() -> Outcome:
    resistance, inductance = 2.0, 109e-6
    impedance = ea.loop_impedance(resistance, inductance)
    at_table_4 = 10.0 ** (ref.IEC60118_4_A1_OVERLOAD_OFFSET_DB / 20.0) * float(
        impedance.at(2500.0)
    )

    def verdict(compliance: float) -> bool:
        return ea.verify_amplifier_overload(
            1.0, impedance, compliance, programme="transient_speech"
        ).passes

    return _window_row(
        {
            "compliance at the 2,5 kHz voltage": (True, verdict(at_table_4)),
            "compliance 0,1 % below it": (False, verdict(0.999 * at_table_4)),
        }
    )


@register(_AFILS, f"{_60118_A1} 10.4.7", "System noise: -47 dB ceiling or 1 dB rise")
def _chk_system_noise() -> Outcome:
    ceiling = ref.IEC60118_4_A1_SYSTEM_NOISE_CEILING_DB
    rise = ref.IEC60118_4_A1_SYSTEM_NOISE_RISE_DB

    def verdict(off: float, on: float) -> bool:
        return ea.verify_induction_loop_system(
            [0.0], background_noise_levels_db=[off], system_noise_levels_db=[on]
        ).passes

    return _window_row(
        {
            "SNR 55 dB, on at -47 dB": (True, verdict(-55.0, ceiling)),
            "SNR 55 dB, on at -46,99 dB": (False, verdict(-55.0, ceiling + 0.01)),
            "SNR 40 dB, on 1 dB up": (True, verdict(-40.0, -40.0 + rise)),
            "SNR 40 dB, on 1,01 dB up": (False, verdict(-40.0, -40.0 + rise + 0.01)),
            # -32,7 + 1 is -31,700 000 000 000 003 in binary.
            "SNR 32,7 dB, on at -31,7 dB": (True, verdict(-32.7, -31.7)),
        }
    )


# ---------------------------------------------------------------------------
# IEC 60118-4:2014 Annex E: the loop, the telecoil and the units
# ---------------------------------------------------------------------------


def _e1_formula(current: float, side: float) -> float:
    """E.1 as printed: H = 2 sqrt(2) I / (pi d), in A/m."""
    return 2.0 * math.sqrt(2.0) * current / (math.pi * side)


@register(
    _AFILS,
    f"{_60118} E.1",
    "Centre field of a 5 m square loop by Biot-Savart, against 2 sqrt(2) I/(pi d)",
)
def _chk_centre_field() -> Outcome:
    side, current = 5.0, 3.0
    exact = float(
        ea.rectangular_loop_field(current, side, side, 0.0, 0.0, 0.0).h_z_a_per_m
    )
    return numeric(
        _e1_formula(current, side), exact, 1e-12, rel=True, unit="A/m", places=6
    )


@register(
    _AFILS,
    f"{_60118} E.1",
    "Centre field of a 10 m by 15 m loop with d = sqrt(d1 d2), as E.1 prints it",
)
def _chk_centre_field_rectangle() -> Outcome:
    d1, d2, current = 10.0, 15.0, 3.0
    computed = ea.loop_centre_field(current, d1, width_m=d2)
    return numeric(
        _e1_formula(current, math.sqrt(d1 * d2)),
        computed,
        1e-12,
        rel=True,
        unit="A/m",
        places=6,
    )


def _figure_e2_row(component: str, position: float) -> Outcome:
    length, width, height = ref.IEC60118_4_FIGURE_E2B_LOOP
    y = position / 100.0 * width - width / 2.0
    field = ea.rectangular_loop_field(1.0, length, width, 0.0, y, height)
    centre = float(
        ea.rectangular_loop_field(1.0, length, width, 0.0, 0.0, 0.0).h_z_a_per_m
    )
    value = field.h_z_a_per_m if component == "vertical" else field.h_y_a_per_m
    level = 20.0 * math.log10(abs(float(value)) / centre)
    printed = ref.IEC60118_4_FIGURE_E2B_DB[(component, position)]
    return numeric(
        printed,
        level,
        0.5,
        unit="dB",
        places=2,
        expected_label=f"{printed:.1f} dB read off the curve (+/-0,5)",
    )


def _register_figure_e2() -> None:
    """The read points of Figure E.2 b), across the loop's width."""
    for component, position in sorted(ref.IEC60118_4_FIGURE_E2B_DB):
        register(
            _AFILS,
            f"{_60118} Figure E.2 b)",
            f"{component.capitalize()} component of a 15 by 10 loop at 1,2 units, "
            f"{position:g} % across its width".replace(".", ","),
        )(functools.partial(_figure_e2_row, component, position))


_register_figure_e2()


def _figure_h1_row(aspect: float) -> Outcome:
    printed = ref.IEC60118_4_FIGURE_H1_AT_10_M_A[aspect]
    computed = ea.loop_current(10.0 * aspect, 10.0)
    return numeric(
        printed,
        computed,
        0.03,
        unit="A",
        places=3,
        expected_label=f"{printed:.2f} A read off the curve (+/-0,03)",
    )


def _register_figure_h1() -> None:
    """The ends of the five curves of Figure H.1, at a 10 m shorter side."""
    for aspect in sorted(ref.IEC60118_4_FIGURE_H1_AT_10_M_A):
        register(
            _AFILS,
            f"{_60118} Figure H.1",
            "Current for 400 mA/m 1,4 m above a 10 m loop of aspect ratio "
            + f"{aspect:g}".replace(".", ","),
        )(functools.partial(_figure_h1_row, aspect))


_register_figure_h1()


@register(
    _AFILS,
    f"{_62489} 5.4.10.2",
    "Loop current for 400 mA/m 1,4 m above a 3-turn 6 m by 2 m loop, by Biot-Savart",
)
def _chk_loop_current_rectangle() -> Outcome:
    height = ref.IEC62489_1_FIELD_HEIGHT_M
    current = ea.loop_current(6.0, 2.0, turns=3)
    field = float(
        ea.rectangular_loop_field(
            current, 6.0, 2.0, 0.0, 0.0, height, turns=3
        ).h_z_a_per_m
    )
    return numeric(
        ref.IEC60118_4_REFERENCE_A_PER_M, field, 1e-12, rel=True, unit="A/m", places=6
    )


@register(_AFILS, f"{_60118} E.2", "Telecoil response 45 degrees off axis")
def _chk_telecoil_45() -> Outcome:
    computed = float(ea.telecoil_response(45.0))
    return numeric(
        ref.IEC60118_4_TELECOIL_DB[45.0], computed, 0.05, unit="dB", places=2
    )


@register(_AFILS, f"{_60118} E.2", "Telecoil response 70 degrees off axis")
def _chk_telecoil_70() -> Outcome:
    computed = float(ea.telecoil_response(70.0))
    return numeric(
        ref.IEC60118_4_TELECOIL_DB[70.0], computed, 0.05, unit="dB", places=2
    )


@register(
    _AFILS,
    f"{_60118} E.3",
    "Loop impedance over resistance where the reactance equals it",
)
def _chk_corner_factor() -> Outcome:
    impedance = ea.loop_impedance(0.69, 109e-6)
    factor = (
        float(impedance.at(impedance.corner_frequency_hz)) / impedance.resistance_ohm
    )
    return numeric(ref.IEC60118_4_E3_CORNER_FACTOR, factor, 0.015, places=3)


@register(_AFILS, f"{_60118} E.6", "One oersted in amperes per metre")
def _chk_oersted() -> Outcome:
    oersted = 1e-4 / float(ea.magnetic_flux_density(1.0))
    return numeric(
        ref.IEC60118_4_E6_OERSTED_A_PER_M, oersted, 0.005, unit="A/m", places=3
    )


@register(_AFILS, f"{_60118} E.6", "Flux density of 1 A/m in air, microtesla")
def _chk_flux_density() -> Outcome:
    microtesla = float(ea.magnetic_flux_density(1.0)) * 1e6
    return numeric(
        ref.IEC60118_4_E6_MICROTESLA_PER_A_PER_M,
        microtesla,
        0.001,
        unit="µT",
        places=4,
        expected_label="1,256 µT (+/-0,001: the print truncates 1,2566, see ERRATA)",
    )


# ---------------------------------------------------------------------------
# IEC 62489-1:2010+A1:2014: Table B.1
# ---------------------------------------------------------------------------


def _perimeter(dims: tuple[float, ...]) -> float:
    return math.pi * dims[0] if len(dims) == 1 else 2.0 * (dims[0] + dims[1])


def _register_table_b1() -> None:
    """Resistance, inductance and impedance of every loop of Table B.1."""
    for (
        name,
        dims,
        turns,
        printed_perimeter,
        area,
        resistance,
        inductance,
        z2k,
        z5k,
    ) in ref.IEC62489_1_TABLE_B1:

        def check_r(
            dims: tuple[float, ...] = dims,
            turns: int = turns,
            area: float = area,
            resistance: float = resistance,
            printed_perimeter: float = printed_perimeter,
        ) -> Outcome:
            perimeter = _perimeter(dims)
            computed = ea.loop_resistance(perimeter, area, turns=turns)
            label = f"{resistance:.2f} ohm"
            if abs(perimeter - printed_perimeter) > 0.051:  # noqa: PLR2004 - rounding of the column
                label += f" (with the {perimeter:.1f} m its sides give, see ERRATA)"
            return numeric(
                resistance, computed, 0.005, unit="ohm", places=3, expected_label=label
            )

        register(
            _AFILS,
            f"{_62489} Table B.1",
            f"{name}: resistance, 1/58 ohm mm2/m copper",
        )(check_r)

        if name in ref.IEC62489_1_TABLE_B1_INDUCTANCE_REPRODUCED:

            def check_l(
                dims: tuple[float, ...] = dims,
                turns: int = turns,
                area: float = area,
                inductance: float = inductance,
            ) -> Outcome:
                computed = 1e6 * ea.rectangular_loop_inductance(
                    dims[0], dims[1], area, turns=turns, internal_inductance=False
                )
                return numeric(inductance, computed, 0.5, unit="µH", places=2)

            register(
                _AFILS,
                f"{_62489} Table B.1",
                f"{name}: inductance by Grover's Formula (58), no internal term",
            )(check_l)

        for frequency, printed in ((2000.0, z2k), (5000.0, z5k)):

            def check_z(
                resistance: float = resistance,
                inductance: float = inductance,
                frequency: float = frequency,
                printed: float = printed,
            ) -> Outcome:
                central = float(
                    ea.loop_impedance(resistance, inductance * 1e-6).at(frequency)
                )
                corners = [
                    float(
                        ea.loop_impedance(resistance + dr, (inductance + dl) * 1e-6).at(
                            frequency
                        )
                    )
                    for dr in (-0.005, 0.005)
                    for dl in (-0.5, 0.5)
                ]
                # The printed impedance rounds a value computed from the
                # unrounded R and L: allow the rounding of both, and its own.
                tol = 0.005 + max(abs(c - central) for c in corners)
                return numeric(printed, central, tol, unit="ohm", places=3)

            register(
                _AFILS,
                f"{_62489} Table B.1",
                f"{name}: impedance at {frequency / 1000:g} kHz from the printed R and L",
            )(check_z)


_register_table_b1()


# ---------------------------------------------------------------------------
# IEC 62489-1:2010+A1:2014: the amplifier; IEC 60028: copper
# ---------------------------------------------------------------------------


@register(
    _AFILS,
    "IEC 60028:1925 clause I",
    "Resistivity of standard annealed copper at 20 degC, from 1 m of 1 mm2",
)
def _chk_copper() -> Outcome:
    # The resistance of one metre of one square millimetre, in ohms, is the
    # resistivity in ohm mm2/m.
    per_metre = ea.loop_resistance(1.0, 1.0)
    return numeric(
        ref.IEC60028_COPPER_OHM_MM2_PER_M,
        per_metre,
        1e-12,
        rel=True,
        unit="ohm·mm²/m",
        places=6,
    )


@register(
    _AFILS,
    f"{_62489} 5.4.7.2",
    "Maximum output current: the voltage across the resistance over its value "
    "where the THD reaches its rating",
)
def _chk_maximum_output_current() -> Outcome:
    resistance, rated = 0.47, 1.0
    voltage = [1.0, 2.0, 3.0, 3.5]
    thd = [0.2, 0.4, 0.8, 1.6]
    result = ea.maximum_output_current(
        voltage, thd, load_resistance_ohm=resistance, rated_thd_percent=rated
    )
    # 1 % lies a quarter of the way from 0,8 % at 3 V to 1,6 % at 3,5 V.
    closed = (3.0 + 0.25 * 0.5) / resistance
    return numeric(
        closed, result.maximum_current_a, 1e-12, rel=True, unit="A", places=4
    )


@register(
    _AFILS,
    f"{_62489} 5.4.8.2",
    "Compliance voltage of a sine, the average peak over sqrt(2)",
)
def _chk_compliance_voltage() -> Outcome:
    t = np.arange(4800) / _FS
    amplitude = 14.0
    voltage = ea.compliance_voltage(amplitude * np.sin(2.0 * np.pi * 1000.0 * t))
    return numeric(amplitude / math.sqrt(2.0), voltage, 1e-9, unit="V", places=4)


@register(
    _AFILS, f"{_62489} 5.4.14.1", "In-phase part of a quadrature network at 85 degrees"
)
def _chk_quadrature_cos() -> Outcome:
    error = ea.quadrature_phase_error([100.0, 1000.0, 5000.0], [90.0, 85.0, 90.0])
    in_phase = math.sin(math.radians(error.max_deviation_deg))
    return numeric(ref.IEC62489_1_QUADRATURE_EXAMPLE_COS, in_phase, 5e-4, places=4)


@register(_AFILS, f"{_62489} 5.4.14.1", "Rise where the fields add at 85 degrees")
def _chk_quadrature_rise() -> Outcome:
    error = ea.quadrature_phase_error([100.0, 1000.0, 5000.0], [90.0, 85.0, 90.0])
    return numeric(
        ref.IEC62489_1_QUADRATURE_EXAMPLE_DB,
        error.level_increase_db,
        0.01,
        unit="dB",
        places=3,
    )


@register(_AFILS, f"{_62489} 5.4.14.1", "Fall where the fields subtract at 85 degrees")
def _chk_quadrature_fall() -> Outcome:
    error = ea.quadrature_phase_error([100.0, 1000.0, 5000.0], [90.0, 85.0, 90.0])
    closed = 20.0 * math.log10(1.0 - math.cos(math.radians(85.0)))
    return numeric(
        closed,
        error.level_decrease_db,
        1e-9,
        unit="dB",
        places=3,
        expected_label=f"{closed:.3f} dB, 20 lg(1 - cos 85) (printed as 0,72 dB, see ERRATA)",
    )


@register(
    _AFILS,
    f"{_A2_DRAFT} Annex D, D.1.2 and D.1.3",
    "Neck-loop types of the draft: DC resistance and input voltage for 400 mA/m",
)
def _chk_neck_loop_types() -> Outcome:
    tol = ref.IEC62489_1_A2_DRAFT_TYPE1_TOL_PERCENT / 100.0
    nominal = ref.IEC62489_1_A2_DRAFT_TYPE1_OHM
    limit = ref.IEC62489_1_A2_DRAFT_MAX_INPUT_V

    def verdict(resistance: float, voltage: float, kind: int) -> bool:
        return ea.verify_neck_loop(resistance, voltage, neck_loop_type=kind).passes

    return _window_row(
        {
            "type 1 at -5 %": (True, verdict(nominal * (1 - tol), limit, 1)),
            "type 1 at +5 %": (True, verdict(nominal * (1 + tol), limit, 1)),
            "type 1 at +5,1 %": (False, verdict(nominal * (1 + tol + 0.001), limit, 1)),
            "type 2 at 32 ohm": (
                True,
                verdict(ref.IEC62489_1_A2_DRAFT_TYPE2_MIN_OHM, limit, 2),
            ),
            "type 2 below 32 ohm": (False, verdict(31.99, limit, 2)),
            "1,07 V for 400 mA/m": (False, verdict(nominal, limit + 0.01, 1)),
        }
    )
