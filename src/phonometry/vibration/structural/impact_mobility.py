#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Mechanical mobility measured by impact excitation (ISO 7626-5:2019).

ISO 7626-5 measures the same frequency-response functions as ISO 7626-2, but
excites the structure with a hammer or another impactor that is not attached
to it. Each record holds one impact and the free decay it leaves behind, and
that shape is what the part is about: the force occupies a small fraction of
the record, so the noise around it matters (8.5.1); the response may not have
died away by the end of the record, so the spectrum leaks (8.3, 8.5.2); a
second impact inside the record cuts notches into the force spectrum (6.4);
and the averaging runs over impacts rather than over segments of one long
record (8.6). This module holds those pieces and reuses the FRF machinery of
:mod:`.mechanical_mobility` for the rest.

**Spectra.** The records are sampled at ``fs`` and transformed with the
discrete Fourier transform scaled by the sampling interval,
:math:`X(f_k) = \Delta t \sum_n x_n \mathrm{e}^{-j 2\pi k n / N}`, which for a transient
wholly inside the record samples its continuous Fourier transform (8.3). The
force energy spectral density is :math:`G_{FF} = 2 \lvert F(f) \rvert^2`, in
N²·s/Hz: the power spectral density of 3.3, :math:`2 \lvert F \rvert^2 / T`,
multiplied by the record length as 3.4 prescribes.

**Averaging (8.6).** Over :math:`n` impacts at one point the estimate is the
averaged cross-spectrum of response and force divided by the averaged
auto-spectrum of the force,

.. math::

   H = \frac{\sum_i X_i F_i^{*}}{\sum_i \lvert F_i \rvert^2}, \qquad
   \gamma^2 = \frac{\lvert \sum_i X_i F_i^{*} \rvert^2}
                   {\sum_i \lvert F_i \rvert^2 \sum_i \lvert X_i \rvert^2}

with the ordinary coherence :math:`\gamma^2` of 9.1 beside it. The FRF comes
out in the kind of the response channel (accelerance, mobility or dynamic
compliance) and is converted to mobility with :func:`.convert_frf`.

**Windows (8.5).** The *force window* has unity gain over the part of the
record that holds the force pulse and its filter response and sets the rest to
exactly zero (8.5.1). The *exponential window*
:math:`w(t) = \mathrm{e}^{-a t}` starts at unity and adds a known decay to the data
(8.3 a), 8.5.2). Applied to force and response alike, it replaces every pole
:math:`s_r` of the impulse response by :math:`s_r - a` (Annex A, Formula
(A.2)), so a mode appears more damped than it is, and Formula (A.3) takes the
added damping away again:

.. math::

   \zeta_r = \hat{\zeta}_r - \frac{a}{\omega_r}

with :math:`\hat\zeta_r` the damping ratio estimated from the windowed data and
:math:`\omega_r` the damped natural frequency in rad/s. The corrected mobility
is synthesized from the corrected modes, and for a lightly damped, well
separated mode the measured peak is multiplied by
:math:`\hat\zeta_r / \zeta_r`. Annex A leaves the damping estimator open;
:func:`single_mode_fit` is the one this library offers, a rational-fraction
fit of one mode over a band.

Formula (A.3) is the first-order form of the pole shift the annex states in
words. The synthesis here moves the pole itself, which is exact, and the
correction reports both: :attr:`ExponentialWindowCorrection.damping_ratio` is
(A.3) as printed and :attr:`ExponentialWindowCorrection.exact_damping_ratio`
is the damping of the shifted pole; they differ by about
:math:`(\hat\zeta_r^3 - \zeta_r^3)/2`.

**Records.** Every function that takes a record takes a bare array with its
sample rate, or a :class:`~phonometry.io.Signal`, which brings its own rate
(an explicit ``fs`` that disagrees is refused). A calibration factor the
Signal carries is deliberately not applied: the records of this part are
forces in newtons and motions in m/s², m/s or m, not pressures. The checks
hand the samples they judged back as bare arrays, in the unit they arrived
in.

**Checks.** Every record check returns a verdict object with ``passes``:
:func:`check_double_hit` (6.4), :func:`check_force_spectrum` (6.2, 6.3),
:func:`check_overload` (8.4), :func:`check_response_decay` (8.3, 8.5.2) and
:func:`check_coherence` (9.1); :func:`verify_channel_match` judges the
channel-to-channel match of the analyser (8.1). The operational calibration of
7.2 is the rigid-mass check of ISO 7626-2:2015, 7.5.2, which 7.2 calls
essentially the same procedure: :func:`.rigid_mass_calibration_check`.

The part prints no worked example, so the implementation is anchored in closed
form: a single-degree-of-freedom structure struck by a smooth pulse gives its
mobility back from the averaged estimate, and its damping and mobility back
after exponential windowing and the Annex A correction.
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Iterable
from dataclasses import KW_ONLY, dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from ..._internal.frozen import OwnsArrays
from ..._internal.validation import (
    require_count,
    require_finite,
    require_non_negative,
    require_positive,
    require_ranks,
    require_real,
    require_same_length,
    require_scalar,
)
from ..._internal.warnings import PhonometryWarning
from ...io._resolve import SignalInput, resolve_fs, resolve_pair_fs, resolve_samples
from .mechanical_mobility import MobilityResult, convert_frf, random_error_percent

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

    from ..._report.metadata import ReportMetadata

#: Kind of motion the response channel measures, and the FRF it gives.
ResponseQuantity = Literal["acceleration", "velocity", "displacement"]

_FRF_OF_RESPONSE: dict[str, str] = {
    "acceleration": "accelerance",
    "velocity": "mobility",
    "displacement": "receptance",
}

#: The response should decay to about 1 % of its initial value at the end of
#: the record (ISO 7626-5:2019, 8.3 and 8.5.2), dimensionless. 8.3 calls the
#: figure a compromise: a longer record improves the frequency resolution but
#: can lower the signal-to-noise ratio, a shorter one truncates the response.
RESPONSE_END_RATIO = 0.01

#: The convenient check of 8.5.2: the peak response at the midpoint of the
#: record is about 10 % of the highest peak, dimensionless.
RESPONSE_MIDPOINT_RATIO = 0.1

#: With an exponential window, the response should decay naturally to 25 % or
#: less of its initial magnitude within the record, or the amplitude
#: corrections of Annex A become very sensitive to any error in the damping
#: estimates (8.5.2), dimensionless.
WINDOWED_RESPONSE_END_RATIO = 0.25

#: A coherence the clause calls high: "greater than 0,9" (9.1), dimensionless.
HIGH_COHERENCE = 0.9

#: Records a high coherence needs for high statistical confidence in its
#: estimate: "five to ten" (9.1). The lower end is the check's default.
COHERENCE_RECORDS = 5

#: Channel-to-channel magnitude match: unity within +/- 5 % (8.1),
#: dimensionless.
CHANNEL_MAGNITUDE_TOLERANCE = 0.05

#: Channel-to-channel phase match: zero within +/- 5 degrees (8.1).
CHANNEL_PHASE_TOLERANCE_DEG = 5.0

#: Samples a record needs for a spectrum to mean anything.
_MIN_SAMPLES = 16

#: A single-mode fit solves for five real coefficients from two equations per
#: frequency, so three frequencies is the least that determines it.
_MIN_FIT_FREQUENCIES = 3

#: Sanathanan-Koerner reweighting passes of the single-mode fit; the fit of an
#: exact single mode converges in one, and noisy data settle within a handful.
_FIT_ITERATIONS = 12

#: What the single-mode fit tells from zero, half the digits of a double. It
#: bounds how well the data determine the fit (the smallest singular value of
#: its least-squares system over the largest, columns of unit norm) and the
#: decay rate and damped natural frequency of the pole it finds, as
#: ``a1 = 2 sigma / omega_c`` and ``a0 - a1**2 / 4 = (omega_d / omega_c)**2``
#: against the centre ``omega_c`` of the band. Data that follow a line without
#: a resonance (a constant, a mass line, a spring line) determine no pole: the
#: one a solver returns for them is rounding, and its sign with it.
_FIT_TOLERANCE = math.sqrt(float(np.finfo(np.float64).eps))

#: The only rank a 2-D record array may have: one row per impact.
_RECORDS_RANK = 2

#: A fall across a range needs a highest and a lowest point.
_MIN_RANGE_FREQUENCIES = 2

#: The fewest impacts a record holds for there to be a secondary one.
_DOUBLE_HIT = 2

#: Where a force pulse ends for :func:`check_response_decay`: the first sample
#: after its peak at which the force has fallen back to this fraction of the
#: peak. This library's choice, low enough that the mass line a driving-point
#: acceleration carries during the impact is over, dimensionless.
_PULSE_END_RATIO = 0.01

#: The response-decay figures of 8.3 and 8.5.2 are printed as whole per
#: cents, and a reading is compared with them at that precision.
_PERCENT = 100.0


class ImpactExcitationWarning(PhonometryWarning):
    """Advisory when an ISO 7626-5 record breaks a rule of the part."""


# ---------------------------------------------------------------------------
# Spectra and windows.
# ---------------------------------------------------------------------------


def _record(value: SignalInput, name: str) -> NDArray[np.float64]:
    """One record, 1-D, finite, long enough for a spectrum."""
    # calibrate=False: a Signal may carry a digital-to-pascal factor, and
    # these records are forces in N and motions, not pressures. See
    # phonometry.io._resolve.
    record = np.asarray(
        resolve_samples(value, calibrate=False, name=name), dtype=np.float64
    )
    if record.ndim != 1:
        msg = f"'{name}' must be one record: a one-dimensional array."
        raise ValueError(msg)
    if record.size < _MIN_SAMPLES:
        msg = f"'{name}' must hold at least {_MIN_SAMPLES} samples."
        raise ValueError(msg)
    if not np.all(np.isfinite(record)):
        msg = f"'{name}' must be finite."
        raise ValueError(msg)
    return record


def _records(value: SignalInput, name: str) -> NDArray[np.float64]:
    """One record per row: a 1-D record becomes a single row.

    A Signal of several channels gives one row per channel.
    """
    # calibrate=False: as in _record, a force or a motion is not a pressure.
    records = np.asarray(
        resolve_samples(value, calibrate=False, name=name), dtype=np.float64
    )
    if records.ndim == 1:
        records = records[np.newaxis, :]
    if records.ndim != _RECORDS_RANK:
        msg = f"'{name}' must be one record or one record per row (1-D or 2-D)."
        raise ValueError(msg)
    if records.shape[0] < 1 or records.shape[1] < _MIN_SAMPLES:
        msg = f"'{name}' must hold at least one record of {_MIN_SAMPLES} samples."
        raise ValueError(msg)
    if not np.all(np.isfinite(records)):
        msg = f"'{name}' must be finite."
        raise ValueError(msg)
    return records


def _spectrum(
    records: NDArray[np.float64], fs: float
) -> tuple[NDArray[np.float64], NDArray[np.complex128]]:
    r"""Frequencies and :math:`\Delta t`-scaled one-sided DFT of each row."""
    n = records.shape[-1]
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    return freqs, np.fft.rfft(records, axis=-1) / fs


def _rounding_floor(records: NDArray[np.float64], fs: float) -> float:
    r"""What rounding leaves in a bin of :math:`\sum_r |F_r|^2`, in N²·s².

    A DFT of ``n`` samples rounds each bin through about ``log2(n)`` stages,
    each of which can err by one rounding of a double on the sum of the
    magnitudes it transforms. A force spectrum that vanishes in exact
    arithmetic, between two equal impacts for one, comes out at this level
    or below, and as an exact zero only for some record lengths.
    """
    n = records.shape[-1]
    rounding = max(math.log2(n), 1.0) * float(np.finfo(np.float64).eps)
    per_record = rounding * np.sum(np.abs(records), axis=-1) / fs
    return float(np.sum(per_record**2))


def _one_sided_factor(n_samples: int, n_bins: int) -> NDArray[np.float64]:
    """2 on every bin except DC (and Nyquist for an even record), which hold 1."""
    factor = np.full(n_bins, 2.0)
    factor[0] = 1.0
    if n_samples % 2 == 0:
        factor[-1] = 1.0
    return factor


