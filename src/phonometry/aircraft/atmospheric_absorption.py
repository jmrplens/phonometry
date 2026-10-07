#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""One-third-octave-band atmospheric absorption for aircraft noise (SAE ARP 5534 and 866A).

Aircraft noise certification (14 CFR Part 36, ICAO Annex 16 Vol. I) works with
one-third-octave-band spectra, and correcting a measured flyover to reference
atmospheric conditions requires the band attenuation over the propagation path.
Two SAE practices give it.

* :func:`sae_band_attenuation` -- SAE ARP 5534, the current practice. Its
  pure-tone coefficient (Eqs. 1-6) is the ISO 9613-1 one, Eqs. 1-3 repeating
  :func:`~phonometry.environment.propagation.air_absorption.air_attenuation`
  term for term, except for the saturation vapour pressure: Eqs. 5-6 write it
  in the longer form of ANSI S1.26, which gives a molar concentration of water
  vapour 4.5 parts in 100 000 below the ISO 9613-1 Annex B formula at
  10 °C. The **SAE Method** (§3.2.2) then turns the pure-tone mid-band
  path-length attenuation into the one-third-octave-band attenuation and stays
  consistent with the ISO/ANSI Exact Method well beyond the 50 dB limit of the
  older Approximate Method. The result is an :class:`AircraftBandAttenuation`
  with a ``.plot()``.
* :func:`arp866a_attenuation` -- SAE ARP 866A (1975), the legacy practice that
  ECAC Doc 29 Vol. 2 Appendix D still offers for recalculating NPD data, in the
  form ISO 3891:1978 Annex A gives it: an attenuation coefficient per band, in
  decibels per 100 m, independent of pressure and of path length, evaluated at
  the band centre up to 4 kHz and at the lower band edge above. The result is an
  :class:`Arp866aAttenuation` with a ``.plot()``.

Sources (clean-room, implemented from the documents): SAE ARP 5534 (2021),
*Application of Pure-Tone Atmospheric Absorption Losses to One-Third-Octave-Band
Data*, Eqs. 1-10; ISO 3891:1978, *Acoustics -- Procedure for describing aircraft
noise heard on the ground*, Annex A (A.1, A.2, Tables 1 and 2), which transcribes
SAE ARP 866A. Both are checked against ECAC Doc 29 5th ed. Vol. 2 Appendix D,
Tables D-3b and D-3c, and ARP 866A against ISO 3891 Table 10 as well.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.frozen import OwnsArrays, read_only
from .._internal.validation import (
    require_above_absolute_zero,
    require_choice,
    require_finite,
    require_non_negative,
    require_positive_array,
    require_ranks,
    require_same_length,
)
from ..environment.propagation.air_absorption import (
    _EIGHT_686,
    _KELVIN,
    _exact_midband,
    _pure_tone_terms,
    _validate,
)
from .certification import NOY_BANDS

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

# SAE Method regression constants (ARP 5534 §3.2.2, Eqs. 7-8).
_A = 0.867942
_B = 0.111761
_C = 0.95824
_D = 0.008191
_E = 1.6
_F = 9.2
_G = 0.765
#: Mid-band attenuation (dB) at which the piecewise SAE Method switches branch.
_SPLIT_DB = 150.0
#: Triple-point isotherm temperature ``T01`` of ARP 5534 Eq. 6, in kelvins.
_T01_K = 273.16


def _sae_band(delta_t: NDArray[np.float64]) -> NDArray[np.float64]:
    """Map pure-tone mid-band attenuation ``δ_t`` (dB) to band attenuation (dB)."""
    # np.where evaluates both branches; clamp the low branch's input to the split
    # point so its power base stays positive (it turns negative near 1209 dB) and
    # never produces a NaN for the discarded δ_t >= 150 dB samples.
    dt_low = np.minimum(delta_t, _SPLIT_DB)
    low = _A * dt_low * (1.0 + _B * (_C - _D * dt_low)) ** _E
    high = _F + _G * delta_t
    return np.asarray(np.where(delta_t < _SPLIT_DB, low, high), dtype=np.float64)


