#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Type-testing a human-vibration meter (ISO 8041-1).

The tables that grade an instrument, pinned against the printed page: the
transition frequencies of Table 4, the tolerance bands of Table 5, the
reference conditions of Table 1 and the indication tolerance of Table 2.

Table 4 is the interesting one to pin. The standard prints each transition
frequency twice, as an exponent ``10**(k/10)`` and as a rounded decimal beside
it, and the library builds them from the exponents. These rows check the
built value against the printed decimal, so the two spellings of the same
table have to agree.

The phase column of Table 5 is graded here too. What it grades is not the
phase error but Formula (6) of it, and the design goal it is measured from is
the one Tables B.1 to B.9 print in their own phase columns: 318 cells that
had no conformance row until these.

Oracle: ISO 8041-1:2017, printed folios 9, 12, 15 and 93 (PDF pages 17, 20,
23 and 101): Table 1 (reference vibration values and frequencies), Table 2
(tolerances of indication), Table 4 (transition frequencies), Table 5
(tolerances on frequency weightings), Formula (6) and Annex H, plus the
decision rule of 13.1 and 14.1 (folios 42 and 48) and the phase columns of
Annex B (folios 56 to 72).
"""

from __future__ import annotations

import numpy as np
import reference_data as ref

import phonometry as ph

from ..registry import Outcome, count, numeric, record, register

_METER = "Human-vibration meter verification (ISO 8041-1)"

_TOLERANCE = 5e-4

#: Table 4, as the decimals printed beside the exponents the library builds
#: the frequencies from.
_TABLE_4_PRINTED = {
    "Wk": (0.2512, 0.631, 63.1, 158.5),
    "Wf": (0.05012, 0.1259, 0.3981, 1.0),
    "Wh": (3.981, 10.0, 794.3, 1995.0),
}

#: Table 1: the reference frequency in hertz, and the weighted acceleration a
#: conforming meter indicates there.
_TABLE_1_PRINTED = {
    "Wb": (15.915, 0.8126),
    "Wd": (15.915, 0.1261),
    "Wh": (79.58, 2.020),
    "Wk": (15.915, 0.7718),
    "Wf": (0.3979, 0.03888),
}


def _register_table_4() -> None:
    """One row per printed corner of Table 4."""
    for weighting, corners in _TABLE_4_PRINTED.items():
        for index, printed in enumerate(corners, start=1):

            def _check(
                weighting: str = weighting, index: int = index, printed: float = printed
            ) -> Outcome:
                built = ph.vibration.TRANSITION_FREQUENCIES_HZ[weighting][index - 1]
                return numeric(printed, built, 2e-4, unit="Hz", places=5, rel=True)

            register(
                _METER,
                "ISO 8041-1:2017 Table 4",
                f"{weighting} transition frequency ft{index}, Hz",
            )(_check)


def _register_table_1() -> None:
    """The reference frequency and the indication at it, per weighting."""
    for weighting, (frequency, indication) in _TABLE_1_PRINTED.items():

        def _check_frequency(
            weighting: str = weighting, printed: float = frequency
        ) -> Outcome:
            built = ph.vibration.REFERENCE_FREQUENCY_HZ[weighting]
            return numeric(printed, built, 1e-4, unit="Hz", places=4, rel=True)

        register(
            _METER,
            "ISO 8041-1:2017 Table 1",
            f"{weighting} reference frequency, Hz",
        )(_check_frequency)

        def _check_indication(
            weighting: str = weighting, printed: float = indication
        ) -> Outcome:
            computed = ph.vibration.reference_indication(weighting)
            return numeric(printed, computed, 1e-3, unit="m/s2", places=5, rel=True)

        register(
            _METER,
            "ISO 8041-1:2017 Table 1",
            f"{weighting} weighted indication at the reference, m/s2",
        )(_check_indication)


_register_table_4()
_register_table_1()


@register(
    _METER,
    "ISO 8041-1:2017 Table 5",
    "Upper magnitude tolerance in the central region, %",
)
def _chk_central_upper() -> Outcome:
    """The ``+12 %`` of the region between ft2 and ft3."""
    upper, _ = ph.vibration.weighting_tolerance_percent("Wk", [16.0])
    return numeric(12.0, float(upper[0]), _TOLERANCE, unit="%", places=4)


@register(
    _METER,
    "ISO 8041-1:2017 Table 5",
    "Lower magnitude tolerance in the central region, %",
)
def _chk_central_lower() -> Outcome:
    """And its ``-11 %``, which is not the mirror of the upper one."""
    _, lower = ph.vibration.weighting_tolerance_percent("Wk", [16.0])
    return numeric(-11.0, float(lower[0]), _TOLERANCE, unit="%", places=4)


@register(
    _METER,
    "ISO 8041-1:2017 Table 5",
    "Upper magnitude tolerance in the skirts, %",
)
def _chk_skirt_upper() -> Outcome:
    """The ``+26 %`` between ft1 and ft2, read just inside the corner."""
    ft1, ft2, _, _ = ph.vibration.TRANSITION_FREQUENCIES_HZ["Wk"]
    upper, _ = ph.vibration.weighting_tolerance_percent("Wk", [(ft1 + ft2) / 2.0])
    return numeric(26.0, float(upper[0]), _TOLERANCE, unit="%", places=4)


@register(
    _METER,
    "ISO 8041-1:2017 Table 5",
    "Lower magnitude tolerance in the skirts, %",
)
def _chk_skirt_lower() -> Outcome:
    """And its ``-21 %``."""
    ft1, ft2, _, _ = ph.vibration.TRANSITION_FREQUENCIES_HZ["Wk"]
    _, lower = ph.vibration.weighting_tolerance_percent("Wk", [(ft1 + ft2) / 2.0])
    return numeric(-21.0, float(lower[0]), _TOLERANCE, unit="%", places=4)


@register(
    _METER,
    "ISO 8041-1:2017 Table 5",
    "Lower magnitude tolerance in the tails, %",
)
def _chk_tail_lower() -> Outcome:
    """The ``-100 %``, which is the absence of a lower limit rather than a wide one."""
    ft1 = ph.vibration.TRANSITION_FREQUENCIES_HZ["Wk"][0]
    _, lower = ph.vibration.weighting_tolerance_percent("Wk", [ft1 / 2.0])
    return numeric(-100.0, float(lower[0]), _TOLERANCE, unit="%", places=4)


@register(
    _METER,
    "ISO 8041-1:2017 Table 5",
    "Characteristic phase deviation in the central region, degrees",
)
def _chk_central_phase() -> Outcome:
    """The ``6 degrees`` of footnote a, for a meter reporting a non-r.m.s. parameter."""
    limits = ph.vibration.phase_tolerance_degrees("Wk", [16.0])
    return numeric(6.0, float(limits[0]), _TOLERANCE, unit="deg", places=4)


@register(
    _METER,
    "ISO 8041-1:2017 Table 2",
    "Indication tolerance at the reference frequency, %",
)
def _chk_indication() -> Outcome:
    """The ``4 %`` of hand-transmitted and whole-body vibration."""
    return numeric(
        4.0,
        ph.vibration.indication_tolerance_percent("Wk"),
        _TOLERANCE,
        unit="%",
        places=4,
    )


@register(
    _METER,
    "ISO 8041-1:2017 Table 2",
    "Indication tolerance for low-frequency whole-body vibration, %",
)
def _chk_low_frequency_indication() -> Outcome:
    """And the ``5 %`` the low-frequency case is allowed instead."""
    return numeric(
        5.0,
        ph.vibration.indication_tolerance_percent("Wf"),
        _TOLERANCE,
        unit="%",
        places=4,
    )


def _deviating_measurement(
    weighting: str, frequency_hz: float, percent: float
) -> list[float]:
    """A measured factor that deviates from the design goal by ``percent``."""
    design = float(
        np.asarray(ph.vibration.weighting_factors(weighting, [frequency_hz]))[0]
    )
    return [design * (1.0 + percent / 100.0)]


@register(
    _METER,
    "ISO 8041-1:2017 13.1 and 14.1",
    "Decision rule at the upper tolerance limit, 2 verdicts",
)
def _chk_decision_rule_upper() -> Outcome:
    """The sentence 13.1 and 14.1 print word for word.

    "Compliance with a specification of this document is demonstrated when
    the result of a measurement of a deviation from a design goal, extended
    by the actual expanded uncertainty of measurement of the testing
    laboratory, does not exceed the specified tolerance limits." So a
    deviation of 11,5 % in the central region, where the limit is +12 %,
    conforms on its own and does not once a laboratory extends it by an
    expanded uncertainty of 1 %. No figure is printed for this: what is
    checked is that the verdict turns where the sentence turns it.
    """
    measured = _deviating_measurement("Wk", 16.0, 11.5)
    bare = ph.vibration.verify_weighting("Wk", [16.0], measured)
    extended = ph.vibration.verify_weighting(
        "Wk", [16.0], measured, expanded_uncertainty_percent=1.0
    )
    agree = int(bare.passes) + int(not extended.passes)
    return count(
        agree,
        2,
        subject="verdicts",
        expected_label="11,5 % conforms bare, and not with U = 1 % against +12 %",
    )


@register(
    _METER,
    "ISO 8041-1:2017 13.1 and 14.1",
    "Decision rule at the lower tolerance limit, 2 verdicts",
)
def _chk_decision_rule_lower() -> Outcome:
    """And the same sentence read downwards, where the limit is -11 %.

    The deviation is extended in the direction that can breach the limit, so
    below the design goal the laboratory's uncertainty is subtracted: -10,5 %
    conforms bare and -10,5 % minus 1 % does not.
    """
    measured = _deviating_measurement("Wk", 16.0, -10.5)
    bare = ph.vibration.verify_weighting("Wk", [16.0], measured)
    extended = ph.vibration.verify_weighting(
        "Wk", [16.0], measured, expanded_uncertainty_percent=1.0
    )
    agree = int(bare.passes) + int(not extended.passes)
    return count(
        agree,
        2,
        subject="verdicts",
        expected_label="-10,5 % conforms bare, and not with U = 1 % against -11 %",
    )


@register(
    _METER,
    "ISO 8041-1:2017 13.1 and 14.1",
    "Coverage factor of the expanded uncertainty",
)
def _chk_coverage_factor() -> Outcome:
    """Both clauses print ``k = 2``; 12.1 prints "no less than 2"."""
    return numeric(
        2.0, ph.vibration.ISO8041_COVERAGE_FACTOR, _TOLERANCE, places=4, unit=""
    )


@register(
    _METER,
    "ISO 8041-1:2017 12.11 and 12.13",
    "Maximum permitted expanded uncertainties of measurement, %",
)
def _chk_max_expanded_uncertainties() -> Outcome:
    """The figures the frequency-response and signal-burst tests print.

    12.11.2 (folio 34) permits 4,5 % for the mechanical response, 12.11.3
    (folio 35) 3 % for the electrical one, 12.11.4 (folio 35) 5 % for the
    overall response that combines them, and 12.13 (folio 36) 3 % for the
    signal-burst test. They bound the uncertainty the decision rule of 13.1
    extends a measured deviation by.
    """
    printed = {"12.11.2": 4.5, "12.11.3": 3.0, "12.11.4": 5.0, "12.13": 3.0}
    computed = {
        clause: ph.vibration.MAX_EXPANDED_UNCERTAINTY_PERCENT[clause]
        for clause in printed
    }
    return record(printed, computed, unit="%")


@register(
    _METER,
    "ISO 8041-1:2017 Table 1",
    "Nominal frequency range, 9 weightings",
)
def _chk_nominal_frequency_ranges() -> Outcome:
    """The column of Table 1 that 5.7, 5.10 and 12.11 are written against.

    Nominal values, printed as round numbers: the hand-transmitted range
    opens at "8 Hz", which is the band centred on 10**(9/10) = 7,943 Hz, and
    the range is the printed 8 rather than that centre.
    """
    printed = {
        "Wb": (0.5, 80.0),
        "Wc": (0.5, 80.0),
        "Wd": (0.5, 80.0),
        "We": (0.5, 80.0),
        "Wf": (0.1, 0.5),
        "Wh": (8.0, 1000.0),
        "Wj": (0.5, 80.0),
        "Wk": (0.5, 80.0),
        "Wm": (1.0, 80.0),
    }
    agree = sum(
        1
        for name, bounds in printed.items()
        for a, b in zip(
            bounds, ph.vibration.NOMINAL_FREQUENCY_RANGE_HZ[name], strict=True
        )
        if a == b
    )
    return count(
        agree,
        18,
        subject="printed range bounds",
        expected_label="18 printed range bounds, 9 weightings",
    )


@register(
    _METER,
    "ISO 8041-1:2017 Table 1",
    "Nominal frequency range of the three applications, Hz",
)
def _chk_nominal_range_bounds() -> Outcome:
    """The four bounds that are not shared: the two extremes of each end."""
    ranges = ph.vibration.NOMINAL_FREQUENCY_RANGE_HZ
    printed = {
        "Wh lower": 8.0,
        "Wh upper": 1000.0,
        "Wm lower": 1.0,
        "Wf upper": 0.5,
    }
    computed = {
        "Wh lower": ranges["Wh"][0],
        "Wh upper": ranges["Wh"][1],
        "Wm lower": ranges["Wm"][0],
        "Wf upper": ranges["Wf"][1],
    }
    return record(printed, computed, unit="Hz")


@register(
    _METER,
    "ISO 8041-1:2017 Formula (H.4)",
    "Peak-value deviation at 12 degrees of characteristic phase deviation, %",
)
def _chk_peak_deviation_at_twelve_degrees() -> Outcome:
    """The only worked number in the phase argument.

    Annex H prints, right under Formula (H.4): "For the maximum characteristic
    phase deviations of 12°, the maximum peak value deviation is approximately
    10 %". The tolerance is the word "approximately": 0,48 sin 12 degrees is
    9,98 %, which is 10 % to the two significant figures printed.
    """
    return numeric(
        10.0,
        ph.vibration.peak_deviation_percent(12.0),
        0.05,
        unit="%",
        places=4,
    )


def _annex_b_design_phase_deg(weighting: str) -> tuple[np.ndarray, np.ndarray]:
    """The design-goal phase on the Annex B grid, as that annex prints it.

    The one-third-octave centres of Annex B are the exact ``10**(n/10)`` of
    Formula (B.1), and the tables print one continuous phase branch, so the
    principal value of Formula (H.1) is unwrapped along the grid before it is
    compared with them.
    """
    rows = ref.ISO8041_1_ANNEX_B_PHASES_DEG[weighting]
    frequencies = np.array([10.0 ** (n / 10.0) for n, _ in rows])
    response = ph.vibration.frequency_weighting(weighting, frequencies).response
    return frequencies, np.degrees(np.unwrap(np.angle(response)))


#: The print rounding of the Annex B phase columns: the coarsest cells carry
#: one decimal, so a computed value is as good as the page can say when it
#: sits inside half of one.
_PHASE_ROUNDING_DEG = 0.05

#: The sampled Annex B phase cells, one per printed table: weighting, band
#: number, and the phase the table prints in degrees.
_ANNEX_B_PHASE_CELLS = (
    ("Wh", 22, -93.75),  # Table B.6, 158,5 Hz
    ("Wb", 0, 42.42),  # Table B.1, 1 Hz
    ("Wk", 12, -61.84),  # Table B.8, 15,85 Hz
    ("Wf", -4, -162.1),  # Table B.5, 0,3981 Hz
)


def _register_annex_b_phase_cells() -> None:
    """One row per sampled cell of the Annex B phase columns."""
    for weighting, band, printed in _ANNEX_B_PHASE_CELLS:
        rows = ref.ISO8041_1_ANNEX_B_PHASES_DEG[weighting]
        index = [n for n, _ in rows].index(band)
        frequency = 10.0 ** (band / 10.0)

        def _check(
            weighting: str = weighting, index: int = index, printed: float = printed
        ) -> Outcome:
            _, design = _annex_b_design_phase_deg(weighting)
            return numeric(
                printed,
                float(design[index]),
                _PHASE_ROUNDING_DEG,
                unit="deg",
                places=4,
            )

        register(
            _METER,
            "ISO 8041-1:2017 Annex B",
            f"{weighting} design-goal phase at {frequency:.4g} Hz, degrees",
        )(_check)


_register_annex_b_phase_cells()


@register(
    _METER,
    "ISO 8041-1:2017 Annex B",
    "Design-goal phase columns of Tables B.1 to B.9, 318 cells",
)
def _chk_annex_b_phase_columns() -> Outcome:
    """Every printed phase cell of the annex, against Formula (H.1).

    Formula (H.1) (folio 92) says the design goal for the phase response is
    the argument of the ``H(s)`` of Formula (5), and that "Values for the
    phase angle φ are included in Tables B.1 to B.9". This is those tables,
    read whole: 318 cells across nine weightings, each within the rounding of
    the figures it is printed to.
    """
    inside = 0
    total = 0
    for weighting, rows in ref.ISO8041_1_ANNEX_B_PHASES_DEG.items():
        _, design = _annex_b_design_phase_deg(weighting)
        printed = np.array([phase for _, phase in rows])
        total += len(rows)
        inside += int(np.count_nonzero(np.abs(design - printed) <= _PHASE_ROUNDING_DEG))
    return count(
        inside,
        total,
        subject="printed phase cells",
        expected_label="318 printed phase cells, 9 weightings",
    )


@register(
    _METER,
    "ISO 8041-1:2017 Table 5",
    "Printed phase columns judged by Formula (6), 9 weightings",
)
def _chk_annex_b_phase_columns_conform() -> Outcome:
    """The printed columns, fed back as a measurement, conform to Table 5.

    A meter whose phase response is the design goal to the figures the annex
    prints has to pass the criterion the same annex tabulates beside it. The
    slack is real and worth recording: the largest characteristic phase
    deviation the rounding of the printed columns produces is 0,39 degrees,
    against the 6 degrees of the central region.
    """
    conforming = 0
    for weighting, rows in ref.ISO8041_1_ANNEX_B_PHASES_DEG.items():
        frequencies = np.array([10.0 ** (n / 10.0) for n, _ in rows])
        printed = np.array([phase for _, phase in rows])
        verdict = ph.vibration.verify_phase_response(weighting, frequencies, printed)
        conforming += int(verdict.passes)
    return count(
        conforming,
        len(ref.ISO8041_1_ANNEX_B_PHASES_DEG),
        subject="weightings",
        expected_label="9 printed phase columns inside Table 5",
    )


@register(
    _METER,
    "ISO 8041-1:2017 H.2.3.4 n)",
    "Characteristic phase deviation of a constant group delay, degrees",
)
def _chk_constant_group_delay() -> Outcome:
    """What the criterion is built to ignore.

    NOTE 1 of H.2.1 says a constant group delay, which is a phase deviation
    proportional to frequency, "would probably far exceed the tolerances on
    phase deviation, but would influence neither the vibration parameters to
    be measured nor the characteristic phase deviation values", and H.2.3.4 n)
    repeats it: "any remaining constant delay time (except 180°) does not
    influence the result at all". One millisecond of delay is 1 433 degrees of
    phase error at the top of the hand-transmitted range and nothing at all
    here.
    """
    frequencies = np.array([10.0 ** (n / 10.0) for n in range(-1, 37)])
    deviation = -0.001 * 360.0 * frequencies
    computed = ph.vibration.characteristic_phase_deviation(frequencies, deviation)
    return numeric(
        0.0,
        float(np.max(np.abs(computed))),
        1e-9,
        unit="deg",
        places=9,
        expected_label="0 deg for any constant delay",
    )