def energy_spectral_density(
    record: SignalInput, fs: float | None = None
) -> tuple[np.ndarray, np.ndarray]:
    r"""One-sided energy spectral density of a transient record (3.3, 3.4).

    :math:`G = 2 \lvert X(f) \rvert^2`, with :math:`X(f)` the discrete Fourier
    transform scaled by the sampling interval: the power spectral density of
    3.3, :math:`2 \lvert X \rvert^2 / T`, multiplied by the record length
    :math:`T` as 3.4 prescribes for a transient wholly inside the record. For a
    force in newtons the unit is N²·s/Hz, the unit of Figures 3, 4, 5, 7 and 8.
    The DC bin and, for an even record, the Nyquist bin are not doubled.

    :param record: One record, 1-D. Accepts a :class:`phonometry.io.Signal`
        for its rate; a calibration factor it carries is not applied.
    :param fs: Sample rate, in Hz. Required for a bare array; a
        :class:`~phonometry.io.Signal` brings its own, and an explicit value
        that disagrees with it raises instead of silently winning.
    :return: ``(frequencies, esd)``: the DFT bin frequencies from 0 Hz to the
        Nyquist frequency, in hertz, and the density at each, in the record's
        unit squared times s/Hz.
    :raises ValueError: for a record that is not 1-D and finite, or a
        non-positive sample rate.
    """
    rate = require_positive(resolve_fs(record, fs, name="record"), "fs")
    x = _record(record, "record")
    freqs, spectrum = _spectrum(x[np.newaxis, :], rate)
    factor = _one_sided_factor(x.size, freqs.size)
    esd = factor * np.abs(spectrum[0]) ** 2
    return freqs, np.asarray(esd, dtype=np.float64)


def force_window(
    n_samples: int,
    fs: float,
    *,
    width_s: float,
    start_s: float = 0.0,
    taper_s: float = 0.0,
) -> np.ndarray:
    r"""The force window of 8.5.1: unity over the pulse, exactly zero elsewhere.

    The window has unity gain for the part of the record that holds the force
    signal, including the filter response, and sets the remaining samples to
    exactly zero before Fourier processing. It removes broad-band noise from
    the force auto-spectrum without distortion as long as none of the force
    data is attenuated (8.5.1, Figure 7). A rectangular window spreads periodic
    noise and DC offset over a wide band (Figure 8), and 8.5.1 notes that a
    smooth transition between zero and one narrows that spread: ``taper_s``
    adds a half-cosine ramp of that length on each side of the unity part,
    outside it, so the pulse itself is never attenuated. The shape of the ramp
    is this library's choice; the part does not prescribe one.

    Never use a force window to cut a second impact out of the record (6.4):
    the response still carries it. :func:`check_double_hit` finds one.

    :param n_samples: Record length ``N``, in samples.
    :param fs: Sample rate, in Hz.
    :param width_s: Length of the unity part, in seconds (> 0). Sample ``n`` is
        inside it when ``start_s <= n / fs < start_s + width_s``.
    :param start_s: Where the unity part begins, in seconds (Default: 0, the
        beginning of the record, which keeps the pre-trigger data of 8.2).
    :param taper_s: Length of each half-cosine ramp, in seconds (Default: 0, a
        rectangular window).
    :return: The window, one value per sample.
    :raises ValueError: for fewer than 16 samples, a non-positive sample rate
        or width, a negative start or taper, or a window, its falling ramp
        included, that is still open at the last sample of the record, at
        :math:`(N - 1)/f_s`.
    """
    n = _sample_count(n_samples)
    fs = require_positive(fs, "fs")
    width_s = require_positive(width_s, "width_s")
    start_s = require_non_negative(start_s, "start_s")
    taper_s = require_non_negative(taper_s, "taper_s")
    t = np.arange(n) / fs
    # The last sample sits at (N - 1)/fs, not at the record length N/fs: a
    # window still open there leaves no sample at zero after the pulse.
    last_s = (n - 1) / fs
    stop_s = start_s + width_s
    if stop_s + taper_s > last_s:
        msg = (
            f"the force window ends at {stop_s + taper_s:.12g} s, its falling "
            f"ramp included, and the last sample of the record is at "
            f"{last_s:.12g} s; a window still open at the last sample does not "
            "set the rest of the record to zero, and is no force window."
        )
        raise ValueError(msg)
    window = np.where((t >= start_s) & (t < stop_s), 1.0, 0.0)
    if taper_s > 0.0:
        rising = (t >= start_s - taper_s) & (t < start_s)
        falling = (t >= stop_s) & (t < stop_s + taper_s)
        window[rising] = 0.5 * (
            1.0 - np.cos(np.pi * (t[rising] - (start_s - taper_s)) / taper_s)
        )
        window[falling] = 0.5 * (1.0 + np.cos(np.pi * (t[falling] - stop_s) / taper_s))
    return np.asarray(window, dtype=np.float64)


def exponential_window(
    n_samples: int, fs: float, *, decay_rate_per_s: float
) -> np.ndarray:
    r"""The exponential window of 8.5.2: :math:`w(t) = \mathrm{e}^{-a t}`.

    The window has an initial value of unity at the start of the record and
    decreases exponentially towards its end, adding a known amount of
    artificial decay to the data (8.3 a), 8.5.2). Applied to force and response
    alike it moves every pole of the impulse response by ``-a`` (Annex A,
    Formula (A.2)); :func:`exponential_window_correction` takes the added
    damping away again.

    :param n_samples: Record length ``N``, in samples.
    :param fs: Sample rate, in Hz.
    :param decay_rate_per_s: Decay rate ``a``, in 1/s (>= 0; 0 is no window).
        :func:`exponential_decay_rate` finds the rate that ends the record at a
        stated value.
    :return: The window, one value per sample, :math:`\mathrm{e}^{-a n / f_s}`.
    :raises ValueError: for fewer than 16 samples, a non-positive sample rate
        or a negative decay rate.
    """
    n = _sample_count(n_samples)
    fs = require_positive(fs, "fs")
    a = require_non_negative(decay_rate_per_s, "decay_rate_per_s")
    return np.asarray(np.exp(-a * np.arange(n) / fs), dtype=np.float64)


def exponential_decay_rate(n_samples: int, fs: float, *, final_value: float) -> float:
    r"""The decay rate of an exponential window that ends the record at a value.

    8.5.2 describes an exponential window by the value it decays to at the end
    of the record: Figure 10 uses one that decays to 5 % of its initial value.
    The end of the record is its last sample, at :math:`(N-1)/f_s`, so
    :math:`a = -\ln(w_\mathrm{end}) f_s / (N - 1)` and
    ``exponential_window(n_samples, fs, decay_rate_per_s=a)[-1]`` is
    ``final_value``.

    :param n_samples: Record length ``N``, in samples.
    :param fs: Sample rate, in Hz.
    :param final_value: Window value at the last sample, in (0, 1]
        (dimensionless; 0.05 for the window of Figure 10).
    :return: The decay rate ``a``, in 1/s.
    :raises ValueError: for fewer than 16 samples, a non-positive sample rate
        or a final value outside (0, 1].
    """
    n = _sample_count(n_samples)
    fs = require_positive(fs, "fs")
    value = require_positive(final_value, "final_value")
    if value > 1.0:
        msg = "'final_value' must lie in (0, 1]: an exponential window only decays."
        raise ValueError(msg)
    return float(-math.log(value) * fs / (n - 1))


def _sample_count(n_samples: object) -> int:
    """A record length in samples: a whole number of at least 16."""
    if (
        isinstance(n_samples, bool)
        or not isinstance(n_samples, (int, np.integer))
        or int(n_samples) < _MIN_SAMPLES
    ):
        msg = f"'n_samples' must be a whole number of at least {_MIN_SAMPLES}."
        raise ValueError(msg)
    return int(n_samples)


# ---------------------------------------------------------------------------
# Double hits (6.4).
# ---------------------------------------------------------------------------


def _signed_force(force: NDArray[np.float64]) -> tuple[NDArray[np.float64], int]:
    """The force with the sign of its largest excursion made positive, and where that is.

    The sign of the largest excursion is taken as the sign of a compressive
    impact, so a force transducer wired either way reads the same.
    """
    loudest = int(np.argmax(np.abs(force)))
    sign = 1.0 if force[loudest] >= 0.0 else -1.0
    return np.asarray(sign * force, dtype=np.float64), loudest


def _impact_peaks(
    force: NDArray[np.float64], threshold_ratio: float
) -> NDArray[np.intp]:
    """Index of the peak of every excursion above the threshold, in time order.

    An impact is a run of samples, in the direction of the largest excursion,
    above ``threshold_ratio`` times that largest value; its peak is the
    largest sample of the run.
    """
    signed, loudest = _signed_force(force)
    peak = signed[loudest]
    if peak <= 0.0:
        return np.asarray([], dtype=np.intp)
    above = signed > threshold_ratio * peak
    edges = np.diff(above.astype(np.int8))
    starts = [int(i) + 1 for i in np.flatnonzero(edges == 1)]
    stops = [int(i) + 1 for i in np.flatnonzero(edges == -1)]
    if above[0]:
        starts.insert(0, 0)
    if above[-1]:
        stops.append(above.size)
    return np.asarray(
        [
            start + int(np.argmax(signed[start:stop]))
            for start, stop in zip(starts, stops, strict=True)
        ],
        dtype=np.intp,
    )