def _arp5534_saturation_ratio(temperature_k: float) -> float:
    r"""Saturation vapour pressure over the reference pressure (ARP 5534 Eqs. 5-6).

    :math:`p_\mathrm{sat}/p_\mathrm{r} = 10^V` with

    .. math::

       V = 10.79586\,[1 - T_{01}/T] - 5.02808 \log_{10}(T/T_{01})
       + 1.50474 \times 10^{-4}\,\{1 - 10^{-8.29692\,[T/T_{01} - 1]}\}
       + 0.42873 \times 10^{-3}\,\{-1 + 10^{4.76955\,[1 - T_{01}/T]}\}
       - 2.2195983

    and :math:`T_{01} = 273.16` K, as ARP 5534 (2021) prints it on page 8.
    """
    ratio = temperature_k / _T01_K
    inverse = _T01_K / temperature_k
    v = (
        10.79586 * (1.0 - inverse)
        - 5.02808 * np.log10(ratio)
        + 1.50474e-4 * (1.0 - 10.0 ** (-8.29692 * (ratio - 1.0)))
        + 0.42873e-3 * (-1.0 + 10.0 ** (4.76955 * (1.0 - inverse)))
        - 2.2195983
    )
    return float(10.0**v)


def _arp5534_coefficient(
    frequencies: NDArray[np.float64],
    temperature_c: float,
    relative_humidity_percent: float,
    atmospheric_pressure_kpa: float,
) -> NDArray[np.float64]:
    """Pure-tone coefficient ``α`` at the exact mid-band frequencies (ARP 5534 Eqs. 1-6, 10).

    Eqs. 1-4 are ISO 9613-1's Eqs. (3)-(5) and its psychrometric conversion,
    so the shared terms are evaluated by the ISO 9613-1 module with the
    saturation vapour pressure of Eqs. 5-6 put in place of its Annex B form.
    The inputs are validated, and warned about, as ISO 9613-1 does.

    :return: ``α`` per band, in dB/m.
    """
    _validate(
        frequencies, temperature_c, relative_humidity_percent, atmospheric_pressure_kpa
    )
    temperature_k = temperature_c + _KELVIN
    f2, bracket = _pure_tone_terms(
        _exact_midband(frequencies),
        temperature_k,
        relative_humidity_percent,
        atmospheric_pressure_kpa,
        saturation_ratio=_arp5534_saturation_ratio(temperature_k),
    )
    return np.asarray(_EIGHT_686 * f2 * bracket, dtype=np.float64)


