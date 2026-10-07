#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The simulated programme signal of IEC 60268-1:1985, Clause 7.

A loudspeaker, an amplifier or a headphone is rated with one tone at a time,
but it is used with programme: speech and music, whose power is spread over
the whole audio band and concentrated in its middle. IEC 60268-1:1985 Clause 7
defines a noise that stands in for that programme in a measurement, the
**simulated programme signal**:

    A signal, whose mean power spectral density closely resembles the average
    of the mean power spectral densities of a wide range of programme
    material, including both speech and music of several kinds, is stationary
    weighted Gaussian noise without amplitude limiting, the weighted power
    spectrum being in accordance with Table II and Figure 1, page 22, when
    measured with third-octave filters in accordance with IEC Publication 225.

Table II gives the relative level of each one-third-octave band from 20 Hz to
20 kHz with its tolerance: 0 dB from 250 Hz to 800 Hz, falling to
:math:`-13{,}5` dB at 20 Hz and :math:`-21{,}6` dB at 20 kHz
(:data:`SIMULATED_PROGRAMME_SPECTRUM`). The Note under the clause adds that the
power of the whole signal is about 12,5 dB above the 0 dB of one band, which is
the power sum of the 31 relative levels, 12,56 dB.

The filter of Figure 2
----------------------

"Such a signal may be obtained from a pink-noise source by means of the filter
circuit shown in Figure 2." The circuit is a passive ladder of five
capacitors driven from the e.m.f. of the pink-noise source through 430 ohm,
which includes the source's own output impedance:

* a series 2,2 µF capacitor into a node shunted by 3,3 kohm and 91 nF;
* a series 330 ohm and 2,2 µF into a node shunted by 3,3 kohm and 68 nF;
* a series 0,47 µF into the 10 kohm output resistor, loaded by at least
  100 kohm; "the effect of the load impedance may be taken into account by
  adjusting the value of the 10 kohm resistor", so the 10 kohm is the whole
  shunt the network sees.

:func:`programme_signal_filter` is the exact transfer function of that ladder,
the voltage across the 10 kohm over the source e.m.f., from its nodal
equations. The two 2,2 µF capacitors with the resistors behind them make the
low-frequency roll-off and the 91 nF and 68 nF shunts the high-frequency one;
the passband loss is about 4 dB. Pink noise has equal power in every
one-third-octave band, so the band levels of its output are the power average
of :math:`|H|^2` over each band, and in ideal one-third-octave bands they fall
inside every tolerance of Table II once the level is set: the worst band is
the 5 kHz one, 1,1 dB below its printed level against a tolerance of 1 dB
when the 0 dB of the table is put on the 630 Hz band, and 0,18 dB inside it
with the level that centres the whole curve in the tolerances. Figure 2 is a
realisation within tolerance, not the definition: the definition is Table II.

The generator
-------------

:func:`simulated_programme_signal` synthesises the signal in the frequency
domain: a white Gaussian spectrum, shaped and transformed back to a record
that is stationary and Gaussian, as the clause asks, at any sample rate and
with no bilinear warping near the Nyquist frequency. It offers two shapes.
The default puts every band on Table II itself: a power spectral density that
is a straight line in decibels against the logarithm of frequency between the
band centres, whose nodes are set so that the power of each band, integrated
over it in closed form, is the printed level, and which carries on at the
slope of its end segments below 20 Hz and above 20 kHz. Every band then keeps
its whole tolerance for the fluctuation of a finite record. The other is the
circuit of Figure 2, pink noise of slope :math:`f^{-1/2}` in amplitude
multiplied by the complex response of the ladder; at 0,18 dB from its nearest
limit it leaves a short record little room, and a 20 s record at 48 kHz falls
outside the tolerance of the 31,5 Hz or 40 Hz band for some seeds.