@dataclass(frozen=True)
class DoubleHitCheck(OwnsArrays):
    r"""Was there more than one impact in the force record? (ISO 7626-5, 6.4)

    If more than a single impact occurs within the record, the Fourier
    transforms of the pulses tend to cancel at certain frequencies and cut
    sharp notches into the force spectrum (Figure 5), where the low
    signal-to-noise ratio spoils the mobility. For two pulses of the same
    shape, the second :math:`r` times the first and :math:`\tau` later, the
    spectrum is the single pulse's times :math:`1 + r \mathrm{e}^{-j\omega\tau}`: it
    ripples with a period of :math:`1/\tau` in frequency between
    :math:`1 + r` and :math:`1 - r`, so the notches are deep only when the
    second impact is about as strong as the first. That is why 6.4 says a small
    second impact shows as a slight ripple, and why moderate dips "may normally
    be tolerated".

    :ivar force: The force record judged, in N, as a bare array (a
        :class:`~phonometry.io.Signal` passed in is read without its
        calibration factor, and its samples are what is kept).
    :ivar fs: Its sample rate, in Hz.
    :ivar impact_indices: Sample index of the peak of every impact found, in
        time order; the first entry is not necessarily the largest.
    :ivar threshold_ratio: The fraction of the largest peak an excursion had
        to exceed to count as an impact.
    """

    force: np.ndarray
    fs: float
    impact_indices: np.ndarray
    _: KW_ONLY
    threshold_ratio: float

    def __post_init__(self) -> None:
        """Reject a check whose impacts do not lie in its record.

        :raises ValueError: if the record is not 1-D, the sample rate is not
            positive, no impact is listed, or an index falls outside the record.
        """
        require_ranks(self, force=1, impact_indices=1)
        require_positive(self.fs, "fs")
        indices = np.asarray(self.impact_indices)
        if indices.size == 0:
            msg = "DoubleHitCheck: 'impact_indices' must list at least one impact."
            raise ValueError(msg)
        if np.any(indices < 0) or np.any(indices >= np.asarray(self.force).size):
            msg = "DoubleHitCheck: every impact index must lie inside the record."
            raise ValueError(msg)

    @property
    def times(self) -> np.ndarray:
        """Time of every sample of the record, in seconds."""
        return np.arange(np.asarray(self.force).size) / self.fs

    @property
    def impact_times_s(self) -> np.ndarray:
        """Time of the peak of every impact, in seconds."""
        return np.asarray(self.impact_indices, dtype=np.float64) / self.fs

    @property
    def impact_peaks(self) -> np.ndarray:
        """Force at the peak of every impact, in N."""
        force = np.asarray(self.force, dtype=np.float64)
        return np.asarray(force[np.asarray(self.impact_indices)], dtype=np.float64)

    @property
    def impacts(self) -> int:
        """How many impacts the record holds."""
        return int(np.asarray(self.impact_indices).size)

    def _primary(self) -> int:
        return int(np.argmax(np.abs(self.impact_peaks)))

    @property
    def secondary_ratio(self) -> float:
        """Largest secondary peak over the primary one (0 for a single impact)."""
        peaks = np.abs(self.impact_peaks)
        if peaks.size < _DOUBLE_HIT:
            return 0.0
        primary = self._primary()
        others = np.delete(peaks, primary)
        return float(np.max(others) / peaks[primary])

    @property
    def delay_s(self) -> float | None:
        """Time from the primary impact to the largest secondary one, in s.

        ``None`` for a single impact.
        """
        peaks = np.abs(self.impact_peaks)
        if peaks.size < _DOUBLE_HIT:
            return None
        primary = self._primary()
        times = self.impact_times_s
        order = [i for i in range(peaks.size) if i != primary]
        secondary = max(order, key=lambda i: peaks[i])
        return float(abs(times[secondary] - times[primary]))

    @property
    def notch_spacing_hz(self) -> float | None:
        r"""Spacing of the notches the two largest impacts cut, :math:`1/\tau`.

        ``None`` for a single impact.
        """
        delay = self.delay_s
        return None if delay is None else 1.0 / delay

    @property
    def ripple_db(self) -> float:
        r"""Peak-to-notch ripple of the force spectrum, in dB.

        :math:`20 \log_{10}[(1 + r)/(1 - r)]` for a secondary impact ``r``
        times the primary one, the same shape and the only other; 0 dB for a
        single impact and infinite for two equal ones, whose notches go to
        zero.
        """
        r = self.secondary_ratio
        if not math.isfinite(r) or r >= 1.0:
            return math.inf
        return float(20.0 * math.log10((1.0 + r) / (1.0 - r)))

    @property
    def passes(self) -> bool:
        """Whether the record holds a single impact."""
        return self.impacts == 1

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a DoubleHitCheck has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes | np.ndarray:
        """Plot the force record with its impacts, and its energy spectral density.

        With no ``ax`` a two-panel figure is drawn: the time history with every
        impact marked, and the energy spectral density with the notches the two
        largest impacts cut (Figure 5). With ``ax`` only the time history is
        drawn on it.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the force curve.
        :return: The axes, or the two-axes array.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_double_hit_check

        return plot_double_hit_check(
            self, ax=ax, language=check_language(language), **kwargs
        )


def check_double_hit(
    force: SignalInput, fs: float | None = None, *, threshold_ratio: float = 0.1
) -> DoubleHitCheck:
    r"""Does the force record hold one impact, or a double hit? (6.4)

    An impact is a run of samples whose force exceeds ``threshold_ratio``
    times the largest force in the record, in the direction of that largest
    force; the check passes when there is exactly one. Run it on the
    unwindowed, and preferably unfiltered, force: 6.4 recommends watching the
    unfiltered signal so the anti-aliasing filter does not hide a secondary
    impact in the ringing of the primary one, and forbids using a force window
    to remove one.

    The threshold is this library's, not the part's, which only says that a
    small second impact shows as a slight ripple and that moderate dips may be
    tolerated. At the default of 0,1 an undetected second pulse of the same
    shape as the first ripples the force spectrum by at most
    :math:`20 \log_{10}(1{,}1/0{,}9) = 1{,}74` dB peak to notch
    (:attr:`DoubleHitCheck.ripple_db`). A softer, longer rebound, the usual
    hammer bounce, carries more of the low-frequency spectrum than its peak
    says: it can stay under the threshold and still ripple the spectrum by
    several decibels. That is why 6.4 finds multiple impacts most easily in
    the frequency domain, which :func:`check_force_spectrum` reads.

    A filtered record has a limit of its own. When the spectrum of the pulse
    reaches the cut-off of the anti-aliasing filter, the ringing the filter
    leaves after the pulse can itself rise above the threshold, most of all
    with a steep elliptic or Chebyshev filter, and a single impact then reads
    as several. The unfiltered force avoids both effects.

    :param force: One force record, 1-D, in N. Accepts a
        :class:`phonometry.io.Signal` for its rate; a calibration factor it
        carries is deliberately not applied, because this record is a force
        in newtons and not a pressure.
    :param fs: Sample rate, in Hz. Required for a bare array; a
        :class:`~phonometry.io.Signal` brings its own, and an explicit value
        that disagrees with it raises instead of silently winning.
    :param threshold_ratio: Fraction of the largest force an excursion must
        exceed to count as an impact, in (0, 1) (Default: 0.1).
    :return: A :class:`DoubleHitCheck`.
    :raises ValueError: for a record that is not 1-D and finite, a
        non-positive sample rate, a threshold outside (0, 1), or a record with
        no force in it.
    """
    rate = require_positive(resolve_fs(force, fs, name="force"), "fs")
    record = _record(force, "force")
    threshold = require_positive(threshold_ratio, "threshold_ratio")
    if threshold >= 1.0:
        msg = "'threshold_ratio' must lie in (0, 1)."
        raise ValueError(msg)
    peaks = _impact_peaks(record, threshold)
    if peaks.size == 0:
        msg = "'force' holds no force: every sample is zero."
        raise ValueError(msg)
    return DoubleHitCheck(
        force=record,
        fs=rate,
        impact_indices=peaks,
        threshold_ratio=threshold,
    )


# ---------------------------------------------------------------------------
# The averaged estimate (8.6).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ImpactMobilityResult(OwnsArrays):
    r"""Mobility averaged over impacts at one point (ISO 7626-5:2019, 8.6).

    :ivar frequencies: DFT bin frequencies above 0 Hz, in hertz: up to the
        Nyquist frequency, or across the frequency range of interest the
        estimate was kept to (3.2).
    :ivar mobility: Complex mobility ``Y`` per frequency, in m/(N·s): the
        averaged estimate of 8.6 as measured, exponential window included. Its
        resonance peaks are therefore lower than the structure's when a window
        was used; :meth:`fit_mode` and the correction of Annex A restore them.
    :ivar coherence: Ordinary coherence :math:`\gamma^2` per frequency (9.1);
        identically 1 for a single impact.
    :ivar force_energy_spectral_density: Averaged one-sided energy spectral
        density of the windowed force, :math:`G_{FF}` in N²·s/Hz (3.4).
    :ivar impacts: Number of impacts averaged.
    :ivar exponential_decay_rate_per_s: Decay rate ``a`` of the exponential
        window applied, in 1/s (0 for none).
    :ivar response_quantity: What the response channel measured:
        ``"acceleration"``, ``"velocity"`` or ``"displacement"``.
    :ivar driving_point: ``True`` if force and response are co-located.
    """

    frequencies: np.ndarray
    mobility: np.ndarray
    coherence: np.ndarray
    force_energy_spectral_density: np.ndarray
    _: KW_ONLY
    impacts: int
    exponential_decay_rate_per_s: float = 0.0
    response_quantity: ResponseQuantity = "acceleration"
    driving_point: bool = True

    def __post_init__(self) -> None:
        """Reject an estimate whose curves do not share one frequency axis.

        :raises ValueError: if the four curves differ in rank or length, a
            frequency is not positive and finite, the mobility is not finite, a
            coherence lies outside [0, 1], fewer than one impact is recorded, the
            decay rate is negative, or the response quantity is unknown.
        """
        require_ranks(
            self,
            frequencies=1,
            mobility=1,
            coherence=1,
            force_energy_spectral_density=1,
        )
        require_same_length(
            self,
            "frequencies",
            "mobility",
            "coherence",
            "force_energy_spectral_density",
            axis="frequency",
        )
        owner = type(self).__name__
        freqs = np.asarray(self.frequencies, dtype=np.float64)
        if freqs.size == 0 or not np.all(np.isfinite(freqs)) or np.any(freqs <= 0.0):
            msg = f"{owner}: 'frequencies' must be positive and finite."
            raise ValueError(msg)
        if not np.all(np.isfinite(np.asarray(self.mobility))):
            msg = f"{owner}: 'mobility' must be finite."
            raise ValueError(msg)
        coherence = np.asarray(self.coherence, dtype=np.float64)
        if np.any(~(coherence >= 0.0)) or np.any(coherence > 1.0):
            msg = f"{owner}: 'coherence' must lie in [0, 1]."
            raise ValueError(msg)
        require_scalar(self.impacts, "impacts")
        if isinstance(self.impacts, bool) or int(self.impacts) < 1:
            msg = f"{owner}: 'impacts' must be at least 1."
            raise ValueError(msg)
        require_non_negative(
            self.exponential_decay_rate_per_s, "exponential_decay_rate_per_s"
        )
        if self.response_quantity not in _FRF_OF_RESPONSE:
            msg = (
                f"{owner}: 'response_quantity' must be one of "
                f"{tuple(_FRF_OF_RESPONSE)}; got {self.response_quantity!r}."
            )
            raise ValueError(msg)

    @property
    def magnitude(self) -> np.ndarray:
        """Mobility magnitude ``|Y|``, in m/(N·s)."""
        return np.asarray(np.abs(self.mobility), dtype=np.float64)

    @property
    def phase(self) -> np.ndarray:
        """Mobility phase, in radians."""
        return np.asarray(np.angle(self.mobility), dtype=np.float64)

    @property
    def measured_frf(self) -> str:
        """The FRF kind the response channel gives: accelerance, mobility or receptance."""
        return _FRF_OF_RESPONSE[self.response_quantity]

    def to(self, target: str) -> np.ndarray:
        """Convert the mobility to another FRF kind (see :func:`.convert_frf`)."""
        return convert_frf(self.mobility, self.frequencies, "mobility", target)

    @property
    def mobility_result(self) -> MobilityResult:
        """The estimate as a :class:`.MobilityResult` (ISO 7626-1 vocabulary)."""
        return MobilityResult(
            frequencies=np.asarray(self.frequencies, dtype=np.float64),
            mobility=np.asarray(self.mobility, dtype=np.complex128),
            driving_point=self.driving_point,
        )

    def fit_mode(self, band_hz: tuple[float, float]) -> SingleModeFitResult:
        """Fit the mode in a band, knowing the window this estimate carries.

        The fit runs on the FRF kind the response channel measured, because
        that is the record the exponential window multiplied, and the result
        carries the window's decay rate so that
        :attr:`SingleModeFitResult.correction` applies Annex A.

        :param band_hz: ``(f_low, f_high)`` around one resonance, in hertz.
        :return: A :class:`SingleModeFitResult`.
        """
        return single_mode_fit(
            self.frequencies,
            self.to(self.measured_frf),
            band_hz=band_hz,
            kind=self.measured_frf,
            exponential_decay_rate_per_s=self.exponential_decay_rate_per_s,
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes | np.ndarray:
        """Plot the averaged mobility and its coherence.

        With no ``ax`` a two-panel figure is drawn: ``|Y(f)|`` on log-log axes
        and the coherence beneath it. With ``ax`` only the magnitude is drawn.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the magnitude curve.
        :return: The axes, or the two-axes array.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_impact_mobility

        return plot_impact_mobility(
            self, ax=ax, language=check_language(language), **kwargs
        )

    def report(
        self,
        path: str,
        *,
        metadata: ReportMetadata | None = None,
        engine: str = "reportlab",
        verbose: bool = False,
        language: str = "en",
    ) -> str:
        """Render the ISO 7626 mobility fiche for an impact measurement to a PDF.

        The one-page fiche of :meth:`.MobilityResult.report`, with the
        standard-basis line naming ISO 7626-5:2019 and the characteristic
        points extended by the number of impacts averaged, the exponential
        window and the coherence at the mobility peak.

        :param path: Destination path of the PDF file.
        :param metadata: Optional :class:`~phonometry.ReportMetadata`.
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: Accepted for a uniform ``.report()`` signature; the
            fiche has a single body layout, so it has no effect.
        :param language: ``"en"`` (default) or ``"es"``.
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` is not ``"reportlab"`` or
            ``language`` is unknown.
        :raises ImportError: If reportlab or matplotlib is not installed.
        """
        from ..._i18n import check_language
        from ..._internal.validation import check_engine

        check_language(language)
        check_engine(engine)
        from ..._report.iso7626 import render_impact_mobility_report

        return render_impact_mobility_report(
            self, path, metadata=metadata, verbose=verbose, language=language
        )


