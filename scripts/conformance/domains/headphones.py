#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Headphones and the simulated programme signal: IEC 60268-7:2010 and IEC 60268-1:1985.

The programme signal of IEC 60268-1 Clause 7 is a relative spectrum, Table II,
which a filter of pink noise (Figure 2) realises within tolerance; the Note
under the clause states the power of the whole signal over one band. The rows
pin the Note against the power sum of the table, the Figure 2 ladder inside
every tolerance of the table, and the generator that puts each band on its
printed level, integrated numerically over each band independently of the
closed form its nodes are fitted with. Neither amendment of 1988 touches the
clause. Clause 3 sets the standard reference frequency at 1 000 Hz, which
IEC 60268-7 names for its comparison responses without defining it.

IEC 60268-7 prints no worked example. Its rows rest on the numbers the part
does print: the three impedance codes of Clause 4, the 80 % of 8.2.1 b), the
94 dB and 500 Hz of 7.2 b), the 1 mW of 8.5.2, the 120 ohm and 5 V of IEC
61938 that 7.1 and 8.3.1 cite, the peak-to-RMS window of 8.3.2.2 b) from both
sides, the 1 dB of 8.3.6.2 b), the eight and 16 persons of 8.6.3 and 8.6.5.3,
the 2,5 dB and 3 dB of 8.6.5.2, NOTE 1 of 8.7.3.3 and the products it names,
the 80 Hz of 8.7.4.1 and the limits of Annex B; and on closed forms the
clauses state, Formula (1), the power summation of the NOTE under Figure 3
and the two settings of the working e.m.f. in 8.5.2 b) and 8.5.3 c),
synthesised to a known result. Formula (3) prints :math:`U_{470}` for the
460 Hz product its own item b) names; the row pins 460 Hz and
``docs/ERRATA.md`` records it, with the disagreement of 8.5.2 b) and 8.5.3 c)
and the references of 8.6.5.3.

