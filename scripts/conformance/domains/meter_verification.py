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

Oracle: ISO 8041-1:2017, printed folios 9, 12 and 15 (PDF pages 17, 20 and
23): Table 1 (reference vibration values and frequencies), Table 2
(tolerances of indication), Table 4 (transition frequencies) and Table 5
(tolerances on frequency weightings).
"""

from __future__ import annotations

import phonometry as ph

from ..registry import Outcome, numeric, register

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