def _warn_masked_impacts(
    force: NDArray[np.float64], window: NDArray[np.float64], fs: float
) -> None:
    """Warn when the force window zeroes an impact that happened (6.4)."""
    for row, record in enumerate(force):
        peaks = _impact_peaks(record, 0.1)
        masked = [int(p) for p in peaks if window[p] < 1.0]
        if masked:
            warnings.warn(
                f"impact record {row}: the force window removes an impact at "
                f"{masked[0] / fs:g} s. ISO 7626-5 6.4 forbids using a force "
                "window to eliminate secondary impacts: the response still "
                "carries them, so the estimate is wrong. Discard the record.",
                ImpactExcitationWarning,
                stacklevel=3,
            )


def impact_mobility(
    force: SignalInput,
    response: SignalInput,
    fs: float | None = None,
    *,
    response_quantity: ResponseQuantity = "acceleration",
    force_window_s: float | None = None,
    force_window_start_s: float = 0.0,
    force_window_taper_s: float = 0.0,
    exponential_decay_rate_per_s: float = 0.0,
    exponential_on_force: bool = True,
    driving_point: bool = True,
    frequency_range_hz: tuple[float, float] | None = None,
) -> ImpactMobilityResult:
    r"""Mobility from impact records, averaged as 8.6 prescribes.

    Each row of ``force`` and ``response`` is one impact at the same point,
    triggered as 8.2 describes. The force is multiplied by the force window
    (8.5.1) and both records by the exponential window (8.5.2), both are
    transformed, and the estimate is the averaged cross-spectrum of response
    and force over the averaged auto-spectrum of the force (8.6), with the
    ordinary coherence of 9.1 beside it.

    The DFT runs up to the Nyquist frequency, but a force pulse has a finite
    usable bandwidth (6.2) and the anti-aliasing filter cuts below the Nyquist
    frequency (8.3), so the top of the spectrum is noise divided by almost no
    force. ``frequency_range_hz`` keeps the estimate to the frequency range of
    interest of 3.2, the span at which mobility data are to be obtained, and
    everything built on the result (its plot, its fiche, its fit) stays there.

    Where the force spectrum vanishes the frequency response is undefined,
    and a range that holds such a frequency is refused. A spectrum that
    vanishes in exact arithmetic, at a notch between two equal impacts for
    one, comes out of the transform at the level of its rounding rather than
    at zero, so any bin at or below that level counts as vanished.

    With ``exponential_on_force=False`` the exponential window multiplies the
    response only, and the force of each impact is multiplied instead by the
    window's value at the instant of its peak, the approximation Annex A
    describes for the common practice of windowing the response alone.

    A force window that zeroes an impact the record holds raises
    :class:`ImpactExcitationWarning`: 6.4 forbids removing a second impact
    that way.

    :param force: Force records, in N: one record (1-D) or one per row (2-D).
        Accepts a :class:`phonometry.io.Signal`, one channel per impact, for
        its rate; a calibration factor it carries is deliberately not
        applied, because this record is a force and not a pressure.
    :param response: Response records, same shape, in m/s², m/s or m as
        ``response_quantity`` says; a Signal likewise, its factor not
        applied.
    :param fs: Sample rate, in Hz. Required when both records are bare
        arrays; a :class:`~phonometry.io.Signal` brings its own, and an
        explicit value, or a second Signal, that disagrees with it raises.
    :param response_quantity: ``"acceleration"`` (default), ``"velocity"`` or
        ``"displacement"``.
    :param force_window_s: Width of the unity part of the force window, in
        seconds (Default: ``None``, no force window).
    :param force_window_start_s: Where the unity part begins, in seconds
        (Default: 0).
    :param force_window_taper_s: Half-cosine ramp on each side, in seconds
        (Default: 0).
    :param exponential_decay_rate_per_s: Decay rate ``a`` of the exponential
        window, in 1/s (Default: 0, none).
    :param exponential_on_force: Window the force too (Default: ``True``, the
        exact case of Formula (A.2)).
    :param driving_point: Whether force and response are co-located
        (Default: ``True``).
    :param frequency_range_hz: ``(f_low, f_high)``, the frequency range of
        interest in hertz, inside the Nyquist frequency (Default: ``None``,
        every bin above 0 Hz).
    :return: An :class:`ImpactMobilityResult`.
    :raises ValueError: for records of different shapes, not finite or too
        short, a non-positive sample rate, an unknown response quantity, an
        invalid window, a range that holds no bin above 0 Hz, or a force
        spectrum that vanishes at some frequency of the range.
    :warns ImpactExcitationWarning: when the force window removes an impact.
    """
    rate = require_positive(
        resolve_pair_fs(force, response, fs, names=("force", "response")), "fs"
    )
    f_records = _records(force, "force")
    x_records = _records(response, "response")
    if f_records.shape != x_records.shape:
        msg = (
            f"'force' and 'response' must have the same shape; got "
            f"{f_records.shape} and {x_records.shape}."
        )
        raise ValueError(msg)
    if response_quantity not in _FRF_OF_RESPONSE:
        msg = (
            f"'response_quantity' must be one of {tuple(_FRF_OF_RESPONSE)}; "
            f"got {response_quantity!r}."
        )
        raise ValueError(msg)
    n = f_records.shape[1]
    exponential = exponential_window(
        n, rate, decay_rate_per_s=exponential_decay_rate_per_s
    )
    weighted_force = f_records
    if force_window_s is not None:
        window = force_window(
            n,
            rate,
            width_s=force_window_s,
            start_s=force_window_start_s,
            taper_s=force_window_taper_s,
        )
        _warn_masked_impacts(f_records, window, rate)
        weighted_force = weighted_force * window
    if exponential_on_force:
        weighted_force = weighted_force * exponential
    else:
        peaks = np.argmax(np.abs(weighted_force), axis=1)
        weighted_force = weighted_force * exponential[peaks][:, np.newaxis]
    weighted_response = x_records * exponential

    freqs, f_spec = _spectrum(weighted_force, rate)
    _, x_spec = _spectrum(weighted_response, rate)
    g_ff = np.sum(np.abs(f_spec) ** 2, axis=0)
    g_xx = np.sum(np.abs(x_spec) ** 2, axis=0)
    g_xf = np.sum(x_spec * np.conj(f_spec), axis=0)
    band = freqs > 0.0
    if frequency_range_hz is not None:
        low, high = _frequency_range(frequency_range_hz, nyquist=rate / 2.0)
        band &= (freqs >= low) & (freqs <= high)
        if not np.any(band):
            msg = (
                f"'frequency_range_hz' ({low:g} Hz to {high:g} Hz) holds no DFT "
                f"bin above 0 Hz; the bins are {rate / n:g} Hz apart."
            )
            raise ValueError(msg)
    vanishing = ~(g_ff[band] > _rounding_floor(weighted_force, rate))
    if np.any(vanishing):
        zero = float(freqs[band][vanishing][0])
        msg = (
            f"the force spectrum vanishes at {zero:g} Hz; the frequency response "
            "is undefined where no force was applied."
        )
        raise ValueError(msg)
    frf = g_xf[band] / g_ff[band]
    denominator = g_ff[band] * g_xx[band]
    coherence = np.divide(
        np.abs(g_xf[band]) ** 2,
        denominator,
        out=np.zeros_like(denominator),
        where=denominator > 0.0,
    )
    impacts = f_records.shape[0]
    factor = _one_sided_factor(n, freqs.size)[band]
    return ImpactMobilityResult(
        frequencies=np.asarray(freqs[band], dtype=np.float64),
        mobility=convert_frf(
            frf, freqs[band], _FRF_OF_RESPONSE[response_quantity], "mobility"
        ),
        coherence=np.asarray(np.clip(coherence, 0.0, 1.0), dtype=np.float64),
        force_energy_spectral_density=np.asarray(
            factor * g_ff[band] / impacts, dtype=np.float64
        ),
        impacts=impacts,
        exponential_decay_rate_per_s=float(exponential_decay_rate_per_s),
        response_quantity=response_quantity,
        driving_point=bool(driving_point),
    )


# ---------------------------------------------------------------------------
# One mode, and the correction of Annex A.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExponentialWindowCorrection(OwnsArrays):
    r"""The damping an exponential window added, taken away (Annex A).

    Formula (A.3), :math:`\zeta_r = \hat\zeta_r - a/\omega_r`, per mode, with
    :math:`\hat\zeta_r` the damping ratio estimated from the windowed data,
    :math:`a` the window's decay rate and :math:`\omega_r` the damped natural
    frequency in rad/s. For a lightly damped, well separated mode the measured
    peak is multiplied by :math:`\hat\zeta_r / \zeta_r` to give the true one.

    :ivar damped_natural_frequency_hz: Damped natural frequency of each mode,
        :math:`\omega_r / 2\pi`, in hertz.
    :ivar apparent_damping_ratio: Damping ratio of each mode estimated from the
        windowed data, :math:`\hat\zeta_r`.
    :ivar exponential_decay_rate_per_s: The window's decay rate ``a``, in 1/s.
    """

    damped_natural_frequency_hz: np.ndarray
    apparent_damping_ratio: np.ndarray
    _: KW_ONLY
    exponential_decay_rate_per_s: float

    def __post_init__(self) -> None:
        r"""Reject a correction that would leave a mode undamped or worse.

        :raises ValueError: if the two arrays differ in rank or length, a
            frequency is not positive and finite, a damping ratio lies outside
            (0, 1), the decay rate is negative, or the window's damping
            :math:`a/\omega_r` reaches the apparent damping of a mode, which no
            real structure allows: the damping estimate or the decay rate is
            wrong.
        """
        require_ranks(self, damped_natural_frequency_hz=1, apparent_damping_ratio=1)
        require_same_length(
            self,
            "damped_natural_frequency_hz",
            "apparent_damping_ratio",
            axis="mode",
        )
        owner = type(self).__name__
        freqs = np.asarray(self.damped_natural_frequency_hz, dtype=np.float64)
        zeta = np.asarray(self.apparent_damping_ratio, dtype=np.float64)
        if freqs.size == 0 or not np.all(np.isfinite(freqs)) or np.any(freqs <= 0.0):
            msg = f"{owner}: 'damped_natural_frequency_hz' must be positive and finite."
            raise ValueError(msg)
        if np.any(~(zeta > 0.0)) or np.any(~(zeta < 1.0)):
            msg = f"{owner}: 'apparent_damping_ratio' must lie in (0, 1)."
            raise ValueError(msg)
        require_non_negative(
            self.exponential_decay_rate_per_s, "exponential_decay_rate_per_s"
        )
        corrected = self.damping_ratio
        if np.any(~(corrected > 0.0)):
            worst = int(np.argmin(corrected))
            msg = (
                f"{owner}: the window's damping a/omega_r = "
                f"{float(self.window_damping_ratio[worst]):.4g} is not below the "
                f"apparent damping {float(zeta[worst]):.4g} of the mode at "
                f"{float(freqs[worst]):g} Hz; the damping estimate or the decay "
                "rate is wrong."
            )
            raise ValueError(msg)

    @property
    def window_damping_ratio(self) -> np.ndarray:
        r"""The damping the window added to each mode, :math:`a/\omega_r`."""
        omega = (
            2.0 * np.pi * np.asarray(self.damped_natural_frequency_hz, dtype=np.float64)
        )
        return np.asarray(self.exponential_decay_rate_per_s / omega, dtype=np.float64)

    @property
    def damping_ratio(self) -> np.ndarray:
        r"""True damping ratio of each mode, Formula (A.3): :math:`\hat\zeta_r - a/\omega_r`."""
        zeta = np.asarray(self.apparent_damping_ratio, dtype=np.float64)
        return np.asarray(zeta - self.window_damping_ratio, dtype=np.float64)

    @property
    def peak_correction_factor(self) -> np.ndarray:
        r"""Factor on the measured peak of each mode, :math:`\hat\zeta_r / \zeta_r`."""
        zeta = np.asarray(self.apparent_damping_ratio, dtype=np.float64)
        return np.asarray(zeta / self.damping_ratio, dtype=np.float64)

    @property
    def exact_damping_ratio(self) -> np.ndarray:
        r"""Damping ratio of the pole moved back by ``a``, of which (A.3) is the first order.

        The window replaces the pole :math:`s_r = -\sigma_r + j\omega_r` by
        :math:`s_r - a` (Annex A, after Formula (A.2)), so the decay rate of
        the windowed mode is :math:`\hat\sigma_r = \sigma_r + a` at the same
        damped frequency. From :math:`\hat\sigma_r = \hat\zeta_r \omega_r /
        \sqrt{1 - \hat\zeta_r^2}`, the true ratio is
        :math:`\sigma_r / \sqrt{\sigma_r^2 + \omega_r^2}` with
        :math:`\sigma_r = \hat\sigma_r - a`. It and (A.3) differ by about
        :math:`(\hat\zeta_r^3 - \zeta_r^3)/2`.
        """
        zeta = np.asarray(self.apparent_damping_ratio, dtype=np.float64)
        omega = (
            2.0 * np.pi * np.asarray(self.damped_natural_frequency_hz, dtype=np.float64)
        )
        sigma = (
            zeta * omega / np.sqrt(1.0 - zeta**2) - self.exponential_decay_rate_per_s
        )
        return np.asarray(sigma / np.hypot(sigma, omega), dtype=np.float64)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot each mode's apparent damping split into the true and the window's part.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the bars of the true damping.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_exponential_window_correction

        return plot_exponential_window_correction(
            self, ax=ax, language=check_language(language), **kwargs
        )


