#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The saw-tooth signal burst of ISO 8041-1:2017, 5.9, and what a meter reads.

Clause 5.9 is the one place where ISO 8041-1 prints an oracle instead of a
requirement. It defines a test signal in Table 6 (folio 17), and then prints
in Tables 7, 8 and 9 (folios 17, 18 and 19) the 228 indications a conforming
human-vibration meter has to show when that signal is applied, each with the
tolerance it is judged against. The standard says where those numbers come
from: "NOTE 1 The response to the saw-tooth signal burst is determined by
digital simulation of the filter characteristics" (folio 16). They are
arithmetic, so a library that implements the weightings and the four
indication quantities can reproduce them, and this module does.

**The signal.** Figure 3 (folio 17) draws it: a bipolar saw-tooth of
amplitude 1 m/s2 from zero to peak, a linear rising ramp and a vertical fall,
with every burst starting at an upward zero crossing and ending at one. That
geometry is load-bearing rather than decorative: a burst started at the peak
reads 28 % high on the single-cycle row of Table 8, four times its tolerance.
Table 6 supplies the rest, per application: the angular frequency, the start
time of the first burst, the burst lengths (1, 2, 4, 8 and 16 cycles, plus a
continuous row), the repeat time and the measurement duration. Six bursts fit
in the printed duration in all three applications.

**Three conventions the tables do not print**, each fixed here by measuring
which reading reproduces the page:

1. *The continuous row starts at t = 0* and fills the printed duration; it
   does not start at the Table 6 start time. Read from zero, the band-limiting
   continuous cell of Table 7 comes out 0,564 9 against the 0,565 printed;
   started at 0,2 s it comes out 0,560 1.
2. *The filtering is zero state.* :func:`~phonometry.vibration.apply_weighting`
   multiplies in the frequency domain without padding, which is a circular
   convolution, and its own docstring says so. In the continuous row that
   wraps the tail of the record onto its front and erases the switch-on
   transient the linear MTVV is built to catch: filtered circularly, four
   continuous cells of Table 8 sit at Wc -0,81 %, Wm -1,10 %, Wd -3,24 % and
   We -5,19 %; filtered from rest they sit at -0,17 %, -0,31 %, -0,36 % and
   -0,52 %. This module therefore pads the record with zeros before applying
   the response and keeps the first samples back, which is a filter switched
   on at t = 0 with nothing stored in it. The default behaviour of
   :func:`~phonometry.vibration.apply_weighting` is deliberately left alone:
   the choice belongs to this test, not to every weighted signal.
3. *The MTVV integration time is 1 s* (ISO 2631-1 6.3.1, and the constant
   Annex D of this standard is written around). With any other constant the
   two MTVV columns stop lining up. It is also why the continuous row of the
   linear MTVV repeats the 16-cycle value for whole-body vibration: 16 cycles
   at 15,915 Hz last 1,005 s, so the burst already fills the window.

**Which band limiting the band-limiting row is.** 5.6.6 (folio 14) makes the
band-limiting response a graded quantity of its own, and Tables 7 to 9 give it
18 of their 72 rows. Six of the seven whole-body weightings share the corner
pair 0,4 Hz and 100 Hz of Table 3 and ``Wm`` does not, so the whole-body row
had to be decided by measurement as well: with the shared pair the 24 printed
cells reproduce to -0,25 % at worst, with the ``Wm`` pair to +0,67 %. The
hand-arm and low-frequency rows have only one candidate each, ``Wh`` and
``Wf``.

**What the reproduction is worth.** At the sampling rates recommended per
application, all 228 printed cells come out within 2,3 %, against printed
tolerances of 10 % and 12 %. The three widest are the 2-cycle row of ``Wf``
and the 8-cycle row of ``We``, cells the page prints to three significant
figures and whose weightings attenuate hardest.

**What a pass means.** The signal-burst response is one clause of a standard
that also grades indication, linearity, overload, timing and environmental
behaviour. A verdict here says the time response of the weighting chain
matches the printed table, and nothing else.

