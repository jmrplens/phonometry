#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Measuring vibration immission in buildings (DIN 45669-1).

DIN 4150-2 and DIN 4150-3 print thresholds; DIN 45669-1 prints the instrument
that produces the numbers those thresholds are compared with, and it prints
enough of them to be checked end to end. These rows do exactly that: a 1 mm/s
sine or a burst of one is generated, run through the band limitation, the KB
weighting and the running r.m.s. of Formula (1), and the indication that comes
out is compared with the printed one.

That is why the rows are worth having. ``KB_Fmax`` sits above ``KB_F`` by the
ripple of a running r.m.s. of a sine, and neither the ripple nor the response
of the chain to a burst of eight cycles has a closed form printed anywhere: a
row that restated a constant would check nothing, and a row that runs the
chain checks the whole of it.

**The row that is not here.** Table 9 also prints a ``|v|max`` row, and two of
its five cells cannot be reproduced: at 31,5 Hz it prints 1,000 where Formula
(5) gives 0,995 and at 315 Hz it prints 0,249 where Formula (5) gives 0,100,
while the ``KB_F`` row of the same two columns follows Formula (5). It is
registered in ``docs/ERRATA.md`` instead.

Oracle: DIN 45669-1:2010-09, Tables 2 and 3 on printed folio 19, Table 9 and
the reference indications of 6.2.3.12 on printed folio 35, Table E.1 on folio
49 and Table E.2 on folio 51; Table 8 in the redraft of DIN 45669-1
Berichtigung 1:2012-12, printed folio 2.
"""

from __future__ import annotations

import functools
import math

import numpy as np

import phonometry as ph

from ..registry import Outcome, numeric, register

_IMMISSION = "Vibration immission measurement (DIN 45669)"
_EDITION = "DIN 45669-1:2010"
_CORRIGENDUM = "DIN 45669-1:2010 Ber 1"

#: A rate that carries the whole building working range with room above it,
#: and a record long enough for the running r.m.s. to have settled. 315 Hz is
#: what fixes it: a bilinear design warps the response near Nyquist, and the
#: top row of Table 9 is read where the low pass is already 20 dB down.
_FS_HZ = 32768.0
_RECORD_S = 12.0
#: The test signal is raised over this many seconds rather than switched on:
#: an abrupt onset drives the band limitation with a step, and a max-hold
#: keeps the transient that follows.
_RAMP_S = 1.0
#: The indication is read after the averaging has settled, which 4 tau puts at
#: half a second.
_SETTLE_S = _RAMP_S + 3.0

#: Table 9 on printed folio 35, the rows that follow Formulae (5) and (6):
#: the KB_F and KB_Fmax a 1 mm/s sine must show at each test frequency.
_TABLE_9 = {
    1.0: (0.103, 0.130),
    5.6: (0.500, 0.528),
    31.5: (0.693, 0.700),
    80.0: (0.594, 0.597),
    315.0: (0.071, 0.071),
}
#: 6.2.3.12: what the 16 Hz reference signal must show.
_REFERENCE = {"kbf": 0.667, "kbf_max": 0.680}
#: One unit in the last printed place. Tighter than either allowance the
#: standard itself carries: the KB_F row is printed with a 2 % fluctuation
#: band, which at 0,5 is 0,010, and Tables 2 and 3 allow the response behind
#: these numbers 10 %. What is left at this precision is the ripple of a
#: running r.m.s., whose mean sits a little below the ideal value at the
#: frequencies where the period and the 0,125 s time constant are comparable.
_INDICATION_TOLERANCE = 0.001

#: Table 8 as Berichtigung 1 rewrites it: bursts of an 80 Hz sine repeated once
#: a second, and the KB_Fmax each shows as a percentage of the indication for
#: the continuous signal of the same amplitude.
_TABLE_8 = {
    math.inf: 100.4,
    800.0: 100.3,
    400.0: 98.3,
    200.0: 89.7,
    100.0: 74.5,
    50.0: 57.6,
    25.0: 42.7,
    12.5: 30.9,
}
#: Points of a percentage. The two shortest bursts are one and two cycles of an
#: 80 Hz sine, where the digital chain and the printed value part company, and
#: the table prints no tolerance of its own.
_PULSE_TOLERANCE = 0.7

#: Table E.1 on printed folio 49, read at the two corners of its segments: the
#: weighting is the guideline curve of DIN 4150-3 Table 1 inverted and
#: normalised to its 1 Hz to 10 Hz value, so at 50 Hz the commercial class,
#: whose curve has risen from 20 mm/s to 40 mm/s, weighs 0,5.
_TABLE_E1 = {
    ("commercial", 50.0): 0.5,
    ("commercial", 100.0): 0.4,
    ("residential", 50.0): 1.0 / 3.0,
    ("residential", 100.0): 0.25,
    ("sensitive", 50.0): 0.375,
    ("sensitive", 100.0): 0.3,
}
#: Table E.2 on printed folio 51: the guideline value each assessment velocity
#: is compared with, in mm/s, independent of frequency.
_TABLE_E2 = {"commercial": 20.0, "residential": 5.0, "sensitive": 3.0}


@functools.cache
def _indications(frequency_hz: float) -> tuple[float, float]:
    """The settled KB_F and the KB_Fmax of a 1 mm/s sine at *frequency_hz*."""
    t = np.arange(int(_RECORD_S * _FS_HZ)) / _FS_HZ
    onset = 0.5 * (1.0 - np.cos(math.pi * np.clip(t / _RAMP_S, 0.0, 1.0)))
    kbf = ph.vibration.kbf_signal(
        onset * np.sin(2.0 * math.pi * frequency_hz * t), _FS_HZ
    )
    settled = kbf[int(_SETTLE_S * _FS_HZ) :]
    return float(settled.mean()), float(settled.max())


@functools.cache
def _burst_indication(duration_ms: float) -> float:
    """KB_Fmax of the 80 Hz burst train, as a percentage of the continuous one."""
    t = np.arange(int(20.0 * _FS_HZ)) / _FS_HZ
    carrier = np.sin(2.0 * math.pi * 80.0 * t)
    settled = slice(int(_SETTLE_S * _FS_HZ), None)
    continuous = ph.vibration.kbf_signal(carrier, _FS_HZ)[settled]
    if math.isinf(duration_ms):
        shown = float(continuous.max())
    else:
        gate = (np.mod(t, 1.0) < duration_ms / 1000.0).astype(float)
        shown = float(ph.vibration.kbf_signal(carrier * gate, _FS_HZ)[settled].max())
    return shown / float(continuous.mean()) * 100.0


def _chk_table_9_kbf(frequency_hz: float) -> Outcome:
    """The settled KB_F of Table 9 at one test frequency."""
    return numeric(
        _TABLE_9[frequency_hz][0],
        _indications(frequency_hz)[0],
        _INDICATION_TOLERANCE,
        places=4,
    )


def _chk_table_9_kbf_max(frequency_hz: float) -> Outcome:
    """The KB_Fmax of Table 9 at one test frequency, ripple included."""
    return numeric(
        _TABLE_9[frequency_hz][1],
        _indications(frequency_hz)[1],
        _INDICATION_TOLERANCE,
        places=4,
    )


def _chk_reference(quantity: str) -> Outcome:
    """One of the reference indications of 6.2.3.12, at 16 Hz."""
    kbf, kbf_max = _indications(ph.vibration.KB_REFERENCE_FREQUENCY_HZ)
    computed = kbf if quantity == "kbf" else kbf_max
    return numeric(_REFERENCE[quantity], computed, _INDICATION_TOLERANCE, places=4)


def _chk_table_8(duration_ms: float) -> Outcome:
    """One burst duration of Table 8, in per cent of the continuous display."""
    return numeric(
        _TABLE_8[duration_ms],
        _burst_indication(duration_ms),
        _PULSE_TOLERANCE,
        unit="%",
        places=3,
    )


def _chk_table_e1(building_class: str, frequency_hz: float) -> Outcome:
    """One corner of one Annex E weighting curve."""
    computed = float(
        ph.vibration.assessment_weighting_response(
            [frequency_hz], building_class=building_class
        )[0]
    )
    return numeric(_TABLE_E1[(building_class, frequency_hz)], computed, 5e-5, places=5)


def _chk_table_e2(building_class: str) -> Outcome:
    """One frequency-independent guideline value of Table E.2."""
    return numeric(
        _TABLE_E2[building_class],
        ph.vibration.ASSESSMENT_GUIDE_VALUES_MM_S[building_class],
        5e-4,
        unit="mm/s",
        places=4,
    )


@register(
    _IMMISSION,
    f"{_EDITION} 5.2.3.2",
    "Band limitation at the lower corner 0,8 f_u, magnitude",
)
def _chk_lower_corner() -> Outcome:
    """The note under Formula (3) puts the high pass at 0,8 Hz for f_u = 1 Hz."""
    computed = float(abs(ph.vibration.band_limitation_response([0.8])[0]))
    return numeric(1.0 / math.sqrt(2.0), computed, 5e-5, places=5)


@register(
    _IMMISSION,
    f"{_EDITION} 5.2.3.2",
    "Band limitation at the upper corner f_o / 0,8, magnitude",
)
def _chk_upper_corner() -> Outcome:
    """And the low pass at 100 Hz for f_o = 80 Hz, three decibels down."""
    computed = float(abs(ph.vibration.band_limitation_response([100.0])[0]))
    return numeric(1.0 / math.sqrt(2.0), computed, 5e-5, places=5)


@register(
    _IMMISSION,
    f"{_EDITION} 5.2.3.2",
    "KB weighting at its own corner 5,6 Hz, relative to the band limitation",
)
def _chk_kb_corner() -> Outcome:
    """Formula (4) divides by ``1 - j 5,6 Hz / f``, so 5,6 Hz is 3 dB down."""
    band = float(abs(ph.vibration.band_limitation_response([5.6])[0]))
    weighted = float(abs(ph.vibration.kb_weighting_response([5.6])[0]))
    return numeric(1.0 / math.sqrt(2.0), weighted / band, 5e-5, places=5)


@register(_IMMISSION, f"{_EDITION} Table 2", "Lower limit of F(f) inside the band, %")
def _chk_central_lower() -> Outcome:
    """From 1,25 f_u to 0,8 f_o the response may fall 10 % short."""
    lower, _ = ph.vibration.response_tolerance_percent([16.0])
    return numeric(10.0, float(lower[0]), 1e-9, unit="%", places=3)


@register(_IMMISSION, f"{_EDITION} Table 2", "Lower limit of F(f) in the skirt, %")
def _chk_skirt_lower() -> Outcome:
    """Outside that band and inside 0,5 f_u to 2 f_o, twice as much."""
    lower, _ = ph.vibration.response_tolerance_percent([1.0])
    return numeric(20.0, float(lower[0]), 1e-9, unit="%", places=3)


@register(_IMMISSION, f"{_EDITION} Table 3", "Upper limit of F(f) outside the band, %")
def _chk_outside_upper() -> Outcome:
    """Table 3 keeps constraining the response from above where Table 2 stops."""
    _, upper = ph.vibration.response_tolerance_percent([200.0])
    return numeric(20.0, float(upper[0]), 1e-9, unit="%", places=3)


def _register_indications() -> None:
    """Table 9 and the reference indications of 6.2.3.12."""
    for frequency_hz in _TABLE_9:
        register(
            _IMMISSION,
            f"{_EDITION} Table 9",
            f"KB_F of a 1 mm/s sine at {frequency_hz:g} Hz",
        )(functools.partial(_chk_table_9_kbf, frequency_hz))
        register(
            _IMMISSION,
            f"{_EDITION} Table 9",
            f"KB_Fmax of a 1 mm/s sine at {frequency_hz:g} Hz",
        )(functools.partial(_chk_table_9_kbf_max, frequency_hz))
    for quantity, label in (("kbf", "KB_F"), ("kbf_max", "KB_Fmax")):
        register(
            _IMMISSION,
            f"{_EDITION} 6.2.3.12",
            f"{label} under the reference conditions (1 mm/s, 16 Hz)",
        )(functools.partial(_chk_reference, quantity))


def _register_pulse_response() -> None:
    """Table 8 as the corrigendum rewrites it."""
    for duration_ms in _TABLE_8:
        printed = "continuous" if math.isinf(duration_ms) else f"{duration_ms:g} ms"
        register(
            _IMMISSION,
            f"{_CORRIGENDUM}, Table 8",
            f"KB_Fmax of an 80 Hz burst train, {printed}, % of continuous",
        )(functools.partial(_chk_table_8, duration_ms))


def _register_annex_e() -> None:
    """The three weighting curves and the three guideline values."""
    for building_class, frequency_hz in _TABLE_E1:
        register(
            _IMMISSION,
            f"{_EDITION} Annex E, Table E.1",
            f"Assessment weighting H_vB, {building_class}, at {frequency_hz:g} Hz",
        )(functools.partial(_chk_table_e1, building_class, frequency_hz))
    for building_class in _TABLE_E2:
        register(
            _IMMISSION,
            f"{_EDITION} Annex E, Table E.2",
            f"Guideline assessment velocity, {building_class}, mm/s",
        )(functools.partial(_chk_table_e2, building_class))


_register_indications()
_register_pulse_response()
_register_annex_e()