def exponential_window_correction(
    damped_natural_frequency_hz: ArrayLike,
    apparent_damping_ratio: ArrayLike,
    *,
    exponential_decay_rate_per_s: float,
) -> ExponentialWindowCorrection:
    r"""Remove an exponential window's damping from estimated modes (Formula (A.3)).

    :math:`\zeta_r = \hat\zeta_r - a/\omega_r` for each mode, with
    :math:`\omega_r = 2\pi f_r` the damped natural frequency. Estimate
    :math:`\hat\zeta_r` from the windowed data with any curve fitter (Annex A
    leaves the method open; :func:`single_mode_fit` is one).

    :param damped_natural_frequency_hz: Damped natural frequency of each mode,
        in hertz (scalar or 1-D).
    :param apparent_damping_ratio: Damping ratio estimated from the windowed
        data, per mode, in (0, 1).
    :param exponential_decay_rate_per_s: Decay rate ``a`` of the window, in 1/s.
    :return: An :class:`ExponentialWindowCorrection`.
    :raises ValueError: for mismatched or invalid inputs, or a window whose
        damping reaches a mode's apparent damping.
    """
    return ExponentialWindowCorrection(
        damped_natural_frequency_hz=np.atleast_1d(
            np.asarray(damped_natural_frequency_hz, dtype=np.float64)
        ),
        apparent_damping_ratio=np.atleast_1d(
            np.asarray(apparent_damping_ratio, dtype=np.float64)
        ),
        exponential_decay_rate_per_s=float(exponential_decay_rate_per_s),
    )


