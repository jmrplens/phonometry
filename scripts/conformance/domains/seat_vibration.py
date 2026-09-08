#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What a seat does to the vibration under it (ISO 10326-1).

The standard is a method rather than a table: it fixes how the seat is
measured and leaves every acceptance value to the application standard written
for the machine. What is numeric in it is the arithmetic of the two tests and
the tolerances they are run under, and that is what these rows pin.

The correction row is the interesting one. The printed Formula (3) asterisks
all four of its symbols and so reduces to an identity; Formula (4) beside it,
with the SEAT factor of Formula (2) substituted, gives the reading the clause
prose asks for. The row computes it both ways and asks them to agree, which is
the argument the errata entry rests on.

Oracle: ISO 10326-1:2016, Clause 10 on printed folios 11 and 12 (PDF pages 17
and 18): Formula (2), the ± 5 % of 10.2.1, Formulae (3) and (4) of 10.2.3, and
Formula (5) with the 75 kg inert mass of 10.3.
"""

from __future__ import annotations

import phonometry as ph

from ..registry import Outcome, numeric, register

_SEAT = "Seat vibration transmission (ISO 10326-1)"

#: One test, in the units the standard measures in: the weighted r.m.s.
#: acceleration of three runs at the platform and three at the seat, agreeing
#: well inside the tolerance 10.2.1 allows.
_PLATFORM_RUNS = (1.02, 1.00, 0.99)
_SEAT_RUNS = (0.72, 0.70, 0.71)

#: 10.2.3: the input the test intended, against the 1,00333... it delivered.
_INTENDED_PLATFORM = 1.10

#: 10.3: the two readings at resonance of a seat that doubles what it is given.
_RESONANCE_SEAT = 2.4
_RESONANCE_PLATFORM = 1.2

_TOLERANCE = 5e-4


@register(_SEAT, "ISO 10326-1:2016 Formula (2)", "SEAT factor of one test")
def _chk_seat_factor() -> Outcome:
    """The ratio of the two means, which is the whole verdict."""
    result = ph.vibration.seat_transmission(_SEAT_RUNS, _PLATFORM_RUNS)
    printed = (sum(_SEAT_RUNS) / 3.0) / (sum(_PLATFORM_RUNS) / 3.0)
    return numeric(printed, result.seat_factor, _TOLERANCE, places=4)


@register(
    _SEAT,
    "ISO 10326-1:2016 Clause 10.2.1",
    "Mean of three agreeing runs at the platform, m/s2",
)
def _chk_run_mean() -> Outcome:
    """The arithmetic mean 10.2.1 records, from runs inside its tolerance."""
    computed = ph.vibration.mean_of_test_runs(_PLATFORM_RUNS)
    return numeric(
        sum(_PLATFORM_RUNS) / 3.0, computed, _TOLERANCE, unit="m/s2", places=4
    )


@register(
    _SEAT,
    "ISO 10326-1:2016 Clause 10.2.1",
    "Agreement three consecutive runs must keep, %",
)
def _chk_tolerance() -> Outcome:
    """The ± 5 % of 10.2.1, as the percentage it is printed as."""
    return numeric(
        5.0,
        100.0 * ph.vibration.RUN_AGREEMENT_TOLERANCE,
        _TOLERANCE,
        unit="%",
        places=4,
    )


@register(
    _SEAT,
    "ISO 10326-1:2016 Formula (4)",
    "Corrected magnitude on the seat, m/s2",
)
def _chk_correction() -> Outcome:
    """Formula (4), against the reading the prose of 10.2.3 asks for.

    The printed Formula (3) is an identity (see ``docs/ERRATA.md``); the
    expected value here is the correction its own prose describes, and the
    computed one comes through the SEAT factor of Formula (2), which is the
    route Formula (4) takes.
    """
    seat = sum(_SEAT_RUNS) / 3.0
    platform = sum(_PLATFORM_RUNS) / 3.0
    printed = seat * _INTENDED_PLATFORM / platform
    computed = ph.vibration.corrected_seat_acceleration(
        seat, platform, _INTENDED_PLATFORM
    )
    return numeric(printed, computed, _TOLERANCE, unit="m/s2", places=4)


@register(
    _SEAT,
    "ISO 10326-1:2016 Formula (5)",
    "Transmissibility at resonance of the damping test",
)
def _chk_transmissibility() -> Outcome:
    """The ratio at the resonance frequency, which is the damping verdict."""
    computed = ph.vibration.resonance_transmissibility(
        _RESONANCE_SEAT, _RESONANCE_PLATFORM
    )
    return numeric(
        _RESONANCE_SEAT / _RESONANCE_PLATFORM, computed, _TOLERANCE, places=4
    )


@register(
    _SEAT,
    "ISO 10326-1:2016 Clause 10.3",
    "Inert mass the seat carries for the damping test, kg",
)
def _chk_damping_mass() -> Outcome:
    """75 kg, and the 1 % the same sentence allows around it."""
    return numeric(
        75.0, ph.vibration.DAMPING_TEST_MASS_KG, _TOLERANCE, unit="kg", places=4
    )


@register(
    _SEAT,
    "ISO 10326-1:2016 Clause 9.5.1",
    "Reduced test mass for an actively damped suspension, kg",
)
def _chk_active_mass() -> Outcome:
    """The 60 kg the clause reports as having been found appropriate."""
    return numeric(
        60.0,
        ph.vibration.ACTIVE_DAMPING_TEST_MASS_KG,
        _TOLERANCE,
        unit="kg",
        places=4,
    )