The clause asks for the noise "without amplitude limiting". IEC 60268-7:2010
8.3.2 asks for the opposite when it rates the long-term maximum source e.m.f.
of a headphone: the programme signal "with additional clipping", with "a
peak-to-r.m.s ratio between 1,8 and 2,2". ``peak_to_rms`` clips the record at
the level that gives the requested ratio after clipping and rescales it.
Clipping spreads power into the weak upper bands: at a ratio of 2,0 it lifts
the 20 kHz band by about half a decibel against the middle of the spectrum,
inside its tolerance of 3 dB.

The verdict
-----------

:func:`check_programme_signal` judges one-third-octave band levels against
Table II. The table is a relative spectrum: its 0 dB is not a level the signal
has to reach, it is where the bands are referred to. The check therefore looks
for the level that places every band inside its tolerance. Each band allows a
window of levels, :math:`[T_i - t_i^- - L_i,\ T_i + t_i^+ - L_i]`, and the
spectrum conforms when the windows overlap; the level reported is the middle
of the overlap, where the smallest margin is largest. Bands that are not
given are not judged, so a record sampled at 44,1 kHz, which cannot hold the
20 kHz band, is judged on the other 30.

Neither amendment of 1988 touches Clause 7: Amendment 1 replaces Table AII,
the tone-burst response of the quasi-peak meter of Appendix A, and
Amendment 2 replaces 12.1, the three coils that make a uniform magnetic field.
"""

from __future__ import annotations

import functools
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from .._internal.frozen import read_only
from .._internal.validation import require_count, require_positive

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "SIMULATED_PROGRAMME_SPECTRUM",
    "ProgrammeSignalCheck",
    "ProgrammeSpectrumBand",
    "check_programme_signal",
    "programme_signal_filter",
    "simulated_programme_signal",
]


@dataclass(frozen=True)
class ProgrammeSpectrumBand:
    """One row of IEC 60268-1:1985 Table II.

    :ivar relative_level_db: The relative level of the one-third-octave band,
        in dB.
    :ivar tolerance_plus_db: The upper tolerance, in dB, as printed (a
        positive number).
    :ivar tolerance_minus_db: The lower tolerance, in dB, as printed (a
        positive number).
    """

    relative_level_db: float
    tolerance_plus_db: float
    tolerance_minus_db: float


#: IEC 60268-1:1985 Table II, "Power spectrum of simulated programme signal"
#: (PDF page 23, printed page 21), keyed by the nominal one-third-octave
#: frequency in hertz. The + and - tolerances are printed in separate columns
#: and are equal in every row.
SIMULATED_PROGRAMME_SPECTRUM: Mapping[float, ProgrammeSpectrumBand] = MappingProxyType(
    {
        frequency: ProgrammeSpectrumBand(level, tolerance, tolerance)
        for frequency, level, tolerance in (
            (20.0, -13.5, 3.0),
            (25.0, -10.2, 2.0),
            (31.5, -7.4, 1.0),
            (40.0, -5.2, 1.0),
            (50.0, -3.5, 1.0),
            (63.0, -2.3, 1.0),
            (80.0, -1.4, 1.0),
            (100.0, -0.9, 0.8),
            (125.0, -0.5, 0.6),
            (160.0, -0.2, 0.5),
            (200.0, -0.1, 0.5),
            (250.0, 0.0, 0.5),
            (315.0, 0.0, 0.5),
            (400.0, 0.0, 0.5),
            (500.0, 0.0, 0.5),
            (630.0, 0.0, 0.5),
            (800.0, 0.0, 0.5),
            (1000.0, -0.1, 0.6),
            (1250.0, -0.3, 0.7),
            (1600.0, -0.6, 0.8),
            (2000.0, -1.0, 1.0),
            (2500.0, -1.6, 1.0),
            (3150.0, -2.5, 1.0),
            (4000.0, -3.7, 1.0),
            (5000.0, -5.1, 1.0),
            (6300.0, -7.0, 1.0),
            (8000.0, -9.4, 1.0),
            (10000.0, -11.9, 1.0),
            (12500.0, -14.8, 1.5),
            (16000.0, -18.2, 2.0),
            (20000.0, -21.6, 3.0),
        )
    }
)

#: The component values of IEC 60268-1:1985 Figure 2 (PDF page 24, printed
#: page 22), in ohms and farads, in the order the signal meets them.
_R_SOURCE_OHM = 430.0
_C_FIRST_F = 2.2e-6
_R_FIRST_SHUNT_OHM = 3300.0
_C_FIRST_SHUNT_F = 91e-9
_R_SECOND_SERIES_OHM = 330.0
_C_SECOND_F = 2.2e-6
_R_SECOND_SHUNT_OHM = 3300.0
_C_SECOND_SHUNT_F = 68e-9
_C_OUTPUT_F = 0.47e-6
_R_OUTPUT_OHM = 10e3

#: How far an exact band-centre frequency may sit from its nominal label, as
#: a ratio, and still be read as that band: half a one-twelfth octave, which
#: no neighbouring one-third-octave centre comes near.
_BAND_MATCH_RATIO = 2.0 ** (1.0 / 24.0)

#: The fewest bands the tolerance check judges: one band fits any level.
_MIN_BANDS = 2

#: The fewest samples the generator synthesises.
_MIN_SAMPLES = 16

#: How close to the smallest margin a band has to be to count as binding, in
#: dB: far below any printed digit, far above the rounding of the arithmetic.
_BINDING_SLACK_DB = 1e-9

#: Slack on a tolerance limit, in dB: a band printed exactly on its limit is
#: inside it, whatever the last bits of the level arithmetic make of it.
_LIMIT_SLACK_DB = 1e-9


def programme_signal_filter(frequencies_hz: ArrayLike) -> NDArray[np.complex128]:
    r"""The transfer function of the filter of IEC 60268-1:1985 Figure 2.

    The voltage across the 10 kohm output resistor over the e.m.f. of the
    pink-noise source, from the nodal equations of the ladder (see the module
    docstring for the circuit). The source's output impedance is part of the
    first 430 ohm and the 10 kohm is the whole output shunt, the two
    conventions the figure's notes state.

    :param frequencies_hz: Frequencies, in Hz, any shape; each must be
        positive.
    :return: The complex response, dimensionless, with the shape of
        ``frequencies_hz``.
    :raises ValueError: If a frequency is not a positive finite number.
    """
    f = np.asarray(frequencies_hz, dtype=np.float64)
    if f.size and not (np.all(np.isfinite(f)) and np.all(f > 0.0)):
        msg = "'frequencies_hz' must hold positive, finite frequencies."
        raise ValueError(msg)
    s = 2j * np.pi * f
    z_first = _R_SOURCE_OHM + 1.0 / (s * _C_FIRST_F)
    z_second = _R_SECOND_SERIES_OHM + 1.0 / (s * _C_SECOND_F)
    z_output = 1.0 / (s * _C_OUTPUT_F)
    y_a = 1.0 / _R_FIRST_SHUNT_OHM + s * _C_FIRST_SHUNT_F
    y_b = 1.0 / _R_SECOND_SHUNT_OHM + s * _C_SECOND_SHUNT_F
    y_c = 1.0 / _R_OUTPUT_OHM
    # Nodal equations of the three nodes A, B, C, solved in closed form by
    # eliminating A and B: the output node sees node B through the series
    # capacitor, node B sees node A through the series RC, and node A is
    # driven through the first series RC from the e.m.f.
    g1 = 1.0 / z_first
    g2 = 1.0 / z_second
    g3 = 1.0 / z_output
    a11 = g1 + y_a + g2
    a22 = g2 + y_b + g3
    a33 = g3 + y_c
    # Solve [[a11, -g2, 0], [-g2, a22, -g3], [0, -g3, a33]] v = [g1, 0, 0].
    determinant = a11 * (a22 * a33 - g3 * g3) - g2 * g2 * a33
    response = g1 * g2 * g3 / determinant
    return np.asarray(response, dtype=np.complex128)


#: The decibel-to-exponent factor, :math:`\ln 10 / 10`.
_DB_TO_EXPONENT = math.log(10.0) / 10.0

#: Below this exponent the series value of :math:`(e^z - 1)/z` is used.
_SMALL_EXPONENT = 1e-12

#: The tolerance of the band-level fit of the ``"table"`` realisation, in dB,
#: and the iterations it is allowed.
_FIT_TOLERANCE_DB = 1e-10
_FIT_ITERATIONS = 100


def _relative_expm1(z: NDArray[np.float64]) -> NDArray[np.float64]:
    """:math:`(e^z - 1)/z`, which tends to 1 as :math:`z` tends to 0."""
    small = np.abs(z) < _SMALL_EXPONENT
    safe = np.where(small, 1.0, z)
    return np.asarray(np.where(small, 1.0, np.expm1(safe) / safe), dtype=np.float64)


def _band_levels_of_nodes(nodes_db: NDArray[np.float64]) -> NDArray[np.float64]:
    r"""The band levels of a density linear in dB between the band centres.

    The density, in dB per unit of :math:`\lg f`, runs straight between the
    nodes at the band centres, one-tenth of a decade apart, and on at the end
    segments' slopes. Each band spans half a segment either side of its node,
    so its mean power is the closed-form integral of an exponential over the
    two halves.
    """
    half = 0.05
    slopes = np.diff(nodes_db) / (2.0 * half)
    left = np.concatenate(([slopes[0]], slopes))
    right = np.concatenate((slopes, [slopes[-1]]))
    # Integral over [-h, 0] of e^{k m x} is h (1 - e^{-k m h})/(k m) and over
    # [0, h] it is h (e^{k m h} - 1)/(k m); the mean over the band divides by 2h.
    falling = np.exp(-_DB_TO_EXPONENT * left * half) * _relative_expm1(
        _DB_TO_EXPONENT * left * half
    )
    rising = _relative_expm1(_DB_TO_EXPONENT * right * half)
    return np.asarray(
        nodes_db + 10.0 * np.log10(0.5 * (falling + rising)), dtype=np.float64
    )


@functools.cache
def _table_nodes_db() -> tuple[float, ...]:
    """The node levels that put every band of Table II on its printed level."""
    target = np.array(
        [row.relative_level_db for row in SIMULATED_PROGRAMME_SPECTRUM.values()]
    )
    nodes = target.copy()
    for _ in range(_FIT_ITERATIONS):
        error = target - _band_levels_of_nodes(nodes)
        nodes += error
        if float(np.max(np.abs(error))) < _FIT_TOLERANCE_DB:
            break
    return tuple(float(value) for value in nodes)


def _table_density_db(frequencies_hz: NDArray[np.float64]) -> NDArray[np.float64]:
    """The ``"table"`` density at each frequency, in dB per unit of lg f."""
    nodes = np.asarray(_table_nodes_db())
    centres = np.arange(-17, 14) / 10.0 + 3.0  # lg of 1000 * 10^(n/10)
    u = np.log10(frequencies_hz)
    inner = np.interp(u, centres, nodes)
    low_slope = (nodes[1] - nodes[0]) / 0.1
    high_slope = (nodes[-1] - nodes[-2]) / 0.1
    below = nodes[0] + low_slope * (u - centres[0])
    above = nodes[-1] + high_slope * (u - centres[-1])
    return np.asarray(
        np.where(u < centres[0], below, np.where(u > centres[-1], above, inner)),
        dtype=np.float64,
    )


def simulated_programme_signal(
    fs: int,
    seconds: float,
    *,
    rms: float = 1.0,
    spectrum: Literal["table", "figure_2"] = "table",
    peak_to_rms: float | None = None,
    seed: int | None = None,
) -> NDArray[np.float64]:
    r"""The simulated programme signal of IEC 60268-1:1985 Clause 7.

    Stationary Gaussian noise whose one-third-octave spectrum follows Table II,
    synthesised in the frequency domain (see the module docstring). The record
    is zero-mean and scaled to ``rms`` exactly.

    Two realisations are offered. ``"table"`` (default) puts every band of
    Table II on its printed level: the power spectral density is linear in
    decibels against the logarithm of frequency between the band centres,
    continued at the slope of the end segments below 20 Hz and above 20 kHz,
    and its nodes are set so that each band's power, integrated over the band
    in closed form, is the printed level. Every band then has its whole
    tolerance for the random fluctuation of a finite record. ``"figure_2"`` is
    pink noise through the filter of Figure 2 (:func:`programme_signal_filter`),
    the circuit the clause offers: inside the tolerances, but only 0,18 dB
    inside at its worst band, so a short record can fall outside them.

    The clause asks for the noise "without amplitude limiting", and so does
    this by default. ``peak_to_rms`` clips it instead, for the limiting
    voltages of IEC 60268-7:2010 8.3.2, which drive a headphone with the
    programme signal "with additional clipping" and a peak-to-r.m.s. ratio
    between 1,8 and 2,2: the record is clipped symmetrically at the level that
    leaves exactly that ratio after clipping, then rescaled to ``rms``.

    A one-third-octave band at 20 Hz is 4,6 Hz wide, so its level fluctuates
    by about :math:`4{,}34/\sqrt{4{,}6\,T}` dB over a record of :math:`T`
    seconds: 0,4 dB in 30 s. Table II allows 3 dB there; the 0,5 dB bands of
    the middle need a few seconds.

    :param fs: Sample rate, in hertz.
    :param seconds: Duration, in seconds.
    :param rms: RMS value of the record, in whatever unit it is scaled to.
    :param spectrum: ``"table"`` (default) for the band levels of Table II,
        ``"figure_2"`` for pink noise through the filter of Figure 2.
    :param peak_to_rms: The ratio of the peak value to the RMS value after
        clipping, or ``None`` (default) for no clipping. It must be above 1
        and below the ratio the unclipped record already has.
    :param seed: Seed for :func:`numpy.random.default_rng`; the same seed
        reproduces the same record.
    :return: The signal, ``round(fs * seconds)`` samples.
    :raises ValueError: If an input is invalid, or ``peak_to_rms`` is not
        below the ratio of the unclipped record.
    """
    if spectrum not in {"table", "figure_2"}:
        msg = f"'spectrum' must be 'table' or 'figure_2'; got {spectrum!r}."
        raise ValueError(msg)
    rate = require_count(fs, "fs")
    duration = require_positive(float(seconds), "seconds")
    level = require_positive(float(rms), "rms")
    n = round(rate * duration)
    if n < _MIN_SAMPLES:
        msg = f"'fs'*'seconds' must give at least {_MIN_SAMPLES} samples, got {n}."
        raise ValueError(msg)
    rng = np.random.default_rng(seed)
    white = np.fft.rfft(rng.standard_normal(n))
    frequencies = np.fft.rfftfreq(n, d=1.0 / rate)
    shaping = np.zeros(frequencies.size, dtype=np.complex128)
    if spectrum == "table":
        shaping[1:] = np.sqrt(
            10.0 ** (_table_density_db(frequencies[1:]) / 10.0) / frequencies[1:]
        )
    else:
        shaping[1:] = programme_signal_filter(frequencies[1:]) / np.sqrt(
            frequencies[1:]
        )
    x = np.fft.irfft(white * shaping, n)
    x -= float(np.mean(x))
    x /= float(np.sqrt(np.mean(x * x)))
    if peak_to_rms is not None:
        x = _clip_to_ratio(x, require_positive(float(peak_to_rms), "peak_to_rms"))
    return np.asarray(x * level, dtype=np.float64)


def _clipped_ratio(x: NDArray[np.float64], threshold: float) -> float:
    """Peak-to-RMS ratio of ``x`` clipped symmetrically at ``threshold``."""
    clipped = np.clip(x, -threshold, threshold)
    return threshold / float(np.sqrt(np.mean(clipped * clipped)))


def _clip_to_ratio(x: NDArray[np.float64], ratio: float) -> NDArray[np.float64]:
    """Clip a unit-RMS record so that its peak-to-RMS ratio is ``ratio``.

    The ratio after clipping at a threshold :math:`c` is :math:`c` over the
    RMS of the clipped record, which rises monotonically from 1 (clipped to a
    square wave) to the ratio of the unclipped record, so the threshold is
    found by bisection on that bracket.
    """
    from scipy.optimize import brentq

    peak = float(np.max(np.abs(x)))
    unclipped = peak / float(np.sqrt(np.mean(x * x)))
    if not 1.0 < ratio < unclipped:
        msg = (
            f"'peak_to_rms' must lie between 1 and {unclipped:.3f}, the ratio "
            f"of the unclipped record; got {ratio:g}."
        )
        raise ValueError(msg)
    threshold = brentq(
        lambda c: _clipped_ratio(x, c) - ratio, peak * 1e-6, peak, xtol=1e-12
    )
    clipped = np.clip(x, -threshold, threshold)
    return np.asarray(clipped / np.sqrt(np.mean(clipped * clipped)), dtype=np.float64)


def _nominal_band(frequency: float) -> float:
    """The Table II frequency an exact or nominal band centre belongs to."""
    for nominal in SIMULATED_PROGRAMME_SPECTRUM:
        ratio = frequency / nominal
        if 1.0 / _BAND_MATCH_RATIO < ratio < _BAND_MATCH_RATIO:
            return nominal
    msg = (
        f"{frequency:g} Hz is not a one-third-octave band of IEC 60268-1 "
        "Table II (20 Hz to 20 kHz)."
    )
    raise ValueError(msg)


@dataclass(frozen=True)
class ProgrammeSignalCheck:
    r"""A one-third-octave spectrum judged against IEC 60268-1:1985 Table II.

    :ivar frequencies_hz: The nominal frequencies of the bands judged, in Hz,
        ascending.
    :ivar band_levels_db: The band levels as given, in dB, in the order of
        :attr:`frequencies_hz`.

    Table II's relative levels and tolerances at the bands, and the offset
    that refers the levels to them, are read from the table, so a check
    cannot be built against other tolerances.
    """

    frequencies_hz: NDArray[np.float64]
    band_levels_db: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Reject a band Table II does not print, or levels of another length.

        :raises ValueError: if a frequency is not a nominal band of Table II,
            or the levels do not hold one finite value per band.
        """
        for value in np.atleast_1d(self.frequencies_hz):
            if float(value) not in SIMULATED_PROGRAMME_SPECTRUM:
                msg = (
                    f"ProgrammeSignalCheck: {float(value):g} Hz is not a nominal "
                    "band of IEC 60268-1 Table II."
                )
                raise ValueError(msg)
        levels = np.asarray(self.band_levels_db, dtype=np.float64)
        if levels.shape != np.shape(self.frequencies_hz) or not np.all(
            np.isfinite(levels)
        ):
            msg = "ProgrammeSignalCheck: one finite band level per band."
            raise ValueError(msg)

    def _rows(self) -> list[ProgrammeSpectrumBand]:
        return [
            SIMULATED_PROGRAMME_SPECTRUM[float(value)]
            for value in np.atleast_1d(self.frequencies_hz)
        ]

    @property
    def relative_levels_db(self) -> NDArray[np.float64]:
        """Table II's relative levels at the bands, in dB."""
        return np.array([row.relative_level_db for row in self._rows()])

    @property
    def tolerance_plus_db(self) -> NDArray[np.float64]:
        """The upper tolerances of Table II at the bands, in dB."""
        return np.array([row.tolerance_plus_db for row in self._rows()])

    @property
    def tolerance_minus_db(self) -> NDArray[np.float64]:
        """The lower tolerances of Table II at the bands, in dB."""
        return np.array([row.tolerance_minus_db for row in self._rows()])

    @property
    def offset_db(self) -> float:
        """The level added to the band levels to refer them to Table II, in dB.

        The middle of the window of levels that keeps every band inside its
        tolerance, or, when no level does, the level that shares the worst
        excursion equally between the two sides.
        """
        table = self.relative_levels_db
        levels = np.asarray(self.band_levels_db, dtype=np.float64)
        lowest = float(np.max(table - self.tolerance_minus_db - levels))
        highest = float(np.min(table + self.tolerance_plus_db - levels))
        return 0.5 * (lowest + highest)

    @property
    def deviations_db(self) -> NDArray[np.float64]:
        """Each band's level, referred by :attr:`offset_db`, minus Table II, in dB."""
        return np.asarray(
            self.band_levels_db + self.offset_db - self.relative_levels_db,
            dtype=np.float64,
        )

    @property
    def margin_db(self) -> float:
        """The smallest distance of a band from its nearer limit, in dB.

        Negative when the spectrum cannot be placed inside the tolerances: its
        magnitude is then the excursion of the worst band.
        """
        deviation = self.deviations_db
        return float(
            np.min(
                np.minimum(
                    self.tolerance_plus_db - deviation,
                    self.tolerance_minus_db + deviation,
                )
            )
        )

    @property
    def binding_bands_hz(self) -> tuple[float, ...]:
        """The bands at the smallest margin, in Hz.

        The level is placed in the middle of the window every band allows, so
        the smallest margin is reached by at least two bands, one against its
        upper limit and one against its lower; those are the bands that fix
        the verdict.
        """
        deviation = self.deviations_db
        margins = np.minimum(
            self.tolerance_plus_db - deviation, self.tolerance_minus_db + deviation
        )
        binding = margins <= float(np.min(margins)) + _BINDING_SLACK_DB
        return tuple(float(value) for value in self.frequencies_hz[binding])

    @property
    def passes(self) -> bool:
        """Whether some level places every band inside its tolerance."""
        return self.margin_db >= -_LIMIT_SLACK_DB

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a ProgrammeSignalCheck has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the referred band levels inside the tolerances of Table II.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the band levels' ``Axes.plot``.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.headphones import plot_programme_signal_check

        check_language(language)
        return plot_programme_signal_check(self, ax, language=language, **kwargs)