@dataclass(frozen=True)
class AircraftBandAttenuation(OwnsArrays):
    r"""One-third-octave-band atmospheric attenuation over a path (SAE ARP 5534).

    :ivar frequencies: Nominal one-third-octave-band centre frequencies, in Hz.
    :ivar band_attenuation: SAE-Method band attenuation ``δ_B`` per band, in dB.
    :ivar midband_attenuation: Pure-tone mid-band path-length attenuation
        :math:`\delta_\mathrm{t} = \alpha \cdot s` per band, in dB (ARP 5534
        Eqs. 1-6 coefficient).
    :ivar coefficient: Pure-tone mid-band attenuation coefficient ``α`` per band,
        in dB/m.
    :ivar path_length: Propagation path length ``s``, in metres.
    :ivar temperature_c: Air temperature, in degrees Celsius.
    :ivar relative_humidity_percent: Relative humidity, in percent.
    :ivar atmospheric_pressure_kpa: Ambient atmospheric pressure, in kPa.
    """

    frequencies: NDArray[np.float64]
    band_attenuation: NDArray[np.float64]
    midband_attenuation: NDArray[np.float64]
    coefficient: NDArray[np.float64]
    path_length: float
    temperature_c: float
    relative_humidity_percent: float
    atmospheric_pressure_kpa: float

    def __post_init__(self) -> None:
        """Reject an attenuation whose arrays do not all run over the same bands.

        Every array here is one value per one-third-octave band of the same
        spectrum: the band attenuation the certification correction subtracts,
        the pure-tone mid-band attenuation it was regressed from, and the
        coefficient behind that. Which field is wrong decides how loud the
        mistake is. The figure draws ``band_attenuation`` and
        ``midband_attenuation`` against ``frequencies``, so any disagreement
        among those three stops it, with matplotlib's complaint about an x and
        a y that name neither field. ``coefficient`` reaches no figure and no
        reader in this library: it leaves as dB/m for the caller to multiply
        by a path length, so a wrong length here passes in silence, and one
        collapsed to a single value is broadcast by numpy over the caller's
        whole spectrum, correcting every band of a measured flyover by one
        band's attenuation and handing back ordinary dB numbers. An extra
        axis passes just as quietly: a column of the same coefficients counts
        one entry per band on its first axis, so every length agrees, and the
        caller's correction comes back as a band-by-band matrix instead of a
        spectrum.

        :raises ValueError: if a per-band array disagrees with the rest, or
            carries an axis beyond the band one.
        """
        require_ranks(
            self,
            frequencies=1,
            band_attenuation=1,
            midband_attenuation=1,
            coefficient=1,
        )
        require_same_length(
            self,
            "frequencies",
            "band_attenuation",
            "midband_attenuation",
            "coefficient",
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the band and pure-tone mid-band attenuation versus frequency."""
        from .._i18n import check_language
        from .._plot.aircraft import plot_aircraft_band_attenuation

        return plot_aircraft_band_attenuation(
            self, ax=ax, language=check_language(language), **kwargs
        )


def sae_band_attenuation(
    frequencies: NDArray[np.float64] | list[float],
    path_length: float,
    *,
    temperature_c: float = 25.0,
    relative_humidity_percent: float = 70.0,
    atmospheric_pressure_kpa: float = 101.325,
) -> AircraftBandAttenuation:
    r"""One-third-octave-band atmospheric attenuation (SAE ARP 5534, SAE Method).

    Computes the pure-tone attenuation coefficient at each band's exact mid-band
    frequency (Eqs. 1-6 and 10, :math:`f_{\mathrm{m},i} = 10^{i/10}`), forms the
    mid-band path-length attenuation :math:`\delta_\mathrm{t} = \alpha \cdot s`
    and maps it to the band attenuation ``δ_B`` with the SAE-Method regression
    (Eqs. 7-8). The coefficient is ISO 9613-1's with the saturation vapour
    pressure of Eqs. 5-6, which is what reproduces ECAC Doc 29 Vol. 2 Table
    D-3c to the last printed digit in all 240 of its cells; the ISO 9613-1
    Annex B form leaves 57 of them up to 0.036 dB off.

    :param frequencies: Nominal one-third-octave-band centre frequencies, in Hz
        (standard range 50 Hz-10 kHz; the method extends to 25 Hz-20 kHz).
    :param path_length: Propagation path length ``s``, in metres (``>= 0``).
    :param temperature_c: Air temperature, in degrees Celsius (SAE window
        ~6-32 °C; default 25 °C, the ARP 5534 reference point).
    :param relative_humidity_percent: Relative humidity, in percent (SAE window
        ~20-95 %; default 70 %).
    :param atmospheric_pressure_kpa: Ambient atmospheric pressure, in kPa (default 101.325).
    :return: An :class:`AircraftBandAttenuation`.
    :raises ValueError: If the inputs are invalid.
    """
    f = require_positive_array(frequencies, "frequencies")
    s = require_non_negative(path_length, "path_length")

    alpha = _arp5534_coefficient(
        f, temperature_c, relative_humidity_percent, atmospheric_pressure_kpa
    )
    delta_t = alpha * s
    delta_b = _sae_band(delta_t)
    return AircraftBandAttenuation(
        frequencies=f,
        band_attenuation=delta_b,
        midband_attenuation=np.asarray(delta_t, dtype=np.float64),
        coefficient=alpha,
        path_length=s,
        temperature_c=float(temperature_c),
        relative_humidity_percent=float(relative_humidity_percent),
        atmospheric_pressure_kpa=float(atmospheric_pressure_kpa),
    )


# --------------------------------------------------------------------------- #
# SAE ARP 866A, as ISO 3891:1978 Annex A gives it
# --------------------------------------------------------------------------- #

#: ISO 3891:1978 Annex A, Table 1: the tabulated values of ``δ`` (left) and of
#: ``η(δ)`` (right), the two column pairs of the table read as one sequence.
#: Beyond ``δ = 10`` the table stops at ``η = 0.200``, the value it has held
#: since ``δ = 6.5``.
_ETA_DELTA = read_only(
    np.array(
        [
            0.00,
            0.25,
            0.50,
            0.60,
            0.70,
            0.80,
            0.90,
            1.00,
            1.10,
            1.20,
            1.30,
            1.50,
            1.70,
            2.00,
            2.30,
            2.50,
            2.80,
            3.00,
            3.30,
            3.60,
            4.15,
            4.45,
            4.80,
            5.25,
            5.70,
            6.05,
            6.50,
            7.00,
            10.00,
        ]
    )
)
_ETA = read_only(
    np.array(
        [
            0.000,
            0.315,
            0.700,
            0.840,
            0.930,
            0.975,
            0.996,
            1.000,
            0.970,
            0.900,
            0.840,
            0.750,
            0.670,
            0.570,
            0.495,
            0.450,
            0.400,
            0.370,
            0.330,
            0.300,
            0.260,
            0.245,
            0.230,
            0.220,
            0.210,
            0.205,
            0.200,
            0.200,
            0.200,
        ]
    )
)
#: The ``δ`` from which Table 1 prints ``η = 0.200`` and nothing else (at 6.50,
#: 7.00 and 10.00): past it ``η`` is flat, whatever the interpolation.
_ETA_PLATEAU_DELTA = 6.50
#: ISO 3891:1978 Annex A, Table 2: the frequency ``f0`` at which the formula of
#: A.2 is evaluated for each nominal band of :data:`NOY_BANDS` (50 Hz to
#: 10 kHz). A.1 sets it at the band centre up to 4 kHz and at the lower band
#: edge above, which Table 2 prints rounded: 4 500, 5 600, 7 100 and 9 000 Hz.
_F0_HZ = read_only(
    np.array(
        [
            50.0,
            63.0,
            80.0,
            100.0,
            125.0,
            160.0,
            200.0,
            250.0,
            315.0,
            400.0,
            500.0,
            630.0,
            800.0,
            1000.0,
            1250.0,
            1600.0,
            2000.0,
            2500.0,
            3150.0,
            4000.0,
            4500.0,
            5600.0,
            7100.0,
            9000.0,
        ]
    )
)
#: Band index ``10 lg(f/1 kHz)`` of the first band of Table 2 (50 Hz).
_FIRST_BAND_INDEX = -13
#: Full-scale relative humidity, in percent.
_MAX_RELATIVE_HUMIDITY_PERCENT = 100.0


def _table2_rows(frequencies: NDArray[np.float64]) -> NDArray[np.intp]:
    r"""Row of Table 2 for each frequency, naming any band the table does not list.

    A frequency is read as the one-third-octave band whose index
    :math:`10 \lg(f/1\,\mathrm{kHz})` rounds to it, so a nominal centre (63 Hz)
    and an exact one (63.0957 Hz) name the same band.

    :raises ValueError: for a band outside the 50 Hz to 10 kHz of Table 2.
    """
    index = np.round(10.0 * np.log10(frequencies / 1000.0)).astype(np.intp)
    rows = index - _FIRST_BAND_INDEX
    outside = (rows < 0) | (rows >= _F0_HZ.size)
    if np.any(outside):
        msg = (
            "'frequencies_hz' must name one-third-octave bands from 50 Hz to "
            "10 kHz, the bands ISO 3891:1978 Annex A Table 2 gives f0 for; got "
            f"{frequencies[outside].tolist()}."
        )
        raise ValueError(msg)
    return np.asarray(rows, dtype=np.intp)


@dataclass(frozen=True)
class Arp866aAttenuation(OwnsArrays):
    r"""Atmospheric attenuation coefficient per band by SAE ARP 866A (ISO 3891 Annex A).

    :ivar frequencies_hz: Nominal one-third-octave-band centre frequencies, in
        Hz, one per band.
    :ivar evaluation_frequencies_hz: The frequency ``f0`` of ISO 3891 Table 2 at
        which each band is evaluated, in Hz: the centre up to 4 kHz, the rounded
        lower band edge above.
    :ivar delta: The humidity-and-temperature argument ``δ`` of A.2 per band,
        dimensionless.
    :ivar eta: ``η(δ)`` per band, interpolated in Table 1.
    :ivar coefficient_db_per_100m: The attenuation coefficient ``α`` per band,
        in decibels per 100 m.
    :ivar temperature_c: Air temperature ``θ``, in degrees Celsius.
    :ivar relative_humidity_percent: Relative humidity ``RH``, in percent.
    :ivar eta_interpolation: How ``η`` was read between the entries of Table 1,
        ``"quadratic"`` or ``"linear"`` (see :func:`arp866a_attenuation`).
    """

    frequencies_hz: NDArray[np.float64]
    evaluation_frequencies_hz: NDArray[np.float64]
    delta: NDArray[np.float64]
    eta: NDArray[np.float64]
    coefficient_db_per_100m: NDArray[np.float64]
    temperature_c: float
    relative_humidity_percent: float
    eta_interpolation: str

    def __post_init__(self) -> None:
        """Reject a coefficient set whose arrays do not all run over the same bands.

        Each array is one value per band, and :meth:`path_attenuation_db`
        multiplies the coefficient by a path length for the caller to subtract
        band by band from a spectrum: a coefficient array one short, or one
        with an extra axis, would be broadcast over that spectrum without a
        word.

        :raises ValueError: if a per-band array disagrees with the rest, or
            carries an axis beyond the band one.
        """
        require_ranks(
            self,
            frequencies_hz=1,
            evaluation_frequencies_hz=1,
            delta=1,
            eta=1,
            coefficient_db_per_100m=1,
        )
        require_same_length(
            self,
            "frequencies_hz",
            "evaluation_frequencies_hz",
            "delta",
            "eta",
            "coefficient_db_per_100m",
        )

    def path_attenuation_db(
        self, path_length_m: float | ArrayLike
    ) -> NDArray[np.float64]:
        r"""Attenuation over a path, :math:`\alpha \cdot s / 100`, in dB.

        ARP 866A gives a rate, so the attenuation is proportional to the path
        length and does not depend on the pressure, unlike SAE ARP 5534.

        :param path_length_m: Path length ``s``, in metres: one length, or a
            1-D sequence of them.
        :return: One value per band for a single length, or an array of shape
            ``(bands, lengths)``.
        :raises ValueError: if a length is negative or not finite.
        """
        s = np.asarray(path_length_m, dtype=np.float64)
        if s.ndim > 1 or not np.all(np.isfinite(s)) or np.any(s < 0.0):
            msg = "'path_length_m' must be one non-negative length or a 1-D sequence of them."
            raise ValueError(msg)
        return np.asarray(
            np.multiply.outer(self.coefficient_db_per_100m / 100.0, s),
            dtype=np.float64,
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the attenuation coefficient versus frequency."""
        from .._i18n import check_language
        from .._plot.aircraft import plot_arp866a_attenuation

        return plot_arp866a_attenuation(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _eta_quadratic(delta: NDArray[np.float64]) -> NDArray[np.float64]:
    """``η(δ)`` by the three-point quadratic that reproduces ISO 3891 Table 10.

    For ``δ`` between the Table 1 entries ``δ_i`` and ``δ_{i+1}`` the parabola
    through the entries ``i - 1``, ``i`` and ``i + 1`` (the first three below
    the second entry). From ``δ = 6.50`` on, where Table 1 prints 0.200 at every
    entry, ``η = 0.200``: the parabola through 6.05, 6.50 and 7.00 would dip
    below it between the last two, which neither Table 1 nor the printed
    tables support. Of the three-point forms, this is the one that reproduces
    all 264 cells of ISO 3891 Table 10 to the printed digit, where linear
    interpolation misses 11.
    """
    last = _ETA_DELTA.size - 1
    below = np.searchsorted(_ETA_DELTA, delta, side="right") - 1
    first = np.clip(below - 1, 0, last - 2)
    x0, x1, x2 = _ETA_DELTA[first], _ETA_DELTA[first + 1], _ETA_DELTA[first + 2]
    y0, y1, y2 = _ETA[first], _ETA[first + 1], _ETA[first + 2]
    eta = (
        y0 * (delta - x1) * (delta - x2) / ((x0 - x1) * (x0 - x2))
        + y1 * (delta - x0) * (delta - x2) / ((x1 - x0) * (x1 - x2))
        + y2 * (delta - x0) * (delta - x1) / ((x2 - x0) * (x2 - x1))
    )
    return np.asarray(np.where(delta >= _ETA_PLATEAU_DELTA, _ETA[last], eta))


#: The two readings of the interpolation Table 1 asks for (see
#: :func:`arp866a_attenuation`).
_ETA_INTERPOLATION = ("quadratic", "linear")


def arp866a_attenuation(
    frequencies_hz: ArrayLike,
    *,
    temperature_c: float,
    relative_humidity_percent: float,
    eta_interpolation: str = "quadratic",
) -> Arp866aAttenuation:
    r"""One-third-octave-band attenuation coefficient by SAE ARP 866A (ISO 3891 Annex A).

    The formula of ISO 3891:1978 A.2, in decibels per 100 m:

    .. math::

       \alpha = 10^{2.05 \log_{10}(f_0/1000) + 1.1394 \times 10^{-3}\,\theta
       - 1.916984}
       + \eta(\delta) \times 10^{\log_{10} f_0 + 8.42994 \times 10^{-3}\,\theta
       - 2.755624}

    .. math::

       \delta = \sqrt{\frac{1010}{f_0}} \times 10^{\log_{10} RH - 1.328924
       + 3.179768 \times 10^{-2}\,\theta - 2.173716 \times 10^{-4}\,\theta^2
       + 1.7496 \times 10^{-6}\,\theta^3}

    with ``θ`` in degrees Celsius, ``RH`` in percent and ``f0`` from Table 2.

    ``η(δ)`` comes from Table 1, whose note says "A form of quadratic
    interpolation shall be used where necessary" without saying which, and
    the two documents that print this attenuation read it differently.
    ``"quadratic"`` (the default) is the parabola through three neighbouring
    entries of Table 1 that reproduces every cell of ISO 3891 Table 10
    (80 %, -10 °C to 40 °C) to the printed digit, where linear interpolation
    misses 11 of the 264. ``"linear"`` reproduces ECAC Doc 29 Vol. 2 Table
    D-3b (10 °C, 80 %, over the ten NPD distances): 208 of its 240 cells to the
    printed digit and all 240 within half a unit of that digit plus 7 parts per
    million, where the quadratic leaves up to 1.2 dB at 25000 ft; it is the
    form :func:`~phonometry.aircraft.npd_atmosphere.npd_atmosphere_increment`
    uses. The two part only where ``δ`` falls in the curved part of Table 1,
    below 6.50; from there on both hold ``η`` at 0.200. ISO 3891 Table 9
    (70 %) is not reproduced as closely as Table 10: the quadratic misses 15
    of its 264 cells by one printed unit, seven where it contradicts Table 10
    (both humidities give the same value there; see the errata register) and
    eight more, each within 0.014 dB/100 m of a rounding boundary.

    A.2 states the range the formula was measured over: from 2 °C to 30 °C (on
    the print the mark before the 2 is unclear and may be a minus sign) and
    from 30 % to 90 %. Its Tables 3 to 12 print the formula from -10 °C to
    40 °C and from 10 % to 100 %.

    :param frequencies_hz: One-third-octave bands, by nominal or exact centre
        frequency in Hz, from 50 Hz to 10 kHz.
    :param temperature_c: Air temperature ``θ``, in degrees Celsius.
    :param relative_humidity_percent: Relative humidity ``RH``, in percent
        (0 to 100).
    :param eta_interpolation: ``"quadratic"`` (default, ISO 3891) or
        ``"linear"`` (ECAC Doc 29 Appendix D).
    :return: An :class:`Arp866aAttenuation`.
    :raises ValueError: for a band outside Table 2, a temperature at or below
        absolute zero, a humidity outside 0 % to 100 %, or an unknown
        interpolation.
    """
    f = require_positive_array(frequencies_hz, "frequencies_hz")
    interpolation = require_choice(
        eta_interpolation, "eta_interpolation", _ETA_INTERPOLATION
    )
    rows = _table2_rows(f)
    theta = require_above_absolute_zero(
        require_finite(temperature_c, "temperature_c"), "temperature_c"
    )
    rh = require_finite(relative_humidity_percent, "relative_humidity_percent")
    if not 0.0 <= rh <= _MAX_RELATIVE_HUMIDITY_PERCENT:
        msg = "'relative_humidity_percent' must be within [0, 100] %."
        raise ValueError(msg)

    f0 = np.asarray(_F0_HZ[rows], dtype=np.float64)
    if rh > 0.0:
        exponent = (
            np.log10(rh)
            - 1.328924
            + 3.179768e-2 * theta
            - 2.173716e-4 * theta**2
            + 1.7496e-6 * theta**3
        )
        delta = np.sqrt(1010.0 / f0) * 10.0**exponent
    else:
        # log10(0) is -inf and the power is 0; written out so no warning fires.
        delta = np.zeros_like(f0)
    eta = (
        _eta_quadratic(delta)
        if interpolation == "quadratic"
        else np.interp(delta, _ETA_DELTA, _ETA)
    )
    alpha = 10.0 ** (
        2.05 * np.log10(f0 / 1000.0) + 1.1394e-3 * theta - 1.916984
    ) + eta * 10.0 ** (np.log10(f0) + 8.42994e-3 * theta - 2.755624)
    nominal = np.asarray(NOY_BANDS[rows], dtype=np.float64)
    return Arp866aAttenuation(
        frequencies_hz=nominal,
        evaluation_frequencies_hz=f0,
        delta=np.asarray(delta, dtype=np.float64),
        eta=np.asarray(eta, dtype=np.float64),
        coefficient_db_per_100m=np.asarray(alpha, dtype=np.float64),
        temperature_c=theta,
        relative_humidity_percent=rh,
        eta_interpolation=interpolation,
    )
