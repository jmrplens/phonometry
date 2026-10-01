#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Qualification of a free field and the reference sound source.

ISO 26101:2017 qualifies an anechoic or hemi-anechoic room by the inverse
square law, ISO 3745:2012 Annex A as Amendment 1:2017 wrote it holds that
qualification to the criteria of the precision method, and ISO 6926:2016 sets
what a reference sound source must do and how its sound power is calibrated.
None of the three prints a worked example, so the rows below read the cells
the standards do print (Table A.1 in both, Table B.1 of ISO 26101, Tables 1
and 2 of ISO 6926) and anchor every formula in a closed form: an exact
inverse-square field qualifies at every distance, a field with one incoherent
image source deviates by exactly the known excess, and each correction of
ISO 6926 is its printed expression evaluated by hand.

The printed limits of the verdicts are read at their edges: a value on the
limit passes and one past it fails.

Oracles, read on the rasterised page: ISO 26101:2017 (second edition),
5.1.2.2 c) on printed folio 3 (PDF page 9), Formula (1) on folio 4 (PDF page
10), 5.1.4.3 on folio 5 (PDF page 11), Formulae (2) to (4) on folios 6 and 7
(PDF pages 12 and 13), Table A.1 on folio 9 (PDF page 15), A.4.3 on folio 11
(PDF page 17), Table B.1 on folio 13 (PDF page 19); ISO 3745:2012/Amd.1:2017,
Table A.1 on folio 2 (PDF page 6), A.2.3 to A.2.5 on folios 2 and 3 (PDF pages
6 and 7), A.3.3 on folio 4 (PDF page 8) and A.4.3 on folio 5 (PDF page 9);
ISO 6926:2016 (third edition), 5.2 and Table 1 on folio 5 (PDF page 11), 5.4 to
5.6 on folios 5 and 6 (PDF pages 11 and 12), Formulae (1) and (2) on folio 11
(PDF page 17), 8.4 and C3 on folio 12 (PDF page 18), Table 2 on folio 14 (PDF
page 20), Annex A on folios 16 and 17 (PDF pages 22 and 23), Table B.1 on
folio 18 (PDF page 24); ISO 3741:2010, Equation (21) on folio 23 (PDF page 32).
"""

from __future__ import annotations

import math

import numpy as np

from phonometry import emission

from ..registry import Outcome, count, numeric, record, register

_DOMAIN = "Free-field qualification & reference sound sources"
_GRID = (
    100.0,
    125.0,
    250.0,
    500.0,
    1000.0,
    2000.0,
    4000.0,
    5000.0,
    6300.0,
    8000.0,
    10000.0,
)
_DIRECTIONS = (
    (1.0, 1.0, 1.0),
    (1.0, 1.0, 0.3),
    (0.0, 1.0, 0.5),
    (1.0, 0.0, 0.2),
    (-1.0, 0.5, 0.6),
    (0.3, -1.0, 0.8),
)
_THIRDS = (
    100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0,
    1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0, 10000.0,
)  # fmt: skip


def _cells(frequencies: tuple[float, ...], values: np.ndarray) -> dict[str, float]:
    return {f"{f:g} Hz": float(v) for f, v in zip(frequencies, values, strict=True)}


@register(
    _DOMAIN,
    "ISO 26101:2017 Table A.1 / ISO 3745:2012/Amd.1:2017 Table A.1",
    "Allowable deviation from the inverse square law, anechoic room, at "
    "630, 800, 5\u202f000 and 6\u202f300 Hz, dB",
)
def _chk_table_a1_anechoic() -> Outcome:
    freqs = (630.0, 800.0, 5000.0, 6300.0)
    return record(
        _cells(freqs, np.array([1.5, 1.0, 1.0, 1.5])),
        _cells(freqs, emission.inverse_square_law_tolerance_db(freqs, room="anechoic")),
        unit="dB",
    )


@register(
    _DOMAIN,
    "ISO 26101:2017 Table A.1 / ISO 3745:2012/Amd.1:2017 Table A.1",
    "Allowable deviation from the inverse square law, hemi-anechoic room, at "
    "630, 800, 5\u202f000 and 6\u202f300 Hz, dB",
)
def _chk_table_a1_hemi() -> Outcome:
    freqs = (630.0, 800.0, 5000.0, 6300.0)
    return record(
        _cells(freqs, np.array([2.5, 2.0, 2.0, 3.0])),
        _cells(
            freqs, emission.inverse_square_law_tolerance_db(freqs, room="hemi-anechoic")
        ),
        unit="dB",
    )


@register(
    _DOMAIN,
    "ISO 26101:2017 Table B.1",
    "Allowable deviation in directionality of the test source, anechoic and "
    "hemi-anechoic, at 630, 800, 6\u202f300 and 12\u202f500 Hz, dB",
)
def _chk_table_b1() -> Outcome:
    freqs = (630.0, 800.0, 6300.0, 12500.0)
    anechoic = emission.directionality_tolerance_db(freqs, room="anechoic")
    hemi = emission.directionality_tolerance_db(freqs, room="hemi-anechoic")
    computed = {f"anechoic {k}": v for k, v in _cells(freqs, anechoic).items()}
    computed |= {f"hemi-anechoic {k}": v for k, v in _cells(freqs, hemi).items()}
    expected = {
        f"anechoic {k}": v
        for k, v in _cells(freqs, np.array([1.5, 2.0, 2.5, 5.0])).items()
    }
    expected |= {
        f"hemi-anechoic {k}": v
        for k, v in _cells(freqs, np.array([2.0, 2.5, 3.0, 5.0])).items()
    }
    return record(expected, computed, unit="dB")


@register(
    _DOMAIN,
    "ISO 3745:2012/Amd.1:2017 A.2.3",
    "Frequencies evaluated from 100 Hz to 10\u202f000 Hz: one-third octaves below "
    "125 Hz and above 4\u202f000 Hz, octave mid-bands between",
)
def _chk_a23_frequencies() -> Outcome:
    got = emission.qualification_frequencies_hz()
    matching = sum(
        1 for a, b in zip(_GRID, got, strict=False) if math.isclose(a, float(b))
    )
    return count(
        matching if got.size == len(_GRID) else 0,
        len(_GRID),
        subject="frequencies",
    )


def _free_field_fit(distances: np.ndarray) -> emission.InverseSquareLawResult:
    level = 90.0 - 20.0 * np.log10(distances)
    grid = np.repeat(level[:, None], len(_GRID), axis=1)
    traverses = [
        emission.MicrophoneTraverse.along(u, distances, grid) for u in _DIRECTIONS
    ]
    return emission.inverse_square_law_deviations(
        traverses, frequencies_hz=_GRID, room="anechoic"
    )


@register(
    _DOMAIN,
    "ISO 26101:2017 Formulae (2) and (4)",
    "An exact inverse-square field, six traverses 0,30 m to 3,00 m: the "
    "qualified radius is the end of the traverses, m (closed form)",
)
def _chk_exact_field_radius() -> Outcome:
    d = np.arange(0.30, 3.0001, 0.02)
    fit = _free_field_fit(d)
    return numeric(
        float(d[-1]), fit.maximum_qualified_radius_m, 1e-9, unit="m", places=4
    )


@register(
    _DOMAIN,
    "ISO 26101:2017 Formulae (2) and (4)",
    "The same field: the largest deviation from the inverse square law, dB "
    "(closed form)",
)
def _chk_exact_field_deviation() -> Outcome:
    fit = _free_field_fit(np.arange(0.30, 3.0001, 0.02))
    return numeric(
        0.0, float(np.max(fit.largest_deviation_db)), 1e-9, unit="dB", places=4
    )


@register(
    _DOMAIN,
    "ISO 26101:2017 Formula (3)",
    "Starting value of b for L_pi = 85,0 / 80,5 / 76,0 / 73,5 dB at 0,5 / 1,0 / "
    "1,5 / 2,0 m, the mean of 20 lg(r_i/r0) + L_pi, dB",
)
def _chk_formula_3() -> Outcome:
    d = np.array([0.5, 1.0, 1.5, 2.0])
    levels = np.array([85.0, 80.5, 76.0, 73.5])
    fit = emission.inverse_square_law_deviations(
        [emission.MicrophoneTraverse.along((1, 0, 0), d, levels)],
        frequencies_hz=[1000.0],
        room="anechoic",
    )
    expected = (np.sum(20.0 * np.log10(d)) + np.sum(levels)) / d.size
    return numeric(float(expected), float(fit.initial_source_strength_db[0, 0]), 1e-9,
                   unit="dB", places=4)  # fmt: skip


def _reflection() -> tuple[np.ndarray, np.ndarray, float]:
    """A fully reflecting wall 2,5 m ahead, as an incoherent image source."""
    rho2, wall, tol = 1.0, 2.5, 1.0
    d = np.arange(0.50, 2.4001, 0.05)
    excess = 10.0 * np.log10(1.0 + rho2 * (d / (2.0 * wall - d)) ** 2)
    q1 = d[0] / (2.0 * wall - d[0])
    q = math.sqrt(((1.0 + rho2 * q1**2) * 10.0 ** (2.0 * tol / 10.0) - 1.0) / rho2)
    return d, excess, 2.0 * wall * q / (1.0 + q)


@register(
    _DOMAIN,
    "ISO 26101:2017 Formulae (2) and (4)",
    "One incoherent reflection, rho^2 = 1 from a wall 2,5 m ahead, 1 kHz in "
    "an anechoic room: the qualified distance is the last point before "
    "D(r) - D(r1) = 2 dB, m (closed form)",
)
def _chk_reflection_radius() -> Outcome:
    d, excess, limit = _reflection()
    traverse = emission.MicrophoneTraverse.along(
        (1, 0, 0), d, 90.0 - 20.0 * np.log10(d) + excess
    )
    fit = emission.inverse_square_law_deviations(
        [traverse], frequencies_hz=[1000.0], room="anechoic"
    )
    expected = float(d[d <= limit][-1])
    return numeric(
        expected, float(fit.traverse_radius_m[0, 0]), 1e-9, unit="m", places=4
    )


@register(
    _DOMAIN,
    "ISO 26101:2017 Formulae (2) and (4)",
    "The same reflection: the spread of the deviations within the qualified "
    "distance equals the spread of the excess D(r), dB (closed form)",
)
def _chk_reflection_spread() -> Outcome:
    d, excess, limit = _reflection()
    traverse = emission.MicrophoneTraverse.along(
        (1, 0, 0), d, 90.0 - 20.0 * np.log10(d) + excess
    )
    fit = emission.inverse_square_law_deviations(
        [traverse], frequencies_hz=[1000.0], room="anechoic"
    )
    inside = d <= limit
    return numeric(float(np.ptp(excess[inside])),
                   float(np.ptp(fit.deviations_db[0][inside, 0])), 1e-9,
                   unit="dB", places=4)  # fmt: skip


@register(
    _DOMAIN,
    "ISO 26101:2017 Formula (1)",
    "A source drifting by 0 to 0,8 dB along the traverse, seen by the monitor "
    "microphone: the largest deviation left after the correction, dB",
)
def _chk_formula_1() -> Outcome:
    d = np.arange(0.3, 2.0, 0.1)
    drift = np.linspace(0.0, 0.8, d.size)
    traverse = emission.MicrophoneTraverse.along(
        (1, 0, 0),
        d,
        90.0 - 20.0 * np.log10(d) + drift,
        monitor_levels_db=70.0 + drift,
    )
    fit = emission.inverse_square_law_deviations(
        [traverse], frequencies_hz=[1000.0], room="anechoic"
    )
    return numeric(0.0, float(np.max(np.abs(fit.deviations_db[0]))), 1e-9, unit="dB",
                   places=4)  # fmt: skip


@register(
    _DOMAIN,
    "ISO 6926:2016 Table 1",
    "Largest standard deviation under repeatability conditions at 80, 160 and "
    "200 Hz, read as the limit of a 3-repetition check, dB",
)
def _chk_6926_table_1() -> Outcome:
    freqs = (80.0, 160.0, 200.0)
    lw = np.full(len(_THIRDS), 90.0)
    verdict = emission.verify_reference_sound_source(
        lw, frequencies_hz=_THIRDS, repeated_levels_db=np.vstack([lw, lw, lw]),
        directivity_index_db=np.zeros(len(_THIRDS)),
    )  # fmt: skip
    limits = dict(zip(_THIRDS, verdict.repeatability_limit_db, strict=True))
    extended = emission.verify_reference_sound_source(
        np.full(3, 90.0), frequencies_hz=(50.0, 63.0, 80.0),
        repeated_levels_db=np.full((3, 3), 90.0), directivity_index_db=np.zeros(3),
    )  # fmt: skip
    computed = {
        "80 Hz": float(extended.repeatability_limit_db[-1]),
        "160 Hz": float(limits[160.0]),
        "200 Hz": float(limits[200.0]),
    }
    return record(_cells(freqs, np.array([0.8, 0.4, 0.2])), computed, unit="dB")


@register(
    _DOMAIN,
    "ISO 6926:2016 Formula (1)",
    "sigma_r of 80,0 / 80,2 / 79,9 dB about their energy average, dB (closed form)",
)
def _chk_6926_formula_1() -> Outcome:
    levels = np.array([80.0, 80.2, 79.9])
    mean = 10.0 * math.log10(float(np.mean(10.0 ** (levels / 10.0))))
    expected = math.sqrt(float(np.sum((levels - mean) ** 2)) / 2.0)
    got = float(emission.repeatability_standard_deviation(levels)[0])
    return numeric(expected, got, 1e-12, unit="dB", places=5)


@register(
    _DOMAIN,
    "ISO 6926:2016 Table 2",
    "Standard deviation of reproducibility, one-third octave rows, three "
    "columns, 15 cells",
)
def _chk_6926_table_2() -> Outcome:
    printed = {
        80.0: (2.0, 2.0, 2.5),
        160.0: (0.8, 0.8, 1.0),
        3150.0: (0.3, 0.5, 0.3),
        10000.0: (0.3, 1.0, 0.3),
        20000.0: (0.3, 1.0, 0.4),
    }
    matching = 0
    for frequency, (paths, fixed, reverberation) in printed.items():
        got = (
            emission.reference_source_reproducibility_db(
                [frequency], environment="hemi-anechoic", arrangement="paths"
            )[0],
            emission.reference_source_reproducibility_db(
                [frequency], environment="hemi-anechoic", arrangement="fixed"
            )[0],
            emission.reference_source_reproducibility_db(
                [frequency], environment="reverberation-room"
            )[0],
        )
        matching += sum(
            1
            for a, b in zip((paths, fixed, reverberation), got, strict=True)
            if math.isclose(a, float(b))
        )
    return count(matching, 15, subject="cells")


@register(
    _DOMAIN,
    "ISO 6926:2016 Annex A, Formulae (A.2) to (A.5)",
    "C2 at 30 degC and 95 kPa for a monopole below and above its knee, an "
    "aerodynamic dipole and a source of unknown radiation, dB (closed form)",
)
def _chk_6926_annex_a() -> Outcome:
    pressure = -10.0 * math.log10(95.0 / 101.325)
    ratio = math.log10(303.15 / 296.0)
    monopole = emission.radiation_impedance_correction(
        temperature_c=30.0, static_pressure_kpa=95.0, radiation="monopole",
        frequencies_hz=[100.0, 1000.0], knee_frequency_hz=500.0,
    )  # fmt: skip
    dipole = emission.radiation_impedance_correction(
        temperature_c=30.0, static_pressure_kpa=95.0, radiation="dipole",
        frequencies_hz=[1000.0], knee_frequency_hz=500.0,
    )  # fmt: skip
    unknown = emission.radiation_impedance_correction(
        temperature_c=30.0, static_pressure_kpa=95.0
    )
    expected = {
        "(A.2)": round(pressure + 15.0 * ratio, 9),
        "(A.3)": round(pressure + 5.0 * ratio, 9),
        "(A.4)": round(pressure + 25.0 * ratio, 9),
        "(A.5)": round(pressure + 7.5 * ratio, 9),
    }
    computed = {
        "(A.2)": round(float(monopole[0]), 9),
        "(A.3)": round(float(monopole[1]), 9),
        "(A.4)": round(float(dipole[0]), 9),
        "(A.5)": round(float(unknown[0]), 9),
    }
    return record(expected, computed, unit="dB")


@register(
    _DOMAIN,
    "ISO 6926:2016 Formula (2)",
    "L_W of a uniform 80 dB over the 2 m hemisphere at the reference "
    "conditions, with a(f) = 0,01 dB/m, 1 kHz, dB (closed form)",
)
def _chk_6926_formula_2() -> Outcome:
    calibration = emission.reference_source_calibration(
        np.full((20, len(_THIRDS)), 80.0),
        frequencies_hz=_THIRDS,
        arrangement="fixed",
        conditions=emission.CalibrationConditions(air_absorption_db_per_m=0.01),
    )
    a0 = 0.02
    expected = (
        80.0
        + 10.0 * math.log10(2.0 * math.pi * 4.0)
        + 5.0 * math.log10(296.15 / 314.0)
        + 7.5 * math.log10(296.15 / 296.0)
        + a0 * (1.0053 - 0.0012 * a0) ** 1.6
    )
    got = float(calibration.sound_power_level_db[_THIRDS.index(1000.0)])
    return numeric(expected, got, 1e-9, unit="dB", places=4)


def _spectrum_verdict(lw: np.ndarray, freqs: tuple[float, ...]) -> bool:
    return bool(
        emission.verify_reference_sound_source(
            lw, frequencies_hz=freqs, repeated_levels_db=np.vstack([lw, lw, lw]),
            directivity_index_db=np.zeros(len(freqs)),
        ).spectrum_met
    )  # fmt: skip


@register(
    _DOMAIN,
    "ISO 6926:2016 5.4",
    "Spectra at the edges of 5.4: a 12,0 dB range and a 3,0 dB step pass, "
    "12,5 dB and 3,1 dB fail; extended to 50 Hz, steps of 4,0 dB pass and one "
    "of 4,1 dB fails, and with every step within 4 dB a 16,0 dB range passes "
    "and 16,5 dB fails",
)
def _chk_6926_spectrum() -> Outcome:
    n = len(_THIRDS)
    within = np.linspace(80.0, 92.0, n)
    wide = np.linspace(80.0, 92.5, n)
    step = np.full(n, 90.0)
    step[10] = 93.0
    steep = np.full(n, 90.0)
    steep[10] = 93.1
    ext = (50.0, 63.0, 80.0, *_THIRDS)
    extended = np.concatenate([[76.0, 80.0, 84.0], np.full(n, 88.0)])
    steeper = np.concatenate([[75.9, 80.0, 84.0], np.full(n, 88.0)])
    # Every step within 4 dB and 3 dB: only the extended range decides.
    core = np.linspace(83.0, 88.5, n)
    on_limit = np.concatenate([[72.5, 76.5, 80.5], core])
    too_wide = np.concatenate([[72.0, 76.0, 80.0], core])
    expected = {
        "12,0 dB range": 1.0,
        "12,5 dB range": 0.0,
        "3,0 dB step": 1.0,
        "3,1 dB step": 0.0,
        "extended, 12 dB and 4 dB steps": 1.0,
        "extended, a 4,1 dB step": 0.0,
        "extended, 16,0 dB": 1.0,
        "extended, 16,5 dB": 0.0,
    }
    computed = {
        "12,0 dB range": float(_spectrum_verdict(within, _THIRDS)),
        "12,5 dB range": float(_spectrum_verdict(wide, _THIRDS)),
        "3,0 dB step": float(_spectrum_verdict(step, _THIRDS)),
        "3,1 dB step": float(_spectrum_verdict(steep, _THIRDS)),
        "extended, 12 dB and 4 dB steps": float(_spectrum_verdict(extended, ext)),
        "extended, a 4,1 dB step": float(_spectrum_verdict(steeper, ext)),
        "extended, 16,0 dB": float(_spectrum_verdict(on_limit, ext)),
        "extended, 16,5 dB": float(_spectrum_verdict(too_wide, ext)),
    }
    return record(expected, computed)


@register(
    _DOMAIN,
    "ISO 6926:2016 5.6.3",
    "Recalibration limit, 2,83 times Table 1, at 80, 125 and 1\u202f000 Hz, dB",
)
def _chk_6926_drift() -> Outcome:
    freqs = (80.0, 125.0, 1000.0)
    result = emission.verify_reference_source_drift(
        np.zeros(3), np.zeros(3), frequencies_hz=freqs
    )
    return record(
        _cells(freqs, np.round(2.83 * np.array([0.8, 0.4, 0.2]), 9)),
        _cells(freqs, np.round(result.limit_db, 9)),
        unit="dB",
    )


def _three_with_sigma(sigma_db: float) -> np.ndarray:
    """Three levels 80 - x, 80 and 80 + x whose sigma_r of Formula (1) is ``sigma_db``.

    sigma_r grows with x, so x is bisected to the last bit and taken on the
    side that reaches ``sigma_db``.
    """
    low, high = 0.0, 5.0
    for _ in range(200):
        middle = (low + high) / 2.0
        trial = np.array([80.0 - middle, 80.0, 80.0 + middle])
        if emission.repeatability_standard_deviation(trial)[0] < sigma_db:
            low = middle
        else:
            high = middle
    return np.array([80.0 - high, 80.0, 80.0 + high])


def _steady_enough(bands: tuple[float, ...], band: float, sigma_db: float) -> float:
    levels = np.full(len(bands), 90.0)
    repeated = np.vstack([levels, levels, levels])
    repeated[:, bands.index(band)] = _three_with_sigma(sigma_db) + 10.0
    verdict = emission.verify_reference_sound_source(
        levels,
        frequencies_hz=bands,
        repeated_levels_db=repeated,
        directivity_index_db=np.zeros(len(bands)),
    )
    return float(bool(verdict.stability_met))


@register(
    _DOMAIN,
    "ISO 6926:2016 Table 1",
    "At the edge of every row: three repetitions whose sigma_r of Formula (1) "
    "equals the limit pass and 0,01 dB more fail, at 80 Hz (0,8 dB), 160 Hz "
    "(0,4 dB) and 200 Hz (0,2 dB)",
)
def _chk_6926_table_1_edges() -> Outcome:
    extended = (50.0, 63.0, 80.0)
    cases = ((extended, 80.0, 0.8), (_THIRDS, 160.0, 0.4), (_THIRDS, 200.0, 0.2))
    expected: dict[str, float] = {}
    computed: dict[str, float] = {}
    for bands, band, limit in cases:
        on = f"{band:g} Hz, {limit:.2f} dB".replace(".", ",")
        past = f"{band:g} Hz, {limit + 0.01:.2f} dB".replace(".", ",")
        expected[on], expected[past] = 1.0, 0.0
        computed[on] = _steady_enough(bands, band, limit)
        computed[past] = _steady_enough(bands, band, limit + 0.01)
    return record(expected, computed)


@register(
    _DOMAIN,
    "ISO 6926:2016 5.6.3",
    "At the edge of every row of Table 1: a change of exactly 2,83 times it "
    "calls for no recalibration and 0,01 dB more does, at 80 Hz (2,264 dB), "
    "125 Hz (1,132 dB) and 1\u202f000 Hz (0,566 dB)",
)
def _chk_6926_drift_edges() -> Outcome:
    freqs = (80.0, 125.0, 1000.0)
    expected: dict[str, float] = {}
    computed: dict[str, float] = {}
    for index, (band, limit) in enumerate(zip(freqs, (2.264, 1.132, 0.566),
                                              strict=True)):  # fmt: skip
        for change, verdict in ((limit, 1.0), (limit + 0.01, 0.0)):
            name = f"{band:g} Hz, {change:.3f} dB".replace(".", ",")
            latest = np.zeros(len(freqs))
            latest[index] = change
            result = emission.verify_reference_source_drift(
                np.zeros(len(freqs)), latest, frequencies_hz=freqs
            )
            expected[name] = verdict
            computed[name] = float(result.passes)
    return record(expected, computed)


# --- the printed limits of the free-field verdict, at their edges -----------


def _exact_traverses(
    distances: np.ndarray,
    freqs: tuple[float, ...],
    directions: tuple[tuple[float, float, float], ...] = _DIRECTIONS,
    *,
    margin_db: float | None = None,
) -> list[emission.MicrophoneTraverse]:
    """Exact inverse-square traverses; ``margin_db`` above the background."""
    level = np.repeat((90.0 - 20.0 * np.log10(distances))[:, None], len(freqs), axis=1)
    return [
        emission.MicrophoneTraverse.along(
            u,
            distances,
            level,
            background_levels_db=None if margin_db is None else level - margin_db,
        )
        for u in directions
    ]


def _check(
    traverses: list[emission.MicrophoneTraverse],
    freqs: tuple[float, ...],
    room: str = "anechoic",
    **options: object,
) -> emission.FreeFieldCheck:
    fit = emission.inverse_square_law_deviations(
        traverses,
        frequencies_hz=freqs,
        room=room,  # type: ignore[arg-type]
    )
    return emission.check_free_field(fit, bandwidth="broadband", **options)  # type: ignore[arg-type]


_TRAVERSE = np.arange(0.30, 3.0001, 0.02)


@register(
    _DOMAIN,
    "ISO 3745:2012/Amd.1:2017 A.2.5",
    "Reflecting plane: an absorption coefficient of 0,06 passes and 0,07 "
    "fails; with 125 Hz the lowest band, a plane extending 0,75 m beyond the "
    "surface passes and 0,74 m fails, the 0,75 m binding over the 0,686 m "
    "quarter wavelength; with 100 Hz the lowest, the quarter wavelength of "
    "0,857\u202f5 m binds, and 0,857\u202f5 m passes and 0,857\u202f4 m fails",
)
def _chk_a25_plane() -> Outcome:
    def plane(freqs: tuple[float, ...], absorption: float, margin: float) -> float:
        check = _check(
            _exact_traverses(_TRAVERSE, freqs),
            freqs,
            "hemi-anechoic",
            reflecting_plane_absorption_coefficient=absorption,
            reflecting_plane_margin_m=margin,
        )
        return float(bool(check.reflecting_plane_met))

    from_125 = _GRID[1:]
    from_100 = (100.0, 1000.0)
    expected = {"0,06": 1.0, "0,07": 0.0, "0,75 m": 1.0, "0,74 m": 0.0,
                "0,857\u202f5 m": 1.0, "0,857\u202f4 m": 0.0}  # fmt: skip
    computed = {
        "0,06": plane(from_125, 0.06, 1.0),
        "0,07": plane(from_125, 0.07, 1.0),
        "0,75 m": plane(from_125, 0.02, 0.75),
        "0,74 m": plane(from_125, 0.02, 0.74),
        "0,857\u202f5 m": plane(from_100, 0.02, 0.8575),
        "0,857\u202f4 m": plane(from_100, 0.02, 0.8574),
    }
    return record(expected, computed)


@register(
    _DOMAIN,
    "ISO 3745:2012/Amd.1:2017 A.3.3",
    "Traverse paths: four fail, five and eight pass, nine fail; in a "
    "hemi-anechoic room a path 20 deg and 80 deg from the vertical passes, "
    "19,9 deg and 80,1 deg fail",
)
def _chk_a33_paths() -> Outcome:
    freqs = (1000.0,)
    many = (
        *_DIRECTIONS,
        (1.0, -1.0, 0.5),
        (-1.0, -1.0, 0.7),
        (-1.0, 0.0, 0.4),
    )
    computed = {
        f"{n} traverses": float(
            _check(
                _exact_traverses(_TRAVERSE, freqs, many[:n]), freqs
            ).traverse_count_met
        )
        for n in (4, 5, 8, 9)
    }
    for degrees, name in (
        (19.9, "19,9 deg"),
        (20.0, "20 deg"),
        (80.0, "80 deg"),
        (80.1, "80,1 deg"),
    ):
        path = (math.tan(math.radians(degrees)), 0.0, 1.0)
        check = _check(
            _exact_traverses(_TRAVERSE, freqs, (*_DIRECTIONS[:5], path)),
            freqs,
            "hemi-anechoic",
        )
        computed[name] = float(bool(check.path_angles_met))
    expected = {
        "4 traverses": 0.0,
        "5 traverses": 1.0,
        "8 traverses": 1.0,
        "9 traverses": 0.0,
        "19,9 deg": 0.0,
        "20 deg": 1.0,
        "80 deg": 1.0,
        "80,1 deg": 0.0,
    }
    return record(expected, computed)


def _points_met(counts: tuple[int, ...]) -> float:
    """Traverses at 20 mm that all end where the longest does, from 0,06 m."""
    longest = max(counts)
    traverses = []
    for count_, u in zip(counts, _DIRECTIONS * 2, strict=False):
        d = 0.06 + 0.02 * np.arange(longest - count_, longest)
        traverses.append(
            emission.MicrophoneTraverse.along(
                u, d, (90.0 - 20.0 * np.log10(d))[:, None]
            )
        )
    return float(bool(_check(traverses, (1000.0,)).points_met[0]))


def _spacing_met(step_m: float, frequency: float, *, iso26101: bool) -> float:
    d = np.arange(0.06, 1.5, step_m)
    check = _check(_exact_traverses(d, (frequency,)), (frequency,))
    flags = check.iso26101_spacing_met if iso26101 else check.spacing_met
    return float(bool(flags[0]))


@register(
    _DOMAIN,
    "ISO 3745:2012/Amd.1:2017 A.4.3",
    "Points within the radius: five traverses of 10 pass, five of 9 (45 in all) "
    "fail, and six of 10, 10, 10, 10, 10 and 9 fail; four of 13, 13, 12 and 12 "
    "(50 in all) pass and four of 13, 12, 12 and 12 (49 in all) fail; the "
    "spacing at 500 Hz, 100 mm passes and 101 mm fails, and at 125 Hz a tenth "
    "of a wavelength, 274,4 mm, passes and 274,5 mm fails",
)
def _chk_a43_points_and_spacing() -> Outcome:
    expected = {
        "5 x 10": 1.0,
        "5 x 9": 0.0,
        "5 x 10 + 9": 0.0,
        "13, 13, 12, 12": 1.0,
        "13, 12, 12, 12": 0.0,
        "100 mm at 500 Hz": 1.0,
        "101 mm at 500 Hz": 0.0,
        "274,4 mm at 125 Hz": 1.0,
        "274,5 mm at 125 Hz": 0.0,
    }
    computed = {
        "5 x 10": _points_met((10,) * 5),
        "5 x 9": _points_met((9,) * 5),
        "5 x 10 + 9": _points_met((10, 10, 10, 10, 10, 9)),
        "13, 13, 12, 12": _points_met((13, 13, 12, 12)),
        "13, 12, 12, 12": _points_met((13, 12, 12, 12)),
        "100 mm at 500 Hz": _spacing_met(0.100, 500.0, iso26101=False),
        "101 mm at 500 Hz": _spacing_met(0.101, 500.0, iso26101=False),
        "274,4 mm at 125 Hz": _spacing_met(0.2744, 125.0, iso26101=False),
        "274,5 mm at 125 Hz": _spacing_met(0.2745, 125.0, iso26101=False),
    }
    return record(expected, computed)


@register(
    _DOMAIN,
    "ISO 26101:2017 A.4.3",
    "Spatial resolution: at 2 kHz, 25 mm passes and 26 mm fails; at 500 Hz, a "
    "tenth of a wavelength, 68,6 mm, passes and 68,7 mm fails",
)
def _chk_26101_resolution() -> Outcome:
    expected = {
        "25 mm at 2 kHz": 1.0,
        "26 mm at 2 kHz": 0.0,
        "68,6 mm at 500 Hz": 1.0,
        "68,7 mm at 500 Hz": 0.0,
    }
    computed = {
        "25 mm at 2 kHz": _spacing_met(0.025, 2000.0, iso26101=True),
        "26 mm at 2 kHz": _spacing_met(0.026, 2000.0, iso26101=True),
        "68,6 mm at 500 Hz": _spacing_met(0.0686, 500.0, iso26101=True),
        "68,7 mm at 500 Hz": _spacing_met(0.0687, 500.0, iso26101=True),
    }
    return record(expected, computed)


@register(
    _DOMAIN,
    "ISO 26101:2017 5.1.4.3",
    "Traverse length at 100 Hz, a quarter wavelength of 0,857\u202f5 m: a start at "
    "0,857\u202f5 m passes and 0,857\u202f6 m fails; a run of 0,857\u202f5 m "
    "passes and 0,857\u202f4 m fails",
)
def _chk_26101_length() -> Outcome:
    freqs = (100.0,)

    def length(start: float, run: float) -> float:
        d = start + np.linspace(0.0, run, 40)
        return float(bool(_check(_exact_traverses(d, freqs), freqs).length_met[0]))

    expected = {"start 0,857\u202f5 m": 1.0, "start 0,857\u202f6 m": 0.0,
                "run 0,857\u202f5 m": 1.0, "run 0,857\u202f4 m": 0.0}  # fmt: skip
    computed = {
        "start 0,857\u202f5 m": length(0.8575, 1.0),
        "start 0,857\u202f6 m": length(0.8576, 1.0),
        "run 0,857\u202f5 m": length(0.30, 0.8575),
        "run 0,857\u202f4 m": length(0.30, 0.8574),
    }
    return record(expected, computed)


@register(
    _DOMAIN,
    "ISO 26101:2017 5.1.2.2 c)",
    "Levels 6,0 dB above the background at every point pass, 5,9 dB fail",
)
def _chk_26101_background() -> Outcome:
    freqs = (1000.0,)

    def background(margin: float) -> float:
        check = _check(_exact_traverses(_TRAVERSE, freqs, margin_db=margin), freqs)
        return float(bool(check.background_met is not None and check.background_met[0]))

    return record(
        {"6,0 dB": 1.0, "5,9 dB": 0.0},
        {"6,0 dB": background(6.0), "5,9 dB": background(5.9)},
    )


def _qualifies_to_the_end(frequency: float, room: str, rise_db: float) -> float:
    """A traverse whose last point lies ``rise_db`` above the inverse square law.

    The spread of L_pi + 20 lg(r_i/r0) is ``rise_db``, so the fitted b leaves a
    deviation of half of it either way: on the Table A.1 limit when
    ``rise_db`` is twice it.
    """
    d = np.arange(0.30, 1.5001, 0.02)
    levels = 90.0 - 20.0 * np.log10(d)
    levels[-1] += rise_db
    fit = emission.inverse_square_law_deviations(
        [emission.MicrophoneTraverse.along((1, 0, 0), d, levels)],
        frequencies_hz=[frequency],
        room=room,  # type: ignore[arg-type]
    )
    return float(bool(fit.traverse_radius_m[0, 0] > d[-2]))


@register(
    _DOMAIN,
    "ISO 26101:2017 Table A.1 / ISO 3745:2012/Amd.1:2017 Table A.1",
    "At the edge of every cell: a traverse whose deviations reach the limit "
    "either way qualifies to its last point, and 0,005 dB past it ends one "
    "point short; anechoic and hemi-anechoic, at 500 Hz, 1\u202f000 Hz and "
    "8\u202f000 Hz",
)
def _chk_table_a1_edges() -> Outcome:
    expected: dict[str, float] = {}
    computed: dict[str, float] = {}
    for room, limits in (("anechoic", (1.5, 1.0, 1.5)),
                         ("hemi-anechoic", (2.5, 2.0, 3.0))):  # fmt: skip
        for frequency, limit in zip((500.0, 1000.0, 8000.0), limits, strict=True):
            name = f"{room} {frequency:g} Hz"
            expected[f"{name}, \u00b1{limit:.1f} dB".replace(".", ",")] = 1.0
            expected[f"{name}, past it"] = 0.0
            computed[f"{name}, \u00b1{limit:.1f} dB".replace(".", ",")] = (
                _qualifies_to_the_end(frequency, room, 2.0 * limit)
            )
            computed[f"{name}, past it"] = _qualifies_to_the_end(
                frequency, room, 2.0 * limit + 0.01
            )
    return record(expected, computed)


def _uniform_within(room: str, frequency: float, deviation_db: float) -> float:
    """B.3.2 positions all at 80 dB but two, ``deviation_db`` above and below."""
    count_ = 32 if room == "hemi-anechoic" else 64
    levels = np.full(count_, 80.0)
    levels[0] += deviation_db
    levels[1] -= deviation_db
    result = emission.verify_source_directionality(
        levels,
        frequencies_hz=[frequency],
        room=room,  # type: ignore[arg-type]
    )
    return float(result.passes)


@register(
    _DOMAIN,
    "ISO 26101:2017 Table B.1",
    "At the edge of every cell: a test source whose extreme positions lie on "
    "the allowable deviation either way is uniform enough, and 0,01 dB past it "
    "is not; anechoic and hemi-anechoic, at 630, 800, 6\u202f300 and "
    "12\u202f500 Hz",
)
def _chk_table_b1_edges() -> Outcome:
    expected: dict[str, float] = {}
    computed: dict[str, float] = {}
    for room, limits in (("anechoic", (1.5, 2.0, 2.5, 5.0)),
                         ("hemi-anechoic", (2.0, 2.5, 3.0, 5.0))):  # fmt: skip
        for frequency, limit in zip(
            (630.0, 800.0, 6300.0, 12500.0), limits, strict=True
        ):
            name = f"{room} {frequency:g} Hz"
            on = f"{name}, \u00b1{limit:.1f} dB".replace(".", ",")
            expected[on] = 1.0
            expected[f"{name}, past it"] = 0.0
            computed[on] = _uniform_within(room, frequency, limit)
            computed[f"{name}, past it"] = _uniform_within(
                room, frequency, limit + 0.01
            )
    return record(expected, computed)


# --- ISO 6926: the printed limits and the calibration in use ------------------


@register(
    _DOMAIN,
    "ISO 6926:2016 Table B.1",
    "Pressure and intensity sound power levels at the edges of the tolerance: "
    "4,0 dB apart at 50 Hz and 1,0 dB at 315 Hz agree, 4,1 dB and 1,1 dB do not",
)
def _chk_6926_table_b1() -> Outcome:
    freqs = (50.0, 63.0, 80.0, *_THIRDS)
    levels = np.full((20, len(freqs)), 80.0)
    pressure = emission.reference_source_calibration(
        levels, frequencies_hz=freqs, arrangement="fixed"
    ).sound_power_level_db

    def agrees(band: float, difference: float) -> float:
        intensity = np.where(np.asarray(freqs) <= 315.0, pressure, np.nan)
        intensity[freqs.index(band)] += difference
        calibration = emission.reference_source_calibration(
            levels,
            frequencies_hz=freqs,
            arrangement="fixed",
            intensity_sound_power_level_db=intensity,
        )
        return float(bool(calibration.intensity_agreement))

    expected = {"50 Hz, 4,0 dB": 1.0, "50 Hz, 4,1 dB": 0.0, "315 Hz, 1,0 dB": 1.0,
                "315 Hz, 1,1 dB": 0.0}  # fmt: skip
    computed = {
        "50 Hz, 4,0 dB": agrees(50.0, 4.0),
        "50 Hz, 4,1 dB": agrees(50.0, 4.1),
        "315 Hz, 1,0 dB": agrees(315.0, 1.0),
        "315 Hz, 1,1 dB": agrees(315.0, 1.1),
    }
    return record(expected, computed)


@register(
    _DOMAIN,
    "ISO 6926:2016 5.2 / ISO 6926:2016 5.5",
    "A change of 0,30 dB over the declared supply range passes and 0,31 dB "
    "fails; a highest directivity index of 6,0 dB passes and 6,1 dB fails",
)
def _chk_6926_supply_and_directivity() -> Outcome:
    lw = np.full(len(_THIRDS), 90.0)

    def verdict(
        supply: float, directivity: float
    ) -> emission.ReferenceSoundSourceVerdict:
        return emission.verify_reference_sound_source(
            lw,
            frequencies_hz=_THIRDS,
            supply_variation_db=supply,
            directivity_index_db=np.full(len(_THIRDS), directivity),
        )

    expected = {"0,30 dB": 1.0, "0,31 dB": 0.0, "6,0 dB": 1.0, "6,1 dB": 0.0}
    computed = {
        "0,30 dB": float(bool(verdict(0.30, 0.0).supply_met)),
        "0,31 dB": float(bool(verdict(0.31, 0.0).supply_met)),
        "6,0 dB": float(bool(verdict(0.0, 6.0).directivity_met)),
        "6,1 dB": float(bool(verdict(0.0, 6.1).directivity_met)),
    }
    return record(expected, computed)


@register(
    _DOMAIN,
    "ISO 6926:2016 Formula (2)",
    "L_W of a uniform 80 dB over the 2 m hemisphere at 30 degC and 95 kPa, "
    "C1 and the C2 of a source of unknown radiation evaluated by hand, 1 kHz, "
    "dB (closed form)",
)
def _chk_6926_formula_2_meteorology() -> Outcome:
    calibration = emission.reference_source_calibration(
        np.full((20, len(_THIRDS)), 80.0),
        frequencies_hz=_THIRDS,
        arrangement="fixed",
        conditions=emission.CalibrationConditions(
            temperature_c=30.0, static_pressure_kpa=95.0
        ),
    )
    pressure = -10.0 * math.log10(95.0 / 101.325)
    expected = (
        80.0
        + 10.0 * math.log10(2.0 * math.pi * 4.0)
        + pressure
        + 5.0 * math.log10(303.15 / 314.0)
        + pressure
        + 7.5 * math.log10(303.15 / 296.0)
    )
    got = float(calibration.sound_power_level_db[_THIRDS.index(1000.0)])
    return numeric(expected, got, 1e-9, unit="dB", places=4)


@register(
    _DOMAIN,
    "ISO 6926:2016 8.4 / ISO 3741:2010 Eq. 21",
    "A calibration read by an ISO 3741 comparison at 20 degC and 90 kPa: L_W "
    "less its own C2 at the test, 0,483 dB for a source of unknown radiation, "
    "plus 4 dB and ISO 3741's C2 of 0,452 dB, 1 kHz, dB (closed form)",
)
def _chk_6926_calibration_at_the_test() -> Outcome:
    calibration = emission.reference_source_calibration(
        np.full((20, len(_THIRDS)), 80.0), frequencies_hz=_THIRDS, arrangement="fixed"
    )
    lp = np.full(len(_THIRDS), 70.0)
    result = emission.sound_power_comparison(
        lp + 4.0,
        lp,
        calibration,
        frequencies=np.asarray(_THIRDS),
        temperature_c=20.0,
        static_pressure_kpa=90.0,
    )
    pressure = -10.0 * math.log10(90.0 / 101.325)
    ratio = math.log10(293.15 / 296.0)
    at = _THIRDS.index(1000.0)
    expected = (
        float(calibration.sound_power_level_db[at])
        - (pressure + 7.5 * ratio)
        + 4.0
        + (pressure + 15.0 * ratio)
    )
    return numeric(expected, float(result.sound_power_level[at]), 1e-9, unit="dB",
                   places=4)  # fmt: skip