ISO 8041-2:2021 5.9 (folio 11) repeats this clause for personal vibration
exposure meters with the same Table 6 and the same Tables 7 to 9, so one
implementation covers both parts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.validation import require_choice
from .exposure import (
    _params,
    frequency_weighting,
    motion_sickness_dose_value,
    mtvv,
    vibration_dose_value,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import NDArray

#: The row of Tables 7 to 9 that grades the band-limiting response instead of
#: a frequency weighting, named rather than spelled out at every call site.
BAND_LIMITING = "band-limiting"

#: The averaging time of the two MTVV columns of Table 8, in seconds. Not
#: printed in the table: recovered by reproducing it, and the "slow" constant
#: of ISO 2631-1 6.3.1 that Annex D of this standard is written around.
_MTVV_INTEGRATION_TIME_S = 1.0

#: The number of half-widths of the fall time 12.13 allows, in
#: ``1 / (5 * f2)``.
_FALL_TIME_DIVISOR = 5.0


def _max_fall_time_s(name: str) -> float:
    """The fall time 12.13 (folio 36) allows a generator, in seconds.

    "The fall time of the saw-tooth burst wave shall be no more than
    ``1/(5 f2)``, where f2 is the upper limiting frequency of the
    band-limiting component of the appropriate frequency weighting, defined in
    Table 3."

    :param name: The weighting whose band limiting the application is tested
        with.
    :return: The largest permitted fall time, in seconds.
    """
    return 1.0 / (_FALL_TIME_DIVISOR * _params(name).f2)


@dataclass(frozen=True)
class SawtoothBurstTest:
    """One application's row of ISO 8041-1 Table 6 (folio 17).

    :ivar application: The application key, as :data:`SAWTOOTH_BURST_TESTS`
        files it.
    :ivar weightings: The frequency weightings the application is tested with,
        in Table 6 order.
    :ivar band_limiting_weighting: The weighting whose Table 3 corners are the
        band-limiting response of this application's band-limiting row.
    :ivar angular_frequency_rad_s: The saw-tooth angular frequency, in radians
        per second, which is what the table prints.
    :ivar start_time_s: When the first burst starts, in seconds.
    :ivar cycle_counts: The printed burst lengths, in saw-tooth cycles.
    :ivar repeat_time_s: The interval between burst starts, in seconds.
    :ivar duration_s: The measurement duration, in seconds.
    :ivar max_fall_time_s: The largest fall time 12.13 allows a real generator,
        in seconds. The record :func:`sawtooth_burst` synthesises has the ideal
        vertical fall of Figure 3; this is the laboratory limit, not a
        property of the synthesised signal.
    :ivar recommended_sampling_rate_hz: The rate :func:`sawtooth_burst` uses
        when the caller names none. Chosen so that the printed cells are
        reproduced to a few tenths of a per cent, which is not a normative
        figure: nothing in the standard prescribes a sampling rate.
    """

    application: str
    weightings: tuple[str, ...]
    band_limiting_weighting: str
    angular_frequency_rad_s: float
    start_time_s: float
    cycle_counts: tuple[int, ...]
    repeat_time_s: float
    duration_s: float
    max_fall_time_s: float
    recommended_sampling_rate_hz: float

    @property
    def frequency_hz(self) -> float:
        """The saw-tooth frequency, in hertz.

        Table 6 prints it beside the angular frequency (79,58 Hz, 15,915 Hz
        and 0,397 9 Hz); this is the division, not the rounded decimal.
        """
        return self.angular_frequency_rad_s / (2.0 * math.pi)

    @property
    def burst_count(self) -> int:
        """How many bursts the printed duration holds at the repeat time."""
        return int(
            math.ceil((self.duration_s - self.start_time_s) / self.repeat_time_s)
        )


_HAND_ARM = "hand-arm"
_WHOLE_BODY = "whole-body"
_LOW_FREQUENCY_WHOLE_BODY = "low-frequency-whole-body"

#: The printed burst lengths of Table 6, shared by the three applications.
_CYCLE_COUNTS = (1, 2, 4, 8, 16)

#: ISO 8041-1:2017 Table 6 (folio 17), one entry per application. The
#: continuous row of Tables 7 to 9 is requested with ``cycles=None`` and is
#: not a sixth entry here, because Table 6 does not give it a burst length.
SAWTOOTH_BURST_TESTS: dict[str, SawtoothBurstTest] = {
    _HAND_ARM: SawtoothBurstTest(
        application=_HAND_ARM,
        weightings=("Wh",),
        band_limiting_weighting="Wh",
        angular_frequency_rad_s=500.0,
        start_time_s=0.2,
        cycle_counts=_CYCLE_COUNTS,
        repeat_time_s=2.0,
        duration_s=12.0,
        max_fall_time_s=_max_fall_time_s("Wh"),
        recommended_sampling_rate_hz=200_000.0,
    ),
    _WHOLE_BODY: SawtoothBurstTest(
        application=_WHOLE_BODY,
        weightings=("Wb", "Wc", "Wd", "We", "Wj", "Wk", "Wm"),
        band_limiting_weighting="Wb",
        angular_frequency_rad_s=100.0,
        start_time_s=1.0,
        cycle_counts=_CYCLE_COUNTS,
        repeat_time_s=10.0,
        duration_s=60.0,
        max_fall_time_s=_max_fall_time_s("Wb"),
        recommended_sampling_rate_hz=20_000.0,
    ),
    _LOW_FREQUENCY_WHOLE_BODY: SawtoothBurstTest(
        application=_LOW_FREQUENCY_WHOLE_BODY,
        weightings=("Wf",),
        band_limiting_weighting="Wf",
        angular_frequency_rad_s=2.5,
        start_time_s=40.0,
        cycle_counts=_CYCLE_COUNTS,
        repeat_time_s=400.0,
        duration_s=2400.0,
        max_fall_time_s=_max_fall_time_s("Wf"),
        recommended_sampling_rate_hz=200.0,
    ),
}

#: The tolerance each printed column of Tables 7 to 9 is judged against, in
#: per cent. Every column is 10 % except the vibration dose value, which is
#: 12 % in all 48 of its cells.
BURST_TOLERANCE_PERCENT: dict[str, float] = {
    "rms": 10.0,
    "vdv": 12.0,
    "mtvv_linear": 10.0,
    "mtvv_exponential": 10.0,
    "msdv": 10.0,
}

#: The quantities each table prints, in printed column order.
_TABLE_7_QUANTITIES = ("rms",)
_TABLE_8_QUANTITIES = ("rms", "vdv", "mtvv_linear", "mtvv_exponential")
_TABLE_9_QUANTITIES = ("rms", "msdv")

#: The rows of Tables 7 to 9, keyed by burst length with ``None`` for the
#: continuous row, in the printed column order of the table above them.
_TABLE_7_ROWS: dict[str, dict[int | None, tuple[float, ...]]] = {
    BAND_LIMITING: {
        1: (0.0448,),
        2: (0.0633,),
        4: (0.0895,),
        8: (0.127,),
        16: (0.179,),
        None: (0.565,),
    },
    "Wh": {
        1: (0.0103,),
        2: (0.0133,),
        4: (0.0168,),
        8: (0.0224,),
        16: (0.0309,),
        None: (0.0946,),
    },
}

_TABLE_8_ROWS: dict[str, dict[int | None, tuple[float, ...]]] = {
    BAND_LIMITING: {
        1: (0.0433, 0.498, 0.137, 0.135),
        2: (0.0612, 0.593, 0.193, 0.188),
        4: (0.0865, 0.705, 0.274, 0.258),
        8: (0.122, 0.838, 0.387, 0.344),
        16: (0.173, 0.996, 0.547, 0.437),
        None: (0.546, 1.77, 0.547, 0.549),
    },
    "Wb": {
        1: (0.0314, 0.342, 0.0991, 0.0968),
        2: (0.0435, 0.403, 0.137, 0.132),
        4: (0.0614, 0.482, 0.194, 0.182),
        8: (0.0867, 0.575, 0.274, 0.243),
        16: (0.123, 0.685, 0.387, 0.309),
        None: (0.387, 1.22, 0.388, 0.388),
    },
    "Wc": {
        1: (0.0222, 0.244, 0.0703, 0.0684),
        2: (0.0292, 0.275, 0.0923, 0.0885),
        4: (0.0397, 0.318, 0.126, 0.117),
        8: (0.055, 0.374, 0.174, 0.153),
        16: (0.077, 0.445, 0.243, 0.192),
        None: (0.24, 0.788, 0.243, 0.242),
    },
    "Wd": {
        1: (0.00669, 0.0779, 0.0212, 0.0197),
        2: (0.00906, 0.0852, 0.0286, 0.0264),
        4: (0.0116, 0.0923, 0.0366, 0.033),
        8: (0.0148, 0.101, 0.0469, 0.04),
        16: (0.0197, 0.115, 0.0611, 0.0481),
        None: (0.059, 0.197, 0.0611, 0.0594),
    },
    "We": {
        1: (0.00342, 0.0409, 0.0108, 0.00992),
        2: (0.00478, 0.0452, 0.0151, 0.0135),
        4: (0.00637, 0.0493, 0.0201, 0.0176),
        8: (0.00816, 0.0535, 0.0255, 0.0214),
        16: (0.0102, 0.0592, 0.0311, 0.0244),
        None: (0.0295, 0.0987, 0.0311, 0.0297),
    },
    "Wj": {
        1: (0.0435, 0.517, 0.138, 0.135),
        2: (0.0616, 0.609, 0.195, 0.189),
        4: (0.0874, 0.723, 0.277, 0.261),
        8: (0.124, 0.859, 0.392, 0.349),
        16: (0.175, 1.02, 0.554, 0.443),
        None: (0.554, 1.81, 0.555, 0.557),
    },
    "Wk": {
        1: (0.0299, 0.323, 0.0944, 0.0922),
        2: (0.0411, 0.38, 0.13, 0.125),
        4: (0.0577, 0.455, 0.182, 0.171),
        8: (0.0814, 0.543, 0.257, 0.228),
        16: (0.115, 0.648, 0.363, 0.289),
        None: (0.362, 1.15, 0.364, 0.363),
    },
    "Wm": {
        1: (0.0149, 0.165, 0.0472, 0.0456),
        2: (0.0197, 0.185, 0.0623, 0.0594),
        4: (0.0264, 0.211, 0.0836, 0.0775),
        8: (0.0363, 0.247, 0.115, 0.101),
        16: (0.0507, 0.294, 0.16, 0.126),
        None: (0.158, 0.52, 0.16, 0.159),
    },
}

_TABLE_9_ROWS: dict[str, dict[int | None, tuple[float, ...]]] = {
    BAND_LIMITING: {
        1: (0.0341, 1.671),
        2: (0.0487, 2.386),
        4: (0.069, 3.38),
        8: (0.0982, 4.811),
        16: (0.139, 6.81),
        None: (0.439, 21.51),
    },
    "Wf": {
        1: (0.0197, 0.9651),
        2: (0.0236, 1.156),
        4: (0.0304, 1.489),
        8: (0.0416, 2.038),
        16: (0.0571, 2.797),
        None: (0.176, 8.622),
    },
}

#: The three printed tables, each with the application it grades and the
#: columns it prints, in printed order.
_PrintedTable = tuple[
    str, tuple[str, ...], dict[str, dict[int | None, tuple[float, ...]]]
]
_PRINTED_TABLES: tuple[_PrintedTable, ...] = (
    (_HAND_ARM, _TABLE_7_QUANTITIES, _TABLE_7_ROWS),
    (_WHOLE_BODY, _TABLE_8_QUANTITIES, _TABLE_8_ROWS),
    (_LOW_FREQUENCY_WHOLE_BODY, _TABLE_9_QUANTITIES, _TABLE_9_ROWS),
)


def _build_response_table() -> dict[tuple[str, str, int | None], dict[str, float]]:
    """Flatten the three printed tables into one indication lookup."""
    table: dict[tuple[str, str, int | None], dict[str, float]] = {}
    for application, quantities, rows in _PRINTED_TABLES:
        for row, cells in rows.items():
            for cycles, values in cells.items():
                table[application, row, cycles] = dict(
                    zip(quantities, values, strict=True)
                )
    return table


#: ISO 8041-1:2017 Tables 7, 8 and 9 (folios 17, 18 and 19) as one lookup:
#: ``(application, weighting or BAND_LIMITING, cycles)`` to the indications a
#: conforming meter shows, in the units of the quantity (m/s2 for the r.m.s.
#: value and the two MTVV columns, m/s^1,75 for the VDV, m/s^1,5 for the
#: MSDV). ``cycles`` is ``None`` for the continuous row. The values are the
#: response to a 1 m/s2 amplitude signal and scale with the amplitude of the
#: actual test signal, which is what 5.9 says on folio 16.
SIGNAL_BURST_RESPONSE: dict[tuple[str, str, int | None], dict[str, float]] = (
    _build_response_table()
)


def _require_application(application: str) -> SawtoothBurstTest:
    """Return the Table 6 row of ``application`` or raise ``ValueError``."""
    key = require_choice(str(application), "application", tuple(SAWTOOTH_BURST_TESTS))
    return SAWTOOTH_BURST_TESTS[key]


def _require_row(test: SawtoothBurstTest, name: str) -> str:
    """Return the row of ``name`` in ``test`` or raise ``ValueError``.

    A weighting that belongs to another application is refused rather than
    silently tested: Table 6 pairs each weighting with one application, and
    the printed cells of the other two do not describe it.
    """
    return require_choice(str(name), "name", (BAND_LIMITING, *test.weightings))


def _require_cycles(test: SawtoothBurstTest, cycles: int | None) -> int | None:
    """Return the burst length or raise ``ValueError``.

    ``None`` is the continuous row. Any other length is refused: the tables
    print five, and a length they do not print has no expected indication to
    be judged against.
    """
    if cycles is None:
        return None
    if isinstance(cycles, bool) or not isinstance(cycles, int):
        msg = (
            "'cycles' must be an integer number of saw-tooth cycles, or None "
            "for the continuous row."
        )
        raise TypeError(msg)
    if cycles not in test.cycle_counts:
        msg = (
            f"'cycles' must be one of {test.cycle_counts} or None for the "
            f"continuous row; got {cycles!r}."
        )
        raise ValueError(msg)
    return cycles


def _require_sampling_rate(test: SawtoothBurstTest, fs: float | None) -> float:
    """Resolve and validate the sampling rate of a burst record.

    ``None`` takes the recommended rate of the application. A rate at or below
    twice the upper band-limiting corner of Table 3 is refused: below it the
    pass band of the weighting under test is not even represented, so the
    indications would be an artefact of the sampling rather than a response.
    """
    if fs is None:
        return test.recommended_sampling_rate_hz
    rate = float(fs)
    if not math.isfinite(rate) or rate <= 0.0:
        msg = "'fs' must be a positive, finite sampling frequency."
        raise ValueError(msg)
    nyquist_floor = 2.0 * _params(test.band_limiting_weighting).f2
    if rate <= nyquist_floor:
        msg = (
            f"'fs' must exceed {nyquist_floor:g} Hz, twice the upper "
            f"band-limiting corner of {test.band_limiting_weighting} "
            f"(ISO 8041-1 Table 3); got {rate:g} Hz."
        )
        raise ValueError(msg)
    return rate


def sawtooth_burst(
    application: str,
    cycles: int | None,
    *,
    fs: float | None = None,
    amplitude_m_s2: float = 1.0,
) -> NDArray[np.float64]:
    r"""The saw-tooth burst record of ISO 8041-1 Table 6 (folio 17).

    The full measurement record: zero everywhere except during the bursts,
    which start at ``start_time_s`` and repeat every ``repeat_time_s`` until
    the printed duration runs out (six bursts, in all three applications).
    Each burst is ``cycles`` whole saw-tooth periods, rising linearly from an
    upward zero crossing to ``+amplitude_m_s2``, falling vertically to
    ``-amplitude_m_s2`` and ending back at zero, which is the waveform of
    Figure 3.

    ``cycles=None`` returns the continuous row of Tables 7 to 9 instead: an
    unbroken saw-tooth from ``t = 0`` to the end of the printed duration. The
    start time does not apply to it, and the reason is measured rather than
    printed: read from zero, the band-limiting continuous cell of Table 7
    comes out 0,564 9 against the 0,565 printed, and read from the start time
    it comes out 0,560 1.

    The fall is vertical, as Figure 3 draws it. 12.13 (folio 36) allows a real
    generator a fall time of up to ``1/(5 f2)``, which is
    :attr:`SawtoothBurstTest.max_fall_time_s`, and that allowance describes
    the laboratory rig, not this record.

    :param application: One of the keys of :data:`SAWTOOTH_BURST_TESTS`.
    :param cycles: Saw-tooth cycles per burst (1, 2, 4, 8 or 16), or ``None``
        for the continuous row.
    :param fs: Sampling frequency, in hertz. Finite, positive, and above twice
        the upper band-limiting corner of the weighting under test, below
        which the pass band is not represented and the indications would be an
        artefact of the sampling. ``None`` takes the recommended rate of the
        application.
    :param amplitude_m_s2: Zero-to-peak amplitude, in m/s2. The printed
        responses are for 1 m/s2 and scale with it.
    :return: The record, in m/s2, ``round(duration_s * fs)`` samples long.
    :raises ValueError: If the application, the burst length or the sampling
        rate is not one this clause defines, or the amplitude is not finite
        and positive.
    :raises TypeError: If ``cycles`` is neither an integer nor ``None``.
    """
    test = _require_application(application)
    burst_cycles = _require_cycles(test, cycles)
    rate = _require_sampling_rate(test, fs)
    amplitude = float(amplitude_m_s2)
    if not math.isfinite(amplitude) or amplitude <= 0.0:
        msg = "'amplitude_m_s2' must be positive and finite."
        raise ValueError(msg)

    n = round(test.duration_s * rate)
    times = np.arange(n, dtype=np.float64) / rate
    frequency = test.frequency_hz
    if burst_cycles is None:
        # The continuous row: one unbroken saw-tooth over the whole duration.
        return _ramp(frequency * times, amplitude)

    record = np.zeros(n, dtype=np.float64)
    span_s = burst_cycles / frequency
    start = test.start_time_s
    for _ in range(test.burst_count):
        inside = (times >= start) & (times < start + span_s)
        record[inside] = _ramp(frequency * (times[inside] - start), amplitude)
        start += test.repeat_time_s
    return record


def _ramp(cycles_elapsed: NDArray[np.float64], amplitude: float) -> NDArray[np.float64]:
    r"""The saw-tooth of Figure 3, sampled at whole cycles elapsed.

    :math:`x = A\,(2\,\mathrm{frac}(u + 1/2) - 1)` rises from zero at
    :math:`u = 0`, reaches :math:`+A` just before the half cycle, falls
    vertically to :math:`-A` there and comes back to zero at every whole
    cycle: the rising ramp with the vertical fall that Figure 3 draws, phased
    so that the burst starts and ends at a zero crossing.
    """
    return np.asarray(
        amplitude * (2.0 * np.mod(cycles_elapsed + 0.5, 1.0) - 1.0), dtype=np.float64
    )


def _band_limiting_response(
    name: str, frequencies: NDArray[np.float64]
) -> NDArray[np.complex128]:
    r"""The band-limiting response :math:`H_h(s) H_l(s)` of Formulae (1) and (2).

    The high-pass and low-pass pair of Table 3 without the transition and step
    stages, which 5.6.6 (folio 14) and Annex B grade in their own right and
    which Tables 7 to 9 devote 18 of their 72 rows to. Built from the same
    Table 3 parameters the weightings are built from, so the printed corner
    frequencies exist once in the tree.
    """
    params = _params(name)
    out = np.zeros(frequencies.shape, dtype=np.complex128)
    positive = frequencies > 0.0
    if not np.any(positive):
        return out
    s = 1j * 2.0 * math.pi * frequencies[positive].astype(np.float64)
    w1 = 2.0 * math.pi * params.f1
    w2 = 2.0 * math.pi * params.f2
    high_pass = 1.0 / (1.0 + w1 / (params.q1 * s) + (w1 / s) ** 2)
    low_pass = 1.0 / (1.0 + s / (params.q2 * w2) + (s / w2) ** 2)
    out[positive] = np.asarray(high_pass * low_pass, dtype=np.complex128)
    return out


def _zero_state_filter(
    record: NDArray[np.float64], fs: float, name: str, *, band_limiting: bool
) -> NDArray[np.float64]:
    """Apply a response to a record with the filter starting at rest.

    The record is padded with its own length in zeros before the frequency
    domain multiplication and the padding is dropped afterwards, so the tail
    of the response lands in the padding instead of wrapping onto the front of
    the record. That is the second of the three conventions the module
    docstring names: the printed tables come from a simulation switched on at
    ``t = 0``, and the circular multiplication of
    :func:`~phonometry.vibration.apply_weighting` erases the switch-on
    transient the linear MTVV of the continuous row is built to catch.
    """
    from scipy import fft as sp_fft

    n = record.size
    nfft = int(sp_fft.next_fast_len(2 * n))
    frequencies = np.fft.rfftfreq(nfft, d=1.0 / fs).astype(np.float64)
    if band_limiting:
        response = _band_limiting_response(name, frequencies)
    else:
        response = np.asarray(
            frequency_weighting(name, frequencies).response, dtype=np.complex128
        )
    weighted = np.fft.irfft(np.fft.rfft(record, n=nfft) * response, n=nfft)
    return np.asarray(weighted[:n], dtype=np.float64)


def signal_burst_indications(
    application: str,
    name: str,
    cycles: int | None,
    *,
    fs: float | None = None,
) -> dict[str, float]:
    """What a conforming meter indicates for one row of Tables 7 to 9.

    Runs the library chain the standard describes: the burst of
    :func:`sawtooth_burst`, the weighting (or the band-limiting response) of
    ISO 8041-1 Table 3 applied from rest, and then the indication quantities
    the table for that application prints, over the whole measurement
    duration. The MTVV columns are the maximum of the running r.m.s. of
    ISO 2631-1 Eq. (4) with the 1 s integration time this clause implies, in
    the linear and the exponential average of Annex D.

    :param application: One of the keys of :data:`SAWTOOTH_BURST_TESTS`.
    :param name: A weighting of that application, or :data:`BAND_LIMITING` for
        the band-limiting row.
    :param cycles: Saw-tooth cycles per burst (1, 2, 4, 8 or 16), or ``None``
        for the continuous row.
    :param fs: Sampling frequency, in hertz. Finite, positive, and above twice
        the upper band-limiting corner of the weighting under test, below
        which the pass band is not represented and the indications would be an
        artefact of the sampling. ``None`` takes the recommended rate of the
        application.
    :return: The indications for a 1 m/s2 amplitude burst, keyed by the
        printed column names of that application's table (``"rms"``,
        ``"vdv"``, ``"mtvv_linear"``, ``"mtvv_exponential"``, ``"msdv"``), in
        the units of each quantity.
    :raises ValueError: As for :func:`sawtooth_burst`, and if the weighting
        belongs to another application.
    :raises TypeError: If ``cycles`` is neither an integer nor ``None``.
    """
    test = _require_application(application)
    row = _require_row(test, name)
    burst_cycles = _require_cycles(test, cycles)
    rate = _require_sampling_rate(test, fs)

    record = sawtooth_burst(test.application, burst_cycles, fs=rate)
    weighting = test.band_limiting_weighting if row == BAND_LIMITING else row
    weighted = _zero_state_filter(
        record, rate, weighting, band_limiting=row == BAND_LIMITING
    )

    printed = SIGNAL_BURST_RESPONSE[test.application, row, burst_cycles]
    indications: dict[str, float] = {}
    for quantity in printed:
        if quantity == "rms":
            indications[quantity] = float(np.sqrt(np.mean(weighted**2)))
        elif quantity == "vdv":
            indications[quantity] = vibration_dose_value(weighted, rate)
        elif quantity == "msdv":
            indications[quantity] = motion_sickness_dose_value(weighted, rate)
        else:
            # MTVV is the maximum of the running r.m.s. (ISO 2631-1 Eq. (4)),
            # and Table 8 prints it under both averagings, so the column
            # selects the method rather than the function: one definition of
            # MTVV in the library, and this table inherits any change to it.
            method = "linear" if quantity == "mtvv_linear" else "exponential"
            indications[quantity] = mtvv(
                weighted,
                rate,
                integration_time=_MTVV_INTEGRATION_TIME_S,
                method=method,
            )
    return indications


@dataclass(frozen=True)
class SignalBurstVerification:
    """A meter's signal-burst indications against ISO 8041-1 Tables 7 to 9.

    :ivar application: The application whose table was used.
    :ivar weighting: The row that was graded, a weighting name or
        :data:`BAND_LIMITING`.
    :ivar amplitude_m_s2: The zero-to-peak amplitude of the test signal the
        printed responses were scaled by.
    :ivar cycle_counts: The burst lengths that were graded, in printed order,
        with ``None`` for the continuous row.
    :ivar quantities: The columns that were graded, in printed order.
    :ivar measured: The indications as supplied, one row per burst length and
        one column per quantity.
    :ivar printed: The Table 7, 8 or 9 cells they are judged against, scaled
        by ``amplitude_m_s2``.
    :ivar deviation_percent: ``(measured / printed - 1) * 100``, elementwise.
    :ivar tolerance_percent: The printed tolerance of each column, from
        :data:`BURST_TOLERANCE_PERCENT`.
    :ivar within_tolerance: Whether each cell is inside its tolerance.
    """

    application: str
    weighting: str
    amplitude_m_s2: float
    cycle_counts: tuple[int | None, ...]
    quantities: tuple[str, ...]
    measured: NDArray[np.float64]
    printed: NDArray[np.float64]
    deviation_percent: NDArray[np.float64]
    tolerance_percent: NDArray[np.float64]
    within_tolerance: NDArray[np.bool_]

    @property
    def passes(self) -> bool:
        """Whether every graded cell is inside its printed tolerance.

        True says the time response of this weighting chain matches the
        printed table. Clause 5.9 is one of the clauses a meter is graded on,
        and the others are hardware measurements this cannot stand in for.
        """
        return bool(np.all(self.within_tolerance))

    @property
    def worst_deviation_percent(self) -> float:
        """The largest deviation in magnitude, signed as it was measured."""
        if self.deviation_percent.size == 0:
            return 0.0
        flat = self.deviation_percent.reshape(-1)
        return float(flat[int(np.argmax(np.abs(flat)))])

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the deviations against the printed tolerance band.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the marker series.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_signal_burst_verification

        check_language(language)
        return plot_signal_burst_verification(self, ax, language=language, **kwargs)


def verify_signal_burst_response(
    application: str,
    name: str,
    measured: Mapping[int | None, Mapping[str, float]],
    *,
    amplitude_m_s2: float = 1.0,
) -> SignalBurstVerification:
    """Check measured burst indications against ISO 8041-1 Tables 7 to 9.

    The acceptance test of 12.13 (folio 36): "The vibration values indicated
    in response to the signal bursts, relative to the values of the vibration
    amplitude of the input signal, shall be as specified in Table 7, 8 or 9",
    within the tolerance printed beside each column.

    5.9 (folio 16) says the printed responses "are relative to a 1 m/s2
    amplitude signal and shall be multiplied by the amplitude of the actual
    test signal", and every one of the five quantities is homogeneous of
    degree one in the signal, so ``amplitude_m_s2`` scales the printed side
    exactly.

    :param application: One of the keys of :data:`SAWTOOTH_BURST_TESTS`.
    :param name: A weighting of that application, or :data:`BAND_LIMITING`.
    :param measured: The indications, keyed by burst length (``None`` for the
        continuous row) and then by printed column name. Every row has to
        report the same columns, so that the verdict is a rectangle rather
        than a ragged set.
    :param amplitude_m_s2: The zero-to-peak amplitude of the test signal, in
        m/s2.
    :return: The verdict, as a :class:`SignalBurstVerification`.
    :raises ValueError: If the application, the weighting or a burst length is
        not one this clause defines, if a column is not printed for that
        application, if the rows disagree about which columns they report, if
        ``measured`` is empty, if an indication is negative or not finite, or
        if the amplitude is not finite and positive.
    :raises TypeError: If a burst length is neither an integer nor ``None``.
    """
    test = _require_application(application)
    row = _require_row(test, name)
    amplitude = float(amplitude_m_s2)
    if not math.isfinite(amplitude) or amplitude <= 0.0:
        msg = "'amplitude_m_s2' must be positive and finite."
        raise ValueError(msg)
    if not measured:
        msg = "'measured' must report at least one burst length."
        raise ValueError(msg)

    for cycles in measured:
        _require_cycles(test, cycles)
    cycle_counts = tuple(
        cycles for cycles in (*test.cycle_counts, None) if cycles in measured
    )
    printed_columns = tuple(SIGNAL_BURST_RESPONSE[test.application, row, None])
    first = cycle_counts[0]
    quantities = tuple(
        quantity for quantity in printed_columns if quantity in measured[first]
    )
    for cycles in cycle_counts:
        reported = tuple(measured[cycles])
        unknown = [column for column in reported if column not in printed_columns]
        if unknown:
            msg = (
                f"'measured' carries {unknown} for {cycles} cycles, which the "
                f"{test.application} table does not print; it prints "
                f"{printed_columns}."
            )
            raise ValueError(msg)
        if set(reported) != set(quantities):
            msg = (
                f"'measured' reports {sorted(reported)} for {cycles} cycles "
                f"and {sorted(quantities)} for {first}; every burst length has "
                "to report the same columns."
            )
            raise ValueError(msg)
    if not quantities:
        msg = (
            f"'measured' reports no column of the {test.application} table; "
            f"it prints {printed_columns}."
        )
        raise ValueError(msg)

    values = np.array(
        [[float(measured[cycles][q]) for q in quantities] for cycles in cycle_counts],
        dtype=np.float64,
    )
    if not np.all(np.isfinite(values) & (values >= 0.0)):
        # Every printed column is a magnitude: an r.m.s. value, a dose value
        # or a maximum of a running r.m.s. A negative indication is not a
        # failing meter, it is a misread column.
        msg = "'measured' must be non-negative and finite."
        raise ValueError(msg)
    printed = amplitude * np.array(
        [
            [
                SIGNAL_BURST_RESPONSE[test.application, row, cycles][q]
                for q in quantities
            ]
            for cycles in cycle_counts
        ],
        dtype=np.float64,
    )
    tolerance = np.array(
        [BURST_TOLERANCE_PERCENT[q] for q in quantities], dtype=np.float64
    )
    deviation = (values / printed - 1.0) * 100.0
    within = np.abs(deviation) <= tolerance[np.newaxis, :]
    return SignalBurstVerification(
        application=test.application,
        weighting=row,
        amplitude_m_s2=amplitude,
        cycle_counts=cycle_counts,
        quantities=quantities,
        measured=values,
        printed=printed,
        deviation_percent=deviation,
        tolerance_percent=tolerance,
        within_tolerance=np.asarray(within, dtype=np.bool_),
    )