@dataclass(frozen=True)
class SingleModeFitResult(OwnsArrays):
    r"""One mode fitted over a band: pole, residue and a direct term.

    The model is
    :math:`H(s) = D + \frac{R}{s - p} + \frac{R^{*}}{s - p^{*}}`, with
    :math:`p = -\hat\sigma + j\omega_d` the pole of the data fitted,
    :math:`R` its residue and :math:`D` a real constant that stands in for the
    modes outside the band. For a single-degree-of-freedom structure the model
    is exact in every FRF kind: :math:`D = 0` for dynamic compliance and
    mobility and :math:`D = 1/m` for accelerance.

    :ivar frequencies: The frequencies fitted, in hertz.
    :ivar frf: The FRF fitted, complex, of kind :attr:`kind`.
    :ivar pole_rad_s: The pole :math:`p` of the data, upper half plane, in rad/s.
    :ivar residue: Its residue :math:`R`, in the FRF's unit times rad/s.
    :ivar direct_term: The constant :math:`D`, in the FRF's unit.
    :ivar kind: The FRF kind fitted: ``"accelerance"``, ``"mobility"`` or
        ``"receptance"``.
    :ivar exponential_decay_rate_per_s: Decay rate of the exponential window the
        data carry, in 1/s (0 for none).
    """

    frequencies: np.ndarray
    frf: np.ndarray
    pole_rad_s: complex
    residue: complex
    direct_term: complex
    _: KW_ONLY
    kind: str = "mobility"
    exponential_decay_rate_per_s: float = 0.0

    def __post_init__(self) -> None:
        """Reject a fit whose data do not share one axis or whose pole is not a mode.

        :raises ValueError: if the data differ in rank or length, the kind is
            not a motion-per-force FRF, the pole is not a decaying oscillation,
            or the decay rate is negative.
        """
        require_ranks(self, frequencies=1, frf=1)
        require_same_length(self, "frequencies", "frf", axis="frequency")
        owner = type(self).__name__
        if self.kind not in ("accelerance", "mobility", "receptance"):
            msg = (
                f"{owner}: 'kind' must be 'accelerance', 'mobility' or "
                f"'receptance'; got {self.kind!r}."
            )
            raise ValueError(msg)
        pole = complex(self.pole_rad_s)
        if not (pole.imag > 0.0 and pole.real < 0.0) or not math.isfinite(abs(pole)):
            msg = f"{owner}: 'pole_rad_s' must be a decaying oscillation, -sigma + j*omega_d."
            raise ValueError(msg)
        require_non_negative(
            self.exponential_decay_rate_per_s, "exponential_decay_rate_per_s"
        )

    @property
    def damped_natural_frequency_hz(self) -> float:
        r"""Damped natural frequency :math:`\omega_d / 2\pi`, in hertz."""
        return float(complex(self.pole_rad_s).imag / (2.0 * np.pi))

    @property
    def apparent_damping_ratio(self) -> float:
        r"""Damping ratio of the fitted pole, :math:`\hat\sigma / \lvert p \rvert`.

        With an exponential window this is the apparent damping
        :math:`\hat\zeta_r` of Annex A, the window's included.
        """
        pole = complex(self.pole_rad_s)
        return float(-pole.real / abs(pole))

    @property
    def correction(self) -> ExponentialWindowCorrection:
        """The Annex A correction of this mode for the window its data carry."""
        return exponential_window_correction(
            self.damped_natural_frequency_hz,
            self.apparent_damping_ratio,
            exponential_decay_rate_per_s=self.exponential_decay_rate_per_s,
        )

    def _synthesize(self, frequencies: ArrayLike, pole: complex) -> np.ndarray:
        s = 2j * np.pi * np.asarray(frequencies, dtype=np.float64)
        residue = complex(self.residue)
        value = (
            complex(self.direct_term)
            + residue / (s - pole)
            + np.conj(residue) / (s - np.conj(pole))
        )
        return np.asarray(value, dtype=np.complex128)

    def fitted_frf(self, frequencies: ArrayLike) -> np.ndarray:
        """The fitted model at any frequencies, window included, of kind :attr:`kind`.

        :param frequencies: Frequencies, in hertz.
        :return: The complex FRF.
        """
        return self._synthesize(frequencies, complex(self.pole_rad_s))

    def corrected_frf(self, frequencies: ArrayLike) -> np.ndarray:
        r"""The mode with the window taken out, of kind :attr:`kind` (Annex A).

        The pole is moved back by the decay rate, :math:`p + a`, and the
        residue and direct term are kept: the window multiplies the impulse
        response :math:`R \mathrm{e}^{p t}` by :math:`\mathrm{e}^{-a t}`, which changes the pole
        and nothing else (Formula (A.2)).

        :param frequencies: Frequencies, in hertz.
        :return: The complex FRF.
        """
        pole = complex(self.pole_rad_s) + self.exponential_decay_rate_per_s
        return self._synthesize(frequencies, pole)

    def corrected_mobility(self, frequencies: ArrayLike) -> np.ndarray:
        """The corrected mode as mobility, in m/(N·s).

        :param frequencies: Frequencies, in hertz (> 0).
        :return: The complex mobility.
        """
        return convert_frf(
            self.corrected_frf(frequencies), frequencies, self.kind, "mobility"
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the data fitted, the fitted mode and the mode with the window taken out.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the fitted curve.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_single_mode_fit

        return plot_single_mode_fit(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _solve_mode(
    s: NDArray[np.complex128], h: NDArray[np.complex128]
) -> tuple[NDArray[np.float64], float]:
    """Coefficients ``(a1, a0, b0, b1, b2)`` of the rational fit, reweighted.

    Also returns how well the data determine them: the least, over the
    passes, of the smallest singular value of the least-squares system over
    its largest, with its columns scaled to unit norm. Data that follow a line
    without a resonance make the two denominator columns combinations of the
    numerator ones, and that ratio falls to rounding.
    """
    weight = np.ones(s.size)
    coefficients = np.zeros(5)
    determination = 1.0
    for _ in range(_FIT_ITERATIONS):
        columns = np.stack([h * s, h, -np.ones_like(s), -s, -(s**2)], axis=1)
        rhs = -h * s**2
        system = columns * weight[:, np.newaxis]
        target = rhs * weight
        real_system = np.concatenate([system.real, system.imag])
        real_target = np.concatenate([target.real, target.imag])
        singular = np.linalg.svd(
            real_system / np.linalg.norm(real_system, axis=0), compute_uv=False
        )
        determination = min(determination, float(singular[-1] / singular[0]))
        solution, *_ = np.linalg.lstsq(real_system, real_target, rcond=None)
        converged = np.allclose(solution, coefficients, rtol=1e-13, atol=0.0)
        coefficients = solution
        if converged:
            break
        denominator = np.abs(s**2 + coefficients[0] * s + coefficients[1])
        if not np.all(denominator > 0.0):
            break
        weight = 1.0 / denominator
    return np.asarray(coefficients, dtype=np.float64), determination


def single_mode_fit(
    frequencies: ArrayLike,
    frf: ArrayLike,
    *,
    band_hz: tuple[float, float],
    kind: str = "mobility",
    exponential_decay_rate_per_s: float = 0.0,
) -> SingleModeFitResult:
    r"""Fit one mode to an FRF over a band around its resonance.

    Annex A needs the apparent damping of each mode and leaves the estimator
    open ("suitable parameter estimation capability is now widely available
    through a variety of curve-fitting methods"). This is a rational-fraction
    fit of one mode: the FRF over the band is fitted by
    :math:`(b_0 + b_1 s + b_2 s^2)/(s^2 + a_1 s + a_0)` in linear least
    squares, reweighted by the previous denominator until it settles
    (Sanathanan and Koerner), and the result is written as a pole, its residue
    and a direct term (:class:`SingleModeFitResult`). The model is exact for a
    single-degree-of-freedom structure; on a real one, choose a band that
    holds one resonance and little else.

    Annex A asks that the apparent damping of each mode "can be accurately
    determined", and a band without a resonance determines none: a constant,
    a mass line or a spring line fits the numerator alone and leaves the pole
    to rounding. The fit is refused when its system does not determine the
    five coefficients to half the digits of a double, or when the pole it
    finds has no decay rate or no damped natural frequency above that same
    fraction of the band's centre frequency.

    Fit the FRF in the kind the response channel measured, because that is
    the record the exponential window multiplied:
    :meth:`ImpactMobilityResult.fit_mode` does so.

    :param frequencies: Frequencies of the FRF, in hertz (> 0).
    :param frf: Complex FRF of kind ``kind``, same length.
    :param band_hz: ``(f_low, f_high)``, in hertz, holding at least three
        frequencies.
    :param kind: ``"accelerance"``, ``"mobility"`` (default) or
        ``"receptance"``.
    :param exponential_decay_rate_per_s: Decay rate of the exponential window
        the data carry, in 1/s (Default: 0).
    :return: A :class:`SingleModeFitResult`.
    :raises ValueError: for mismatched or non-finite data, a band that is not
        a pair of positive numbers or holds fewer than three frequencies, an
        unknown kind, or a band whose data hold no lightly damped mode.
    """
    freqs = np.asarray(frequencies, dtype=np.float64)
    values = np.asarray(frf, dtype=np.complex128)
    if freqs.ndim != 1 or values.shape != freqs.shape:
        msg = "'frequencies' and 'frf' must be one-dimensional and of one length."
        raise ValueError(msg)
    if not (np.all(np.isfinite(freqs)) and np.all(np.isfinite(values))):
        msg = "'frequencies' and 'frf' must be finite."
        raise ValueError(msg)
    if kind not in ("accelerance", "mobility", "receptance"):
        msg = f"'kind' must be 'accelerance', 'mobility' or 'receptance'; got {kind!r}."
        raise ValueError(msg)
    low, high = _pair(band_hz, "band_hz")
    low = require_positive(low, "band_hz[0]")
    high = require_positive(high, "band_hz[1]")
    if high <= low:
        msg = "'band_hz' must be (f_low, f_high) with f_high above f_low."
        raise ValueError(msg)
    inside = (freqs >= low) & (freqs <= high)
    if np.count_nonzero(inside) < _MIN_FIT_FREQUENCIES:
        msg = (
            f"'band_hz' holds {np.count_nonzero(inside)} frequencies; a mode "
            f"needs at least {_MIN_FIT_FREQUENCIES}."
        )
        raise ValueError(msg)
    decay = require_non_negative(
        exponential_decay_rate_per_s, "exponential_decay_rate_per_s"
    )
    f_band = freqs[inside]
    h_band = values[inside]
    omega_c = 2.0 * np.pi * math.sqrt(low * high)
    scale = float(np.sqrt(np.mean(np.abs(h_band) ** 2)))
    if scale <= 0.0:
        msg = "'frf' is zero over the band; there is no mode to fit."
        raise ValueError(msg)
    s = np.asarray(1j * (2.0 * np.pi * f_band) / omega_c, dtype=np.complex128)
    coefficients, determination = _solve_mode(
        s, np.asarray(h_band / scale, dtype=np.complex128)
    )
    a1, a0, b0, b1, b2 = coefficients
    discriminant = a0 - a1**2 / 4.0
    if not (
        determination > _FIT_TOLERANCE
        and a1 > _FIT_TOLERANCE
        and discriminant > _FIT_TOLERANCE
    ):
        msg = (
            f"the data between {low:g} Hz and {high:g} Hz hold no lightly damped "
            "mode; narrow the band around one resonance."
        )
        raise ValueError(msg)
    pole_n = complex(-a1 / 2.0, math.sqrt(discriminant))
    remainder = (b0 - b2 * a0) + (b1 - b2 * a1) * pole_n
    residue_n = remainder / (pole_n - pole_n.conjugate())
    return SingleModeFitResult(
        frequencies=f_band,
        frf=h_band,
        pole_rad_s=omega_c * pole_n,
        residue=complex(omega_c * residue_n * scale),
        direct_term=complex(b2 * scale),
        kind=kind,
        exponential_decay_rate_per_s=decay,
    )


# ---------------------------------------------------------------------------
# Checks on the record.
# ---------------------------------------------------------------------------


def _pair(value: object, name: str) -> tuple[float, float]:
    """Two numbers ``(f_low, f_high)``, as given, or a ValueError that says so.

    Indexing the argument would answer a one-number tuple with an IndexError
    and a bare number with a TypeError, neither of which names the argument.
    """
    msg = (
        f"'{name}' must be a pair of numbers (f_low, f_high), in hertz; got {value!r}."
    )
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError(msg)
    try:
        low, high = (require_real(edge, msg) for edge in value)
    except (TypeError, ValueError):
        raise ValueError(msg) from None
    return low, high


def _frequency_range(
    frequency_range_hz: tuple[float, float],
    nyquist: float | None = None,
    *,
    name: str = "frequency_range_hz",
) -> tuple[float, float]:
    """A validated frequency range of interest (3.2).

    ``nyquist`` is half the sample rate, the bound of 8.3, whether or not a
    DFT bin falls on it (an odd record has none there).
    """
    low, high = _pair(frequency_range_hz, name)
    low = require_non_negative(low, f"{name}[0]")
    high = require_positive(high, f"{name}[1]")
    if high <= low:
        msg = f"'{name}' must be (f_low, f_high) with f_high above f_low."
        raise ValueError(msg)
    if nyquist is not None and high > nyquist:
        msg = (
            f"'{name}' ends at {high:.12g} Hz, above the Nyquist frequency "
            f"{nyquist:.12g} Hz, half the sample rate."
        )
        raise ValueError(msg)
    return low, high


@dataclass(frozen=True)
class ForceSpectrumCheck(OwnsArrays):
    r"""Does the force spectrum cover the frequency range of interest? (6.2, 6.3)

    The spectrum of a force pulse is a main lobe at low frequency followed by
    side lobes that fall rapidly, with a usable bandwidth inversely
    proportional to the pulse duration (6.2). The tip stiffness and the
    impactor mass set that bandwidth (6.3), and a double hit cuts notches into
    it (6.4). The check reads how far the energy spectral density falls across
    the frequency range of interest, from its highest to its lowest value
    there, against a limit the caller states: the part prints none.

    :ivar frequencies: Frequencies above 0 Hz, in hertz.
    :ivar energy_spectral_density: One-sided force energy spectral density, in
        N²·s/Hz (3.4).
    :ivar frequency_range_hz: The frequency range of interest (3.2), in hertz.
    :ivar max_drop_db: The largest fall across the range the check accepts,
        in dB.
    """

    frequencies: np.ndarray
    energy_spectral_density: np.ndarray
    _: KW_ONLY
    frequency_range_hz: tuple[float, float]
    max_drop_db: float

    def __post_init__(self) -> None:
        """Reject a check whose spectrum and range do not fit together.

        :raises ValueError: if the arrays differ in rank or length, the range
            holds fewer than two frequencies, or the limit is not positive.
        """
        require_ranks(self, frequencies=1, energy_spectral_density=1)
        require_same_length(
            self, "frequencies", "energy_spectral_density", axis="frequency"
        )
        _frequency_range(self.frequency_range_hz)
        require_positive(self.max_drop_db, "max_drop_db")
        if np.count_nonzero(self.in_range) < _MIN_RANGE_FREQUENCIES:
            msg = "ForceSpectrumCheck: the frequency range must hold at least two frequencies."
            raise ValueError(msg)

    @property
    def in_range(self) -> np.ndarray:
        """Per frequency, whether it lies in the frequency range of interest."""
        freqs = np.asarray(self.frequencies, dtype=np.float64)
        low, high = self.frequency_range_hz
        return (freqs >= low) & (freqs <= high)

    @property
    def level_db(self) -> np.ndarray:
        """The density in dB re its highest value inside the range."""
        esd = np.asarray(self.energy_spectral_density, dtype=np.float64)
        top = float(np.max(esd[self.in_range]))
        with np.errstate(divide="ignore"):
            return np.asarray(10.0 * np.log10(esd / top), dtype=np.float64)

    @property
    def drop_db(self) -> float:
        """How far the density falls across the range, highest to lowest, in dB."""
        return float(-np.min(self.level_db[self.in_range]))

    @property
    def energy_fraction_above(self) -> float:
        """Share of the force energy above the range of interest (6.3)."""
        esd = np.asarray(self.energy_spectral_density, dtype=np.float64)
        freqs = np.asarray(self.frequencies, dtype=np.float64)
        total = float(np.sum(esd))
        return (
            float(np.sum(esd[freqs > self.frequency_range_hz[1]]) / total)
            if total > 0.0
            else 0.0
        )

    @property
    def passes(self) -> bool:
        """Whether the density falls no further than the limit across the range."""
        return self.drop_db <= self.max_drop_db

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a ForceSpectrumCheck has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the force energy spectral density against the range and the limit.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the density curve.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_force_spectrum_check

        return plot_force_spectrum_check(
            self, ax=ax, language=check_language(language), **kwargs
        )


def check_force_spectrum(
    force: SignalInput,
    fs: float | None = None,
    *,
    frequency_range_hz: tuple[float, float],
    max_drop_db: float,
) -> ForceSpectrumCheck:
    """Is the force spectrum flat enough across the frequency range of interest?

    Computes the energy spectral density of one force record (3.3, 3.4) and
    reads how far it falls between its highest and lowest value inside the
    range. The check passes when that fall is at most ``max_drop_db``. The part
    gives no number for it, so the caller states the one their practice uses;
    the share of force energy above the range, which 6.3 asks to keep small, is
    reported beside it as :attr:`ForceSpectrumCheck.energy_fraction_above`.

    :param force: One force record, 1-D, in N (windowed or not, as it will be
        processed). Accepts a :class:`phonometry.io.Signal` for its rate; a
        calibration factor it carries is deliberately not applied, because
        this record is a force in newtons and not a pressure.
    :param fs: Sample rate, in Hz. Required for a bare array; a
        :class:`~phonometry.io.Signal` brings its own, and an explicit value
        that disagrees with it raises instead of silently winning.
    :param frequency_range_hz: ``(f_low, f_high)``, the frequency range of
        interest, in hertz.
    :param max_drop_db: The largest fall across the range to accept, in dB.
    :return: A :class:`ForceSpectrumCheck`.
    :raises ValueError: for an invalid record, sample rate, range or limit.
    """
    rate = require_positive(resolve_fs(force, fs, name="force"), "fs")
    freqs, esd = energy_spectral_density(force, rate)
    low, high = _frequency_range(frequency_range_hz, nyquist=rate / 2.0)
    return ForceSpectrumCheck(
        frequencies=freqs[1:],
        energy_spectral_density=esd[1:],
        frequency_range_hz=(low, high),
        max_drop_db=float(max_drop_db),
    )


@dataclass(frozen=True)
class OverloadCheck(OwnsArrays):
    """Did the record stay inside the linear range of its channel? (8.4)

    Impact excitation risks saturating the measurement system, because the
    signals carry out-of-band energy and the dynamic range is used to its
    limit (8.4). Saturation is not always visible as a clipped waveform, so
    8.4 asks that the manufacturer's maximum for linear operation be observed,
    and warns that filtered digital records give poor definition of the actual
    waveform: pass the widest-band record available. A pass here is necessary,
    not sufficient.

    :ivar record: The record judged, in its own unit, as a bare array (a
        :class:`~phonometry.io.Signal` passed in is read without its
        calibration factor, and its samples are what is kept).
    :ivar fs: Its sample rate, in Hz.
    :ivar full_scale: The largest magnitude the channel handles linearly, in the
        unit of the record.
    """

    record: np.ndarray
    fs: float
    _: KW_ONLY
    full_scale: float

    def __post_init__(self) -> None:
        """Reject a check without a record or a positive full scale.

        :raises ValueError: if the record is not 1-D or the full scale or the
            sample rate is not positive.
        """
        require_ranks(self, record=1)
        require_positive(self.fs, "fs")
        require_positive(self.full_scale, "full_scale")

    @property
    def peak(self) -> float:
        """Largest magnitude in the record, in its unit."""
        return float(np.max(np.abs(np.asarray(self.record, dtype=np.float64))))

    @property
    def clipped_samples(self) -> int:
        """How many samples reach the full scale."""
        return int(np.count_nonzero(np.abs(np.asarray(self.record)) >= self.full_scale))

    @property
    def headroom_db(self) -> float:
        """Distance from the peak to the full scale, in dB (infinite for silence)."""
        peak = self.peak
        return (
            float(20.0 * math.log10(self.full_scale / peak)) if peak > 0.0 else math.inf
        )

    @property
    def passes(self) -> bool:
        """Whether every sample stays below the full scale."""
        return self.peak < self.full_scale

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "an OverloadCheck has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the record against its full scale, clipped samples marked.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the record curve.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_overload_check

        return plot_overload_check(
            self, ax=ax, language=check_language(language), **kwargs
        )


def check_overload(
    record: SignalInput, fs: float | None = None, *, full_scale: float
) -> OverloadCheck:
    """Did one channel of the record stay below its full scale? (8.4)

    :param record: One record, 1-D, in any unit. Accepts a
        :class:`phonometry.io.Signal` for its rate; a calibration factor it
        carries is deliberately not applied, so the samples stay in the unit
        the channel recorded them in, the unit of its full scale.
    :param fs: Sample rate, in Hz. Required for a bare array; a
        :class:`~phonometry.io.Signal` brings its own, and an explicit value
        that disagrees with it raises instead of silently winning.
    :param full_scale: The manufacturer's maximum for linear operation, in the
        unit of the record.
    :return: An :class:`OverloadCheck`, which passes when every sample stays
        strictly below the full scale.
    :raises ValueError: for an invalid record, sample rate or full scale.
    """
    rate = require_positive(resolve_fs(record, fs, name="record"), "fs")
    x = _record(record, "record")
    return OverloadCheck(
        record=x,
        fs=rate,
        full_scale=require_positive(full_scale, "full_scale"),
    )


@dataclass(frozen=True)
class ResponseDecayCheck(OwnsArrays):
    r"""Did the response decay far enough within the record? (8.3, 8.5.2)

    Without a window the response should decay to about 1 % of its initial
    magnitude at the end of the record, or truncation leaks (8.3). 8.3 calls
    that figure a compromise: a longer record, reaching further down, improves
    the frequency resolution but can lower the signal-to-noise ratio, so a
    much faster decay is no better. With an exponential window, as a general
    guideline, the natural decay should reach 25 % or less, or the corrections
    of Annex A become very sensitive to errors in the damping estimates
    (8.5.2). 8.5.2 also offers a convenient check: the peak response at the
    midpoint of the record is about 10 % of the highest one, which for a steady
    exponential decay is the same statement as 1 % at the end.

    Levels are peaks of the magnitude over segments of the record, relative to
    the highest peak from ``start_s`` on; a segment needs at least one period
    of the lowest mode for its peak to be a peak. The midpoint level is the
    peak over the segment that starts at the midpoint. The level at the end is
    read at the last sample: the peak over the last segment sits at its start,
    so it is carried to the last sample at the rate the peaks decay from the
    midpoint segment to the last one, the steady decay the midpoint check
    itself assumes. A response that has stopped decaying, on a noise floor, is
    read at the peak of its last segment, never higher.

    The verdict compares the level at the end, rounded to a whole per cent
    (the precision both figures are printed in), with the figure: "about 1 %"
    accepts any level below 1,5 %, which rounds to 1 %, and "25 % or less"
    any level below 25,5 %.

    A driving-point acceleration follows the force itself during the impact
    (the mass line of the structure), so its highest peak can be the impact
    rather than the decay. ``start_s`` just after the force pulse, or the force
    record passed to :func:`check_response_decay`, judges the free decay alone.

    :ivar record: The response record judged, unwindowed, in its own unit, as
        a bare array (a :class:`~phonometry.io.Signal` passed in is read
        without its calibration factor, and its samples are what is kept).
    :ivar fs: Its sample rate, in Hz.
    :ivar segment_s: Length of the segments the end and midpoint levels are
        read over, in seconds.
    :ivar exponential_window: Whether the record is to be processed with an
        exponential window (25 % limit) or without (1 %).
    :ivar start_s: Time from which the highest peak is sought, in seconds.
    """

    record: np.ndarray
    fs: float
    _: KW_ONLY
    segment_s: float
    exponential_window: bool
    start_s: float = 0.0

    def __post_init__(self) -> None:
        """Reject a check whose segment or start does not fit in its record.

        :raises ValueError: if the record is not 1-D and finite, the sample
            rate or the segment is not positive, the segment is longer than
            half the record, the start is negative or reaches the midpoint, or
            the record is zero at every sample from the start on.
        """
        require_ranks(self, record=1)
        require_positive(self.fs, "fs")
        require_positive(self.segment_s, "segment_s")
        require_non_negative(self.start_s, "start_s")
        record = np.asarray(self.record, dtype=np.float64)
        if not np.all(np.isfinite(record)):
            msg = "ResponseDecayCheck: 'record' must be finite."
            raise ValueError(msg)
        size = record.size
        if self._segment_samples() > size // 2:
            msg = "ResponseDecayCheck: 'segment_s' must be at most half the record."
            raise ValueError(msg)
        if self._start_sample() >= size // 2:
            msg = "ResponseDecayCheck: 'start_s' must lie before the midpoint of the record."
            raise ValueError(msg)
        # A dead channel reads zero at its end too, and would pass for a
        # response that decayed: there is nothing to judge a decay against.
        if self.peak <= 0.0:
            msg = (
                "ResponseDecayCheck: the record holds no motion from 'start_s' "
                "on; a silent channel has not decayed, it has measured nothing."
            )
            raise ValueError(msg)

    def _segment_samples(self) -> int:
        return max(1, round(self.segment_s * self.fs))

    def _start_sample(self) -> int:
        return round(self.start_s * self.fs)

    def _magnitude(self) -> NDArray[np.float64]:
        return np.abs(np.asarray(self.record, dtype=np.float64))

    @property
    def peak(self) -> float:
        """The highest peak of the response from ``start_s`` on, in its unit."""
        return float(np.max(self._magnitude()[self._start_sample() :]))

    @property
    def peak_time_s(self) -> float:
        """When the highest peak from ``start_s`` on occurs, in seconds."""
        start = self._start_sample()
        return (start + int(np.argmax(self._magnitude()[start:]))) / self.fs

    @property
    def midpoint_ratio(self) -> float:
        """Peak over the segment starting at the midpoint, relative to the highest peak."""
        x = self._magnitude()
        middle = x.size // 2
        segment = x[middle : middle + self._segment_samples()]
        return float(np.max(segment) / self.peak)

    @property
    def last_segment_ratio(self) -> float:
        """Peak over the last segment, relative to the highest peak.

        For a response still decaying this is its level at the start of the
        segment, above the level at the end of the record.
        """
        x = self._magnitude()
        return float(np.max(x[-self._segment_samples() :]) / self.peak)

    @property
    def end_ratio(self) -> float:
        """Level at the last sample of the record, relative to the highest peak.

        The peak over the last segment, carried over the rest of the segment
        at the rate the segment peaks decay from the midpoint to the last
        segment (never raised).
        """
        size = np.asarray(self.record).size
        segment = self._segment_samples()
        last = self.last_segment_ratio
        middle = self.midpoint_ratio
        span = size - segment - size // 2
        if not (span > 0 and middle > last > 0.0):
            return last
        return float(last * (last / middle) ** ((segment - 1) / span))

    @property
    def limit_ratio(self) -> float:
        """The figure the clause prints: 0,01 without a window, 0,25 with one."""
        return (
            WINDOWED_RESPONSE_END_RATIO
            if self.exponential_window
            else RESPONSE_END_RATIO
        )

    @property
    def passes(self) -> bool:
        """Whether the level at the end, to a whole per cent, is at most the figure."""
        reading = math.floor(_PERCENT * self.end_ratio + 0.5)
        return reading <= round(_PERCENT * self.limit_ratio)

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a ResponseDecayCheck has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the response with the levels it reaches at the midpoint and the end.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the response curve.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_response_decay_check

        return plot_response_decay_check(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _pulse_end(force: NDArray[np.float64]) -> int:
    """First sample after the largest force peak at which the pulse is over.

    The impact runs in the direction of the largest excursion, as in
    :func:`check_double_hit`; the pulse is over where the force has fallen
    back to ``_PULSE_END_RATIO`` of that peak.
    """
    signed, loudest = _signed_force(force)
    peak = signed[loudest]
    if peak <= 0.0:
        msg = "'force' holds no force: every sample is zero."
        raise ValueError(msg)
    after = np.flatnonzero(signed[loudest:] <= _PULSE_END_RATIO * peak)
    if after.size == 0:
        msg = "'force' does not fall back after its peak: the pulse must end inside the record."
        raise ValueError(msg)
    return loudest + int(after[0])


def check_response_decay(
    response: SignalInput,
    fs: float | None = None,
    *,
    exponential_window: bool = False,
    segment_s: float | None = None,
    start_s: float = 0.0,
    force: SignalInput | None = None,
) -> ResponseDecayCheck:
    """Has the response decayed enough by the end of the record? (8.3, 8.5.2)

    Without an exponential window the response should end at about 1 % of its
    highest peak (8.3, 8.5.2); with one, its natural decay should reach 25 % or
    less, the general guideline of 8.5.2. The level at the end is read at the
    last sample and compared with the figure to a whole per cent, so any
    level below 1,5 % passes "about 1 %" (see :class:`ResponseDecayCheck`).
    8.3 calls the 1 % a compromise, and the check is one-sided: it asks
    whether the response has decayed far enough, not whether it decayed too
    far. Pass the response as recorded, before any window.

    :param response: One response record, 1-D, in any unit. Accepts a
        :class:`phonometry.io.Signal` for its rate; a calibration factor it
        carries is deliberately not applied, because this record is a motion
        and not a pressure.
    :param fs: Sample rate, in Hz. Required when the records are bare arrays;
        a :class:`~phonometry.io.Signal` brings its own, and an explicit value,
        or a force Signal, that disagrees with it raises instead of silently
        winning.
    :param exponential_window: Whether the record is to be processed with an
        exponential window (Default: ``False``).
    :param segment_s: Length of the segments the levels are read over, in
        seconds; make it at least one period of the lowest mode (Default:
        ``None``, one tenth of the record).
    :param start_s: Time from which the highest peak is sought, in seconds
        (Default: 0, the whole record, as the clause reads).
    :param force: The force record of the same impact, same length (Default:
        ``None``). When given, the highest peak is sought only after the force
        pulse, where the force has fallen back to 1 % of its peak, so a
        driving-point acceleration is judged on its free decay and not on the
        impact it follows (the mass line). The later of this and ``start_s``
        is used. A Signal likewise, its factor not applied.
    :return: A :class:`ResponseDecayCheck`.
    :raises ValueError: for an invalid record, sample rate, segment or start,
        a response that is zero at every sample or at every sample from the
        start on (a dead channel has measured nothing, so it has not decayed
        either), or a force record of another length, without force or whose
        pulse does not end inside the record.
    """
    if force is None:
        rate = require_positive(resolve_fs(response, fs, name="response"), "fs")
    else:
        rate = require_positive(
            resolve_pair_fs(response, force, fs, names=("response", "force")), "fs"
        )
    x = _record(response, "response")
    if not np.any(x):
        # As check_double_hit refuses a force record without force: a dead
        # channel ends at zero and would read as a response that decayed.
        msg = "'response' holds no motion: every sample is zero."
        raise ValueError(msg)
    start = require_non_negative(start_s, "start_s")
    if force is not None:
        pulse = _record(force, "force")
        if pulse.size != x.size:
            msg = (
                f"'force' and 'response' must be records of one length; got "
                f"{pulse.size} and {x.size} samples."
            )
            raise ValueError(msg)
        start = max(start, _pulse_end(pulse) / rate)
    segment = (
        x.size / rate / 10.0
        if segment_s is None
        else require_positive(segment_s, "segment_s")
    )
    return ResponseDecayCheck(
        record=x,
        fs=rate,
        segment_s=float(segment),
        exponential_window=bool(exponential_window),
        start_s=float(start),
    )


@dataclass(frozen=True)
class CoherenceCheck(OwnsArrays):
    r"""Is the coherence high, over enough impacts to trust it? (9.1)

    The coherence expresses how linearly the response follows the force at
    each frequency; a value below 1 flags possible poor data (9.1). The clause
    calls a coherence above 0,9 high, and says only a few records, five to
    ten, are then needed for high statistical confidence in its estimate.
    NOTE 1 adds that low coherence at an anti-resonance is not generally a
    concern: the response is near the noise floor there. Such frequencies can
    be excluded from the judgement.

    :ivar frequencies: Frequencies in the range of interest, in hertz.
    :ivar coherence: Ordinary coherence :math:`\gamma^2` at each.
    :ivar judged: Per frequency, whether it enters the verdict (``False`` where
        excluded as an anti-resonance).
    :ivar impacts: Number of impacts averaged.
    :ivar minimum_coherence: The coherence each judged frequency must exceed.
    :ivar minimum_records: The fewest impacts the check accepts.
    """

    frequencies: np.ndarray
    coherence: np.ndarray
    judged: np.ndarray
    _: KW_ONLY
    impacts: int
    minimum_coherence: float = HIGH_COHERENCE
    minimum_records: int = COHERENCE_RECORDS

    def __post_init__(self) -> None:
        """Reject a check whose arrays disagree or whose limits are meaningless.

        :raises ValueError: if the arrays differ in rank or length, no
            frequency is judged, a coherence lies outside [0, 1], the minimum
            coherence outside (0, 1), or a count is not a whole number of at
            least 1 (a bool is refused).
        """
        require_ranks(self, frequencies=1, coherence=1, judged=1)
        require_same_length(
            self, "frequencies", "coherence", "judged", axis="frequency"
        )
        owner = type(self).__name__
        gamma2 = np.asarray(self.coherence, dtype=np.float64)
        if np.any(~(gamma2 >= 0.0)) or np.any(gamma2 > 1.0):
            msg = f"{owner}: 'coherence' must lie in [0, 1]."
            raise ValueError(msg)
        if not 0.0 < self.minimum_coherence < 1.0:
            msg = f"{owner}: 'minimum_coherence' must lie in (0, 1)."
            raise ValueError(msg)
        # int() would read 5.9 as 5 and True as 1: a count is a whole number.
        require_count(self.impacts, "impacts")
        require_count(self.minimum_records, "minimum_records")
        # With nothing judged, every judged frequency is high by default and
        # the verdict passes without having looked at the coherence.
        if not np.any(np.asarray(self.judged, dtype=bool)):
            msg = (
                f"{owner}: no frequency is judged; the exclusions cover the "
                "whole range, so there is no coherence to pass or fail."
            )
            raise ValueError(msg)

    @property
    def high(self) -> np.ndarray:
        """Per frequency, whether the coherence exceeds the minimum."""
        return np.asarray(self.coherence, dtype=np.float64) > self.minimum_coherence

    @property
    def enough_records(self) -> bool:
        """Whether enough impacts were averaged for the coherence to be trusted."""
        return int(self.impacts) >= int(self.minimum_records)

    @property
    def random_error_percent(self) -> np.ndarray:
        """Normalized random error of the FRF magnitude, in percent (ISO 7626-2 Annex A).

        NaN where the coherence is zero.
        """
        gamma2 = np.asarray(self.coherence, dtype=np.float64)
        error = np.full(gamma2.shape, np.nan)
        valid = gamma2 > 0.0
        if np.any(valid):
            error[valid] = random_error_percent(gamma2[valid], int(self.impacts))
        return error

    @property
    def passes(self) -> bool:
        """Whether every judged frequency is high and the records are enough."""
        judged = np.asarray(self.judged, dtype=bool)
        return bool(np.all(self.high[judged])) and self.enough_records

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a CoherenceCheck has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the coherence against its minimum, excluded frequencies shaded.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the coherence curve.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_coherence_check

        return plot_coherence_check(
            self, ax=ax, language=check_language(language), **kwargs
        )


def check_coherence(
    result: ImpactMobilityResult,
    *,
    frequency_range_hz: tuple[float, float],
    exclude_hz: Sequence[tuple[float, float]] = (),
    minimum_coherence: float = HIGH_COHERENCE,
    minimum_records: int = COHERENCE_RECORDS,
) -> CoherenceCheck:
    """Is the averaged estimate's coherence high over the range of interest? (9.1)

    The check passes when the coherence exceeds ``minimum_coherence`` (0,9,
    what 9.1 calls high) at every frequency of the range that is not excluded,
    and at least ``minimum_records`` impacts were averaged (five, the lower end
    of the five to ten 9.1 says a high coherence needs). A single impact has a
    coherence of 1 by construction and fails the second condition.

    8.6 finds three to five impacts usually enough to verify data quality in a
    low-noise environment; the coherence estimate itself, 9.1 adds, needs five
    to ten records to be trusted. Averaging five impacts satisfies both, and a
    lower ``minimum_records`` states that fewer were judged enough.

    :param result: The averaged estimate, from :func:`impact_mobility`.
    :param frequency_range_hz: ``(f_low, f_high)``, in hertz.
    :param exclude_hz: Bands ``(f_low, f_high)`` to leave out of the verdict,
        such as anti-resonances (9.1, NOTE 1) (Default: none).
    :param minimum_coherence: The coherence to exceed (Default: 0.9).
    :param minimum_records: The fewest impacts to accept, a whole number of at
        least 1 (Default: 5).
    :return: A :class:`CoherenceCheck`.
    :raises ValueError: for an invalid range, exclusion or limit, a
        ``minimum_records`` that is not a whole number of at least 1, or
        exclusions that leave no frequency of the range to judge.
    """
    low, high = _frequency_range(frequency_range_hz)
    records = require_count(minimum_records, "minimum_records")
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    inside = (freqs >= low) & (freqs <= high)
    if not np.any(inside):
        msg = "'frequency_range_hz' holds none of the estimate's frequencies."
        raise ValueError(msg)
    judged = np.ones(int(np.count_nonzero(inside)), dtype=bool)
    for lo, hi in _exclusions(exclude_hz):
        judged &= ~((freqs[inside] >= lo) & (freqs[inside] <= hi))
    if not np.any(judged):
        msg = (
            "'exclude_hz' covers every frequency of 'frequency_range_hz'; with "
            "nothing left to judge, the verdict would pass on no coherence at all."
        )
        raise ValueError(msg)
    return CoherenceCheck(
        frequencies=freqs[inside],
        coherence=np.asarray(result.coherence, dtype=np.float64)[inside],
        judged=judged,
        impacts=int(result.impacts),
        minimum_coherence=float(require_finite(minimum_coherence, "minimum_coherence")),
        minimum_records=records,
    )


def _exclusions(exclude_hz: object) -> list[tuple[float, float]]:
    """The anti-resonance bands of :func:`check_coherence`, each validated.

    A single band passed bare, ``(40.0, 50.0)``, is a sequence of two numbers
    and not of pairs; it is refused with the form it should take.
    """
    msg = (
        "'exclude_hz' must be a sequence of (f_low, f_high) pairs, such as "
        f"[(40.0, 50.0)]; got {exclude_hz!r}."
    )
    if isinstance(exclude_hz, (str, bytes)) or not isinstance(exclude_hz, Iterable):
        raise ValueError(msg)
    bands = list(exclude_hz)
    if any(isinstance(band, (int, float, np.number)) for band in bands):
        raise ValueError(msg)
    return [
        _frequency_range(band, name=f"exclude_hz[{index}]")
        for index, band in enumerate(bands)
    ]


@dataclass(frozen=True)
class ChannelMatchVerification(OwnsArrays):
    """Do two analyser channels match in gain and phase? (8.1)

    The channel-to-channel match of the filters and the analyser is checked by
    connecting one broad-band signal to both channels and measuring the
    frequency response between them: its magnitude should equal unity within
    +/- 5 % over the frequency range of interest and its phase zero within
    +/- 5 degrees (8.1).

    :ivar frequencies: Frequencies in the range of interest, in hertz.
    :ivar response: Complex frequency response between the channels.
    """

    frequencies: np.ndarray
    response: np.ndarray

    def __post_init__(self) -> None:
        """Reject a verification whose response is not on its frequency axis.

        :raises ValueError: if the arrays differ in rank or length, or are empty
            or not finite.
        """
        require_ranks(self, frequencies=1, response=1)
        require_same_length(self, "frequencies", "response", axis="frequency")
        if np.asarray(self.frequencies).size == 0 or not np.all(
            np.isfinite(np.asarray(self.response))
        ):
            msg = "ChannelMatchVerification: the response must be finite and not empty."
            raise ValueError(msg)

    @property
    def magnitude_deviation(self) -> np.ndarray:
        """Relative deviation of the magnitude from unity, ``|H| - 1``."""
        return np.asarray(np.abs(self.response) - 1.0, dtype=np.float64)

    @property
    def phase_deg(self) -> np.ndarray:
        """Phase of the response, in degrees."""
        return np.asarray(np.degrees(np.angle(self.response)), dtype=np.float64)

    @property
    def magnitude_within(self) -> np.ndarray:
        """Per frequency, whether the magnitude is within +/- 5 % of unity.

        The magnitude is compared with the bounds ``1 - 0,05`` and
        ``1 + 0,05`` themselves, so a response of exactly 0,95 or 1,05 is
        within them.
        """
        magnitude = np.abs(np.asarray(self.response))
        return np.asarray(
            (magnitude >= 1.0 - CHANNEL_MAGNITUDE_TOLERANCE)
            & (magnitude <= 1.0 + CHANNEL_MAGNITUDE_TOLERANCE),
            dtype=bool,
        )

    @property
    def phase_within(self) -> np.ndarray:
        """Per frequency, whether the phase is within +/- 5 degrees of zero."""
        return np.abs(self.phase_deg) <= CHANNEL_PHASE_TOLERANCE_DEG

    @property
    def passes(self) -> bool:
        """Whether both requirements hold at every frequency."""
        return bool(np.all(self.magnitude_within) and np.all(self.phase_within))

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a ChannelMatchVerification has no truth value; read its '.passes' "
            "for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes | np.ndarray:
        """Plot the magnitude and phase deviations against their tolerances.

        With no ``ax`` a two-panel figure is drawn; with ``ax`` only the
        magnitude deviation.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the magnitude-deviation curve.
        :return: The axes, or the two-axes array.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_channel_match

        return plot_channel_match(
            self, ax=ax, language=check_language(language), **kwargs
        )


def verify_channel_match(
    frequencies: ArrayLike,
    response: ArrayLike,
    *,
    frequency_range_hz: tuple[float, float],
) -> ChannelMatchVerification:
    """Is the analyser's channel-to-channel match inside 8.1's tolerances?

    Feed the same broad-band signal to both channels, estimate the frequency
    response between them (for instance with
    :func:`phonometry.electroacoustics.frequency_response.transfer_function`),
    and pass it here. The verification passes when its magnitude is unity
    within +/- 5 % and its phase zero within +/- 5 degrees at every frequency
    of the range of interest.

    :param frequencies: Frequencies of the response, in hertz.
    :param response: Complex frequency response between the channels.
    :param frequency_range_hz: ``(f_low, f_high)``, in hertz.
    :return: A :class:`ChannelMatchVerification` over the range.
    :raises ValueError: for mismatched or non-finite data, or a range that
        holds none of the frequencies.
    """
    freqs = np.asarray(frequencies, dtype=np.float64)
    values = np.asarray(response, dtype=np.complex128)
    if freqs.ndim != 1 or values.shape != freqs.shape:
        msg = "'frequencies' and 'response' must be one-dimensional and of one length."
        raise ValueError(msg)
    # Checked on the whole arrays: a NaN frequency drops out of the range
    # selection silently, and a NaN response outside the range with it.
    if not (np.all(np.isfinite(freqs)) and np.all(np.isfinite(values))):
        msg = "'frequencies' and 'response' must be finite."
        raise ValueError(msg)
    low, high = _frequency_range(frequency_range_hz)
    inside = (freqs >= low) & (freqs <= high)
    if not np.any(inside):
        msg = "'frequency_range_hz' holds none of the frequencies."
        raise ValueError(msg)
    return ChannelMatchVerification(frequencies=freqs[inside], response=values[inside])