Oracle: IEC 60268-1:1985, bilingual (PDF page = English folio + 2): Clause 3
(folio 9), Clause 7 (13), Table II (21), Figures 1 and 2 (22). IEC 60268-7:2010 Edition 3.0
(PDF page = folio + 2): Clause 4 (9, 10), 7.1 (14), 7.2 (15), 7.4 and
Figure 3 (15, 16), 8.2 (17, 18), 8.3.1 to 8.3.3 (18, 19), 8.3.4 and 8.3.5 (20,
21), 8.3.6 (21), 8.4 and 8.5 (21 to 23), 8.6.3 (24), 8.6.5 (25 to 27), 8.7.3
(28), 8.7.4 (28, 29), Annex B (42). IEC 61672-1:2013 Table 3 for the
A-weighting the NOTE under Figure 3 names.
"""

from __future__ import annotations

import math

import numpy as np
import reference_data as ref

from phonometry import electroacoustics as ea
from phonometry.electroacoustics import programme_signal as ps
from phonometry.filters import octave_filter

from ..registry import Outcome, count, mask, numeric, record, register

_HEADPHONES = "Headphones and the programme signal (IEC 60268-7:2010, IEC 60268-1:1985)"

_60268_1 = "IEC 60268-1:1985"
_60268_7 = "IEC 60268-7:2010"

_FS = 48000

#: One-third-octave centres from 100 Hz to 10 kHz, with the 500 Hz band.
_BANDS = np.array(
    [100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0]
    + [1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0]
    + [10000.0]
)


def _flag(passes: bool) -> float:  # noqa: FBT001
    """A verdict as the 1 or 0 a record compares."""
    return 1.0 if passes else 0.0


def _table_ii() -> tuple[np.ndarray, np.ndarray]:
    """Table II as printed: nominal frequencies and relative levels."""
    rows = np.array(ref.IEC60268_1_TABLE_II)
    return rows[:, 0], rows[:, 1]


# ---------------------------------------------------------------------------
# IEC 60268-1:1985 Clause 7: the simulated programme signal
# ---------------------------------------------------------------------------


@register(
    _HEADPHONES,
    f"{_60268_1} Table II",
    "The 31 bands of the simulated programme signal, as published",
)
def _chk_table_ii() -> Outcome:
    frequencies, levels = _table_ii()
    published = ea.SIMULATED_PROGRAMME_SPECTRUM
    matching = sum(
        1
        for f, level, tol in ref.IEC60268_1_TABLE_II
        if published[f].relative_level_db == level
        and published[f].tolerance_plus_db == tol
        and published[f].tolerance_minus_db == tol
    )
    return count(matching, frequencies.size, subject="bands of Table II")


@register(
    _HEADPHONES,
    f"{_60268_1} Clause 7 Note",
    "Power over the full range above the 0 dB of one band",
)
def _chk_full_range() -> Outcome:
    levels = np.array(
        [band.relative_level_db for band in ea.SIMULATED_PROGRAMME_SPECTRUM.values()]
    )
    excess = 10.0 * math.log10(float(np.sum(10.0 ** (levels / 10.0))))
    return numeric(
        ref.IEC60268_1_FULL_RANGE_EXCESS_DB,
        excess,
        0.1,
        unit="dB",
        places=2,
        expected_label="approximately 12.5 dB",
    )


def _figure_2_band_levels() -> np.ndarray:
    """Pink noise through Figure 2 in ideal one-third-octave bands, in dB."""
    frequencies, _ = _table_ii()
    exact = 1000.0 * 10.0 ** (np.round(10.0 * np.log10(frequencies / 1000.0)) / 10.0)
    edge = 10.0 ** (1.0 / 20.0)
    levels = []
    for centre in exact:
        f = np.geomspace(centre / edge, centre * edge, 4001)
        power = np.abs(ea.programme_signal_filter(f)) ** 2 / f
        levels.append(10.0 * np.log10(np.trapezoid(power, f) / math.log(edge**2)))
    return np.asarray(levels)


@register(
    _HEADPHONES,
    f"{_60268_1} Figure 2",
    "Pink noise through the filter of Figure 2 inside every tolerance of Table II",
)
def _chk_figure_2() -> Outcome:
    frequencies, _ = _table_ii()
    check = ea.check_programme_signal(frequencies, _figure_2_band_levels())
    bands = " Hz and ".join(f"{f:g}" for f in check.binding_bands_hz)
    return mask(
        expected="one level puts all 31 bands inside Table II",
        computed=f"smallest margin {check.margin_db:.3f} dB, at {bands} Hz",
        deviation=check.margin_db,
        lower=0.0,
        unit="dB",
    )


def _table_band_levels_by_quadrature() -> np.ndarray:
    r"""The generator's ``"table"`` density integrated numerically over each band.

    The trapezoidal rule over 20 001 points of :math:`\lg f` across each ideal
    base-ten band, divided by its width: a sum that never calls the closed form
    the nodes are fitted with, so an error in that closed form shows here.
    """
    levels = []
    for n in range(-17, 14):
        centre = 3.0 + n / 10.0
        u = np.linspace(centre - 0.05, centre + 0.05, 20001)
        power = 10.0 ** (ps._table_density_db(10.0**u) / 10.0)
        levels.append(10.0 * np.log10(np.trapezoid(power, u) / 0.1))
    return np.asarray(levels)


@register(
    _HEADPHONES,
    f"{_60268_1} Table II",
    "Band levels of the generator's Table II density, integrated numerically",
)
def _chk_generator_nodes() -> Outcome:
    _, levels = _table_ii()
    bands = _table_band_levels_by_quadrature()
    worst = float(np.max(np.abs(bands - levels)))
    return numeric(
        0.0,
        worst,
        1e-6,
        unit="dB",
        places=6,
        expected_label="0 dB from every printed level",
        computed_label=f"largest difference {worst:.1e} dB",
    )


@register(
    _HEADPHONES,
    f"{_60268_1} Clause 7",
    "A 60 s record of the generator judged in one-third-octave bands",
)
def _chk_generator_record() -> Outcome:
    x = ea.simulated_programme_signal(_FS, 60.0, seed=1)
    bands = octave_filter(x, _FS, fraction=3, limits=[19.95, 19952.6])
    check = ea.check_programme_signal(bands.frequencies, np.asarray(bands.levels))
    return mask(
        expected="all 31 bands inside Table II",
        computed=f"smallest margin {check.margin_db:.3f} dB",
        deviation=check.margin_db,
        lower=0.0,
        unit="dB",
    )


# ---------------------------------------------------------------------------
# IEC 60268-7:2010 Clause 4: the code
# ---------------------------------------------------------------------------


@register(
    _HEADPHONES,
    f"{_60268_7} Clause 4",
    "Impedance in mantissa and exponent form: 8, 32 and 600 ohm both ways",
)
def _chk_impedance_codes() -> Outcome:
    printed = ref.IEC60268_7_IMPEDANCE_CODES
    matching = sum(
        1
        for impedance, code in printed.items()
        if ea.impedance_code(impedance) == code
        and ea.parse_classification_code(f"60268-7-IEC-DCSC-{code}-2").impedance_ohm
        == impedance
    )
    return count(
        matching,
        len(printed),
        subject="printed codes",
        expected_label='3/3 printed codes ("08R0", "32R0", "06R2")',
    )


# ---------------------------------------------------------------------------
# 8.2: impedance
# ---------------------------------------------------------------------------


@register(
    _HEADPHONES,
    f"{_60268_7} 8.2.1 b)",
    "Lowest modulus in the rated range at 80 % and at 79,9 % of the rated value",
)
def _chk_rated_impedance() -> Outcome:
    f = np.array([20.0, 100.0, 1000.0, 20000.0])
    rated = 32.0
    verdicts = {}
    for share in (ref.IEC60268_7_RATED_IMPEDANCE_FRACTION, 0.799):
        z = np.array([40.0, rated * share, 33.0, 36.0])
        verdict = ea.verify_rated_impedance(
            f, z, rated_impedance_ohm=rated, rated_frequency_range_hz=(20.0, 20000.0)
        )
        verdicts[f"{100 * share:g} %"] = _flag(verdict.passes)
    return record(
        {"80 %": 1.0, "79.9 %": 0.0}, verdicts, label="80 % passes, 79,9 % fails"
    )


# ---------------------------------------------------------------------------
# 8.3 to 8.5: voltages, powers, levels
# ---------------------------------------------------------------------------


@register(
    _HEADPHONES,
    f"{_60268_7} 8.3.3",
    "Characteristic voltage from 100 dB at 0,1 V: the e.m.f. for 94 dB",
)
def _chk_characteristic_voltage() -> Outcome:
    voltage = ea.characteristic_voltage(0.1, 100.0)
    expected = 0.1 * 10.0 ** ((ref.IEC60268_7_STANDARD_LEVEL_DB - 100.0) / 20.0)
    return numeric(expected, voltage, 1e-12, unit="V", places=6)


@register(
    _HEADPHONES,
    f"{_60268_7} 8.5.2 b) with 7.1 NOTE",
    "Source e.m.f. for 1 mW in 32 ohm through the 120 ohm of IEC 61938",
)
def _chk_working_emf() -> Outcome:
    emf = ea.headphone_source_emf(
        ref.IEC60268_7_WORKING_POWER_W,
        rated_impedance_ohm=32.0,
        rated_source_impedance_ohm=ref.IEC60268_7_IEC61938_SOURCE_IMPEDANCE_OHM,
    )
    expected = math.sqrt(1e-3 * 32.0) * (32.0 + 120.0) / 32.0
    return numeric(expected, emf, 1e-12, unit="V", places=6)


@register(
    _HEADPHONES,
    f"{_60268_7} 8.5.2 b) and 8.5.3 c)",
    "Working level of a 32 ohm headphone that is 40 ohm at 500 Hz, on 120 ohm",
)
def _chk_working_level_method() -> Outcome:
    impedances = {
        "rated_impedance_ohm": 32.0,
        "rated_source_impedance_ohm": ref.IEC60268_7_IEC61938_SOURCE_IMPEDANCE_OHM,
    }
    by_definition = ea.working_sound_pressure_level(100.0, 0.5, **impedances)
    by_method = ea.working_sound_pressure_level(
        100.0, 0.5, **impedances, headphone_impedance_ohm=40.0
    )
    # 8.5.2 b): E = sqrt(PR)(R + Rs)/R; 8.5.3 c): E = sqrt(PR)|Z + Rs|/|Z|.
    expected = 20.0 * math.log10((152.0 / 32.0) / (160.0 / 40.0))
    return numeric(
        expected,
        by_definition - by_method,
        1e-12,
        unit="dB",
        places=4,
        expected_label="20 lg(4.75/4) = 1.4927 dB below the definition",
    )


@register(
    _HEADPHONES,
    f"{_60268_7} 8.4 with 8.3.1 NOTE 2",
    "Power of the 5 V rated source e.m.f. in 32 ohm through 120 ohm",
)
def _chk_rated_power() -> Outcome:
    power = ea.headphone_input_power(
        ref.IEC60268_7_IEC61938_SOURCE_EMF_V,
        rated_impedance_ohm=32.0,
        rated_source_impedance_ohm=ref.IEC60268_7_IEC61938_SOURCE_IMPEDANCE_OHM,
    )
    expected = 5.0**2 * 32.0 / (32.0 + 120.0) ** 2
    return numeric(expected, power, 1e-12, unit="W", places=6)


@register(
    _HEADPHONES,
    f"{_60268_7} Figure 3 NOTE with IEC 61672-1:2013 Table 3",
    "A-weighting coefficient of each band of Table II in the power summation",
)
def _chk_a_weighting_coefficients() -> Outcome:
    table3 = {float(row[0]): float(row[1]) for row in ref.IEC61672_TABLE3}
    frequencies, _ = _table_ii()
    matching = sum(
        1
        for f in frequencies
        if round(ea.programme_signal_level([f], [0.0], a_weighted=True), 1) == table3[f]
    )
    return count(matching, frequencies.size, subject="bands matching Table 3")


@register(
    _HEADPHONES,
    f"{_60268_7} 8.3.4, Figure 3 NOTE",
    "Programme characteristic voltage of a flat headphone, 21 bands at 80 dB from 0,1 V",
)
def _chk_programme_voltage() -> Outcome:
    result = ea.programme_characteristic_voltage(
        0.1, _BANDS, np.full(_BANDS.size, 80.0)
    )
    total = 80.0 + 10.0 * math.log10(_BANDS.size)
    expected = 0.1 * 10.0 ** ((94.0 - total) / 20.0)
    return numeric(expected, result.characteristic_voltage_v, 1e-12, unit="V", places=6)


@register(
    _HEADPHONES,
    f"{_60268_7} 8.3.5 g)",
    "Corrected characteristic voltage, the mean e.m.f. of three fittings",
)
def _chk_fittings_mean() -> Outcome:
    offsets = np.array([0.0, 1.0, -1.0])
    levels = 80.0 + offsets[:, None] + np.zeros(_BANDS.size)
    result = ea.programme_characteristic_voltage(0.1, _BANDS, levels)
    total = 80.0 + 10.0 * math.log10(_BANDS.size) + offsets
    expected = float(np.mean(0.1 * 10.0 ** ((94.0 - total) / 20.0)))
    return numeric(expected, result.characteristic_voltage_v, 1e-12, unit="V", places=6)


@register(
    _HEADPHONES,
    f"{_60268_7} 8.3.2.2 b)",
    "Clipped programme signal at the two ends of the 1,8 to 2,2 window",
)
def _chk_limiting_signal() -> Outcome:
    verdicts = {}
    lower, upper = ref.IEC60268_7_LIMITING_PEAK_TO_RMS
    for ratio in (lower - 0.1, lower, upper, upper + 0.1):
        x = ea.simulated_programme_signal(_FS, 20.0, peak_to_rms=ratio, seed=3)
        verdicts[f"{ratio:g}"] = _flag(ea.check_limiting_test_signal(x, _FS).passes)
    x = ea.simulated_programme_signal(_FS, 20.0, seed=3)
    verdicts["unclipped"] = _flag(ea.check_limiting_test_signal(x, _FS).passes)
    return record(
        {"1.7": 0.0, "1.8": 1.0, "2.2": 1.0, "2.3": 0.0, "unclipped": 0.0},
        verdicts,
        label="1,8 and 2,2 pass with the Table II spectrum; 1,7, 2,3 and unclipped fail",
    )


@register(
    _HEADPHONES,
    f"{_60268_7} 8.3.6.2 b)",
    "Protection voltage where the sensitivity has changed 1 dB",
)
def _chk_protection_voltage() -> Outcome:
    emf = np.array([0.1, 0.2, 0.4, 0.8, 1.6])
    shortfall = np.array([0.0, 0.0, 0.0, 0.5, 2.0])
    levels = 94.0 + 20.0 * np.log10(emf / 0.1) - shortfall
    result = ea.protection_voltage(emf, levels)
    # The 1 dB falls a third of the way from 0,5 dB at 0,8 V to 2 dB at 1,6 V.
    expected = 0.8 * 2.0 ** (1.0 / 3.0)
    computed = result.protection_voltage_v or float("nan")
    return numeric(expected, computed, 1e-12, unit="V", places=6)


# ---------------------------------------------------------------------------
# 8.6: frequency responses with test persons
# ---------------------------------------------------------------------------


@register(
    _HEADPHONES,
    f"{_60268_7} 8.6.3.2 d), 8.6.3.3",
    "Panel sizes: eight persons for a measurement, 16 for a reference",
)
def _chk_panel_sizes() -> Outcome:
    flags = {}
    for persons in (7, 8, 15, 16):
        emf = np.full((persons, _BANDS.size), 0.05)
        result = ea.field_comparison_response(_BANDS, 70.0, emf, field="free")
        flags[f"{persons} measure"] = _flag(result.meets_panel_size)
        flags[f"{persons} reference"] = _flag(result.qualifies_as_reference)
    expected = {
        "7 measure": 0.0,
        "7 reference": 0.0,
        "8 measure": 1.0,
        "8 reference": 0.0,
        "15 measure": 1.0,
        "15 reference": 0.0,
        "16 measure": 1.0,
        "16 reference": 1.0,
    }
    return record(expected, flags, label="8 persons measure, 16 qualify a reference")


@register(
    _HEADPHONES,
    f"{_60268_7} 8.6.3.1 with {_60268_1} Clause 3",
    "Comparison response referred to the standard reference frequency of 1 000 Hz",
)
def _chk_standard_reference_frequency() -> Outcome:
    emf = 0.05 * 10.0 ** (-np.linspace(0.0, 4.0, _BANDS.size)[None, :] / 20.0)
    result = ea.field_comparison_response(
        _BANDS, 70.0, np.repeat(emf, 8, 0), field="free"
    )
    band = list(_BANDS).index(ref.IEC60268_1_STANDARD_REFERENCE_FREQUENCY_HZ)
    computed = {
        "reference": result.reference_frequency_hz,
        "response there": float(result.mean_db[band]),
    }
    return record(
        {
            "reference": ref.IEC60268_1_STANDARD_REFERENCE_FREQUENCY_HZ,
            "response there": 0.0,
        },
        computed,
        label="1 000 Hz by default, and 0 dB on that band",
    )


@register(
    _HEADPHONES,
    f"{_60268_7} 8.6.5.3 with 8.6.5.2 h)",
    "Ear canal panel: eight persons for a measurement, 16 to calibrate a reference",
)
def _chk_ear_canal_panel() -> Outcome:
    flags = {}
    for persons in (7, 8, 15, 16):
        levels = np.full((persons, 2, _BANDS.size), 70.0)
        result = ea.ear_canal_frequency_response(_BANDS, levels, levels)
        flags[f"{persons} measure"] = _flag(result.meets_panel_size)
        flags[f"{persons} reference"] = _flag(result.qualifies_as_reference)
    expected = {
        "7 measure": 0.0,
        "7 reference": 0.0,
        "8 measure": 1.0,
        "8 reference": 0.0,
        "15 measure": 1.0,
        "15 reference": 0.0,
        "16 measure": 1.0,
        "16 reference": 1.0,
    }
    return record(expected, flags, label="8 persons measure, 16 calibrate a reference")


@register(
    _HEADPHONES,
    f"{_60268_7} 8.6.5.2 g), Formula (1)",
    "Ear canal response of a headphone 3 dB up at 2 kHz and level elsewhere",
)
def _chk_formula_1() -> Outcome:
    field = np.full((1, 2, _BANDS.size), 70.0)
    earphone = np.full((1, 2, _BANDS.size), 74.0)
    earphone[0, :, list(_BANDS).index(2000.0)] += 3.0
    result = ea.ear_canal_frequency_response(_BANDS, earphone, field)
    return numeric(
        3.0, float(result.mean_db[list(_BANDS).index(2000.0)]), 1e-12, unit="dB"
    )


@register(
    _HEADPHONES,
    f"{_60268_7} 8.6.5.2 c) and f)",
    "Fittings 2,5 dB apart and a 500 Hz band 3 dB off, inclusive",
)
def _chk_ear_canal_limits() -> Outcome:
    # Four persons: the first two refit 2,5 dB and 2,6 dB apart in one band,
    # the last two set their 500 Hz band 3,0 dB and 3,1 dB off the field's.
    field = np.full((4, 2, _BANDS.size), 70.0)
    earphone = np.full((4, 2, _BANDS.size), 70.0)
    reference = list(_BANDS).index(500.0)
    earphone[0, 1, 3] += ref.IEC60268_7_MAX_FITTING_DIFFERENCE_DB
    earphone[1, 1, 3] += 2.6
    earphone[2, :, reference] += ref.IEC60268_7_LEVEL_MATCH_DB
    earphone[3, :, reference] += 3.1
    result = ea.ear_canal_frequency_response(_BANDS, earphone, field)
    computed = {
        "2.5 dB apart": _flag(bool(result.fittings_consistent[0])),
        "2.6 dB apart": _flag(bool(result.fittings_consistent[1])),
        "3.0 dB off": _flag(bool(result.levels_matched[2])),
        "3.1 dB off": _flag(bool(result.levels_matched[3])),
    }
    expected = {
        "2.5 dB apart": 1.0,
        "2.6 dB apart": 0.0,
        "3.0 dB off": 1.0,
        "3.1 dB off": 0.0,
    }
    return record(
        expected, computed, label="2,5 dB and 3 dB are inside, 2,6 dB and 3,1 dB not"
    )


# ---------------------------------------------------------------------------
# 8.7: the distortion test signals
# ---------------------------------------------------------------------------


def _tone_level_db(x: np.ndarray, frequency: float) -> float:
    """RMS level of the tone at ``frequency`` re 1 V, from a whole-period record."""
    spectrum = np.fft.rfft(x) / x.size
    k = round(frequency * x.size / _FS)
    return 20.0 * math.log10(2.0 * abs(spectrum[k]) / math.sqrt(2.0))


def _modulation_row(frequency: float) -> Outcome:
    x = ea.headphone_modulation_signal(_FS, 1.0, rated_source_emf_v=1.0)
    printed = ref.IEC60268_7_MODULATION_LEVELS_DB[frequency]
    return numeric(printed, _tone_level_db(x, frequency), 0.05, unit="dB", places=2)


@register(
    _HEADPHONES,
    f"{_60268_7} 8.7.3.3 NOTE 1",
    "Level of the 70 Hz tone re the rated input voltage",
)
def _chk_modulation_70() -> Outcome:
    return _modulation_row(70.0)


@register(
    _HEADPHONES,
    f"{_60268_7} 8.7.3.3 NOTE 1",
    "Level of the 600 Hz tone re the rated input voltage",
)
def _chk_modulation_600() -> Outcome:
    return _modulation_row(600.0)


@register(
    _HEADPHONES,
    f"{_60268_7} 8.7.3.3 b) and Formula (3)",
    "Modulation products read at 530, 670, 460 and 740 Hz",
)
def _chk_modulation_products() -> Outcome:
    x = ea.headphone_modulation_signal(_FS, 1.0, rated_source_emf_v=1.0)
    low, high = ref.IEC60268_7_MODULATION_HZ
    result = ea.modulation_distortion(x, _FS, f_low=low, f_high=high)
    products = sorted(float(f) for f in np.asarray(result.sideband_frequencies))
    names = ("third lower", "second lower", "second upper", "third upper")
    expected = sorted(ref.IEC60268_7_SECOND_ORDER_HZ + ref.IEC60268_7_THIRD_ORDER_HZ)
    return record(
        dict(zip(names, expected, strict=True)),
        dict(zip(names, products, strict=True)),
        unit="Hz",
        label="460, 530, 670 and 740 Hz (item b; Formula (3) prints 470 Hz, see ERRATA)",
    )


@register(
    _HEADPHONES,
    f"{_60268_7} 8.7.4.1",
    "Each tone of the difference-frequency signal at half the rated voltage",
)
def _chk_difference_frequency() -> Outcome:
    x = ea.headphone_difference_frequency_signal(
        _FS, 1.0, upper_frequency_hz=1000.0, rated_source_emf_v=1.0
    )
    lower = 1000.0 - ref.IEC60268_7_DIFFERENCE_FREQUENCY_HZ
    levels = [_tone_level_db(x, f) for f in (lower, 1000.0)]
    return numeric(
        20.0 * math.log10(0.5),
        max(levels, key=lambda level: abs(level - 20.0 * math.log10(0.5))),
        1e-9,
        unit="dB",
        places=3,
        expected_label="-6.021 dB each, 80 Hz apart",
    )


# ---------------------------------------------------------------------------
# Annex B
# ---------------------------------------------------------------------------


@register(
    _HEADPHONES,
    f"{_60268_7} Annex B a) to e)",
    "A probe microphone on each printed limit",
)
def _chk_annex_b() -> Outcome:
    limits = ref.IEC60268_7_ANNEX_B
    verdict = ea.verify_ear_canal_microphone(
        entrance_area_mm2=limits["entrance_area_mm2"],
        canal_section_area_mm2=limits["canal_area_ratio"]
        * limits["adult_canal_area_mm2"],
        volume_mm3=limits["volume_mm3"],
        pink_noise_band_levels_db=[60.0, 60.0 + limits["neighbour_difference_db"]],
        open_levels_db=[60.0],
        sealed_levels_db=[60.0 - limits["sealed_attenuation_db"]],
    )
    computed = {key: _flag(value) for key, value in verdict.requirements.items()}
    # a), d) and e) include their limit ("or less", "not more", "at least");
    # b) and c) do not ("less than").
    expected = {"a": 1.0, "b": 0.0, "c": 0.0, "d": 1.0, "e": 1.0}
    return record(
        expected, computed, label="a, d, e pass on the limit; b, c fail on it"
    )