def check_programme_signal(
    frequencies_hz: ArrayLike, band_levels_db: ArrayLike
) -> ProgrammeSignalCheck:
    r"""Is this one-third-octave spectrum the programme signal of IEC 60268-1?

    Clause 7 asks for a weighted power spectrum "in accordance with Table II
    and Figure 1 [...] when measured with third-octave filters". Table II is a
    relative spectrum, so the band levels are judged up to a constant: the
    spectrum conforms when one level places every band inside its tolerance
    (see the module docstring). Only the bands given are judged.

    The band levels can come from any one-third-octave analyser, for instance
    :func:`phonometry.filters.octave_filter` with ``fraction=3``, whose exact
    band centres (19,95 Hz, 25,12 Hz, ...) are read as the nominal ones of the
    table.

    :param frequencies_hz: Band centre frequencies, in Hz, nominal or exact,
        each a band of Table II (20 Hz to 20 kHz) and none repeated.
    :param band_levels_db: The band levels, in dB, on any reference.
    :return: A :class:`ProgrammeSignalCheck`.
    :raises ValueError: If the inputs differ in length, a frequency is not a
        band of Table II or appears twice, a level is not finite, or fewer than
        two bands are given.
    """
    f = np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64))
    levels = np.atleast_1d(np.asarray(band_levels_db, dtype=np.float64))
    if f.ndim != 1 or levels.shape != f.shape:
        msg = "'frequencies_hz' and 'band_levels_db' must be 1-D and of equal length."
        raise ValueError(msg)
    if f.size < _MIN_BANDS:
        msg = f"At least {_MIN_BANDS} bands are needed to judge a relative spectrum."
        raise ValueError(msg)
    if not np.all(np.isfinite(levels)):
        msg = "'band_levels_db' must be finite."
        raise ValueError(msg)
    if not (np.all(np.isfinite(f)) and np.all(f > 0.0)):
        msg = "'frequencies_hz' must hold positive, finite frequencies."
        raise ValueError(msg)
    nominal = np.array([_nominal_band(float(value)) for value in f])
    if np.unique(nominal).size != nominal.size:
        msg = "'frequencies_hz' names a band of Table II more than once."
        raise ValueError(msg)
    order = np.argsort(nominal)
    return ProgrammeSignalCheck(
        frequencies_hz=read_only(nominal[order]),
        band_levels_db=read_only(levels[order].copy()),
    )
