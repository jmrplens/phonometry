#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Rotorcraft noise by the hemisphere method (ECAC Doc 32 / NORAH2).

The ECAC Doc 32 rotorcraft-noise method describes a helicopter's highly directive
source with a **noise hemisphere**: one-third-octave-band sound pressure levels on
a spherical grid of azimuth ``φ`` and polar angle ``θ`` at a fixed 60 m reference
distance (at ICAO reference atmospheric conditions). Placing that source at a
receiver adds the propagation adjustment ``ΔLp = ΔLs + ΔLa + ΔLg (+ ΔLd)``
(spherical spreading, atmospheric absorption, ground effect and — later — shielding).

This module provides the source and propagation primitives (clean-room, from the
NORAH2 guidance SC03.D1.5d, the basis of ECAC Doc 32):

* :func:`hemisphere_source_level` -- the interpolated source level ``L(fc, φ, θ)``
  from a :class:`RotorcraftHemisphere`, bilinear over the 10° grid (Eq. 13) with
  nearest-bin fill outside the measured coverage (Eq. 14/15).
* :func:`spherical_spreading_adjustment` -- ``ΔLs = −20·log10(r/60)`` (Eq. 24).
* :func:`atmospheric_adjustment` -- ``ΔLa = −α(f)·(r−60)`` with the ISO 9613-1
  pure-tone coefficient (Eq. 26/27), reusing :func:`~phonometry.air_absorption.air_attenuation`.
* :func:`ground_effect_adjustment` -- ``ΔLg`` for a point source over an impedance
  plane (Chien-Soroka, Eq. 28-35) with the Delany-Bazley one-parameter impedance
  and the CNOSSOS flow-resistivity classes.

Source (clean-room): ECAC Doc 32, 1st ed.; NORAH2 rotorcraft-noise modelling
guidance (EASA.2020.FC.06 SC03.D1.5d), §A.3-A.4. The atmospheric term is validated
against the guidance Table 4 (one-third-octave attenuation per km at ICAO
reference conditions).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ._internal.validation import require_non_negative, require_positive, require_positive_array

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import NDArray

#: Hemisphere reference distance, in metres (ECAC Doc 32 §A.3.2 / Eq. 24).
_RH = 60.0
#: Speed of sound at ICAO reference conditions, in m/s (Eq. 22).
_C = 346.1
#: CNOSSOS-EU flow resistivity by ground class, in Pa·s/m² (Doc 32 Table 5 / D1.5d Table 5).
_FLOW_RESISTIVITY = {
    "A": 12.5e3,   # very soft (snow, moss)
    "B": 31.5e3,   # soft forest floor
    "C": 80.0e3,   # uncompacted loose ground (turf, grass)
    "D": 200.0e3,  # normal uncompacted ground (pasture)
    "E": 500.0e3,  # compacted field and gravel
    "F": 2.0e6,    # compacted dense ground (gravel road, car park)
    "G": 20.0e6,   # hard surfaces (asphalt, concrete)
    "H": 200.0e6,  # very hard and dense (dense asphalt, water)
}


def spherical_spreading_adjustment(distance: float) -> float:
    """Spherical-spreading adjustment ``ΔLs`` of the hemisphere level (Eq. 24).

    The hemisphere levels are defined at the 60 m reference distance, so at slant
    distance ``r`` the geometric spreading adjustment is ``ΔLs = −20·log10(r/60)``.

    :param distance: Slant distance ``r`` from the rotorcraft to the observer, in
        metres (``> 0``).
    :return: The spreading adjustment ``ΔLs``, in dB (added to the level).
    :raises ValueError: If ``distance`` is not strictly positive.
    """
    r = require_positive(distance, "distance")
    return float(-20.0 * np.log10(r / _RH))


def atmospheric_adjustment(
    frequencies: "NDArray[np.float64] | list[float]",
    distance: float,
    *,
    temperature: float = 25.0,
    relative_humidity: float = 70.0,
    pressure: float = 101.325,
) -> "NDArray[np.float64]":
    """Atmospheric-absorption adjustment ``ΔLa`` of the hemisphere level (Eq. 26/27).

    The hemisphere already includes absorption out to the 60 m reference distance,
    so only the excess path ``r − 60`` is corrected: ``ΔLa = −α(f)·(r − 60)`` with
    the ISO 9613-1 pure-tone coefficient ``α`` (per ECAC Doc 32 Eq. 27, evaluated
    at the ICAO reference atmosphere by default). Reproduces the guidance Table 4.

    :param frequencies: One-third-octave-band centre frequencies, in Hz.
    :param distance: Slant distance ``r``, in metres (``>= 60``; below 60 m the
        adjustment is a small positive value, i.e. less absorption than the
        reference path).
    :param temperature: Air temperature, in °C (default 25 °C, ICAO reference).
    :param relative_humidity: Relative humidity, in % (default 70 %).
    :param pressure: Ambient pressure, in kPa (default 101.325).
    :return: The adjustment ``ΔLa`` per band, in dB (added to the level, ``<= 0``
        for ``r >= 60``).
    :raises ValueError: If ``distance`` is not strictly positive.
    """
    from .air_absorption import air_attenuation

    f = require_positive_array(frequencies, "frequencies")
    r = require_positive(distance, "distance")
    alpha = air_attenuation(f, temperature, relative_humidity, pressure, exact_midband=True)
    return np.asarray(-alpha * (r - _RH), dtype=np.float64)


def _delany_bazley_impedance(
    frequencies: "NDArray[np.float64]", flow_resistivity: float) -> "NDArray[np.complex128]":
    """Delany-Bazley one-parameter normalised surface impedance ``Zs`` (Eq. 35)."""
    ratio = frequencies / flow_resistivity
    real = 1.0 + 0.0511 * ratio ** (-0.754)
    imag = 0.0768 * ratio ** (-0.732)
    return np.asarray(real + 1j * imag, dtype=np.complex128)


def ground_effect_adjustment(
    frequencies: "NDArray[np.float64] | list[float]",
    source_height: float,
    receiver_height: float,
    horizontal_distance: float,
    *,
    flow_resistivity: "float | str" = "G",
) -> "NDArray[np.float64]":
    """Ground-effect adjustment ``ΔLg`` over an impedance plane (Eq. 28-35).

    A point source over a locally-reacting impedance ground produces interference
    between the direct and reflected rays. With the spherical reflection
    coefficient ``Q`` (Chien-Soroka) and the Delany-Bazley impedance,
    ``ΔLg = 10·log10{1 + (r1/r2)²|Q|² + 2(r1/r2)|Q|·I}`` (Eq. 29), where ``I``
    (Eq. 30) is the in-band interference factor.

    :param frequencies: One-third-octave-band centre frequencies, in Hz.
    :param source_height: Source height above the ground ``hs``, in metres
        (clamped to ``>= 0.1``).
    :param receiver_height: Receiver height above the ground ``hr``, in metres
        (clamped to ``>= 0.1``).
    :param horizontal_distance: Horizontal source-receiver distance ``dp``, in
        metres (``> 0``).
    :param flow_resistivity: Ground flow resistivity ``σ`` in Pa·s/m², or a
        CNOSSOS class letter ``"A"``-``"H"`` (default ``"G"``, hard surface).
    :return: The adjustment ``ΔLg`` per band, in dB (added to the level).
    :raises ValueError: If the inputs are invalid.
    """
    from scipy.special import wofz

    f = require_positive_array(frequencies, "frequencies")
    hs = max(require_non_negative(source_height, "source_height"), 0.1)
    hr = max(require_non_negative(receiver_height, "receiver_height"), 0.1)
    dp = require_positive(horizontal_distance, "horizontal_distance")
    if isinstance(flow_resistivity, str):
        key = flow_resistivity.strip().upper()
        if key not in _FLOW_RESISTIVITY:
            valid = ", ".join(sorted(_FLOW_RESISTIVITY))
            raise ValueError(
                f"'flow_resistivity' class must be one of {valid}, got {flow_resistivity!r}.")
        sigma = _FLOW_RESISTIVITY[key]
    else:
        sigma = require_positive(flow_resistivity, "flow_resistivity")

    r1 = np.hypot(dp, hs - hr)                    # direct path
    r2 = np.hypot(dp, hs + hr)                    # reflected path (image source)
    dr = r2 - r1                                  # path-length difference ΔR
    cos_xi = (hs + hr) / r2                       # incidence angle from the normal
    k = 2.0 * np.pi * f / _C

    zs = _delany_bazley_impedance(f, sigma)
    rp = (zs * cos_xi - 1.0) / (zs * cos_xi + 1.0)
    d_num = (1.0 + 1j) / 2.0 * np.sqrt(k * r2) * (1.0 / zs + cos_xi)
    f_loss = 1.0 + 1j * d_num * np.sqrt(np.pi) * wofz(d_num)   # F(d) = 1 + i·d·√π·w(d)
    q = rp + (1.0 - rp) * f_loss
    q_mag = np.abs(q)
    psi = np.angle(q)

    a = 0.727 * f * dr / _C
    sinc = np.sinc(a / np.pi)                                 # sin(a)/a, = 1 at a = 0
    inter = sinc * np.cos(6.325 * f * dr / _C + psi)          # I (Eq. 30)
    ratio = r1 / r2
    arg = 1.0 + ratio**2 * q_mag**2 + 2.0 * ratio * q_mag * inter
    return np.asarray(10.0 * np.log10(np.maximum(arg, 1e-15)), dtype=np.float64)


@dataclass(frozen=True)
class RotorcraftHemisphere:
    """A rotorcraft noise hemisphere (ECAC Doc 32 §A.3.2).

    One-third-octave-band sound pressure levels on a regular azimuth/polar grid at
    the 60 m reference distance (ICAO reference atmosphere). Missing bins (outside
    the measured coverage) are ``NaN`` and filled by nearest-bin extrapolation on
    lookup.

    :ivar frequencies: Band centre frequencies, in Hz, shape ``(F,)``.
    :ivar azimuth: Azimuth angles ``φ``, in degrees, shape ``(A,)`` (``-90``
        port … ``+90`` starboard).
    :ivar polar: Polar angles ``θ``, in degrees, shape ``(P,)`` (``0`` forward …
        ``180`` rearward).
    :ivar levels: Band levels, in dB, shape ``(A, P, F)``.
    :ivar distance: Reference distance, in metres (default 60).
    """

    frequencies: "NDArray[np.float64]"
    azimuth: "NDArray[np.float64]"
    polar: "NDArray[np.float64]"
    levels: "NDArray[np.float64]"
    distance: float = _RH

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the hemisphere directivity for one band (polar section)."""
        from ._plotting import plot_rotorcraft_hemisphere

        return plot_rotorcraft_hemisphere(self, ax=ax, **kwargs)


def _emission_unit_vector(azimuth_deg: float, polar_deg: float) -> "NDArray[np.float64]":
    """Unit emission direction (Eq. 11 with rh = 1): x=cosθ, y=sinθ·sinφ, z=sinθ·cosφ."""
    phi = np.radians(azimuth_deg)
    theta = np.radians(polar_deg)
    return np.array([np.cos(theta), np.sin(theta) * np.sin(phi), np.sin(theta) * np.cos(phi)])


def hemisphere_source_level(
    hemisphere: RotorcraftHemisphere, azimuth_deg: float, polar_deg: float,
) -> "NDArray[np.float64]":
    """Interpolated source level ``L(fc, φ, θ)`` from a hemisphere (Eq. 13-15).

    Bilinear interpolation in the energy domain over the four neighbouring
    azimuth/polar bins (Eq. 13). Outside the measured coverage (or where a
    neighbour is missing) the nearest filled bin by angular distance
    ``ρ = arccos(x·x_{m,n})`` is used (Eq. 14/15, constant-value extrapolation).

    :param hemisphere: The :class:`RotorcraftHemisphere` source description.
    :param azimuth_deg: Emission azimuth ``φ``, in degrees.
    :param polar_deg: Emission polar angle ``θ``, in degrees.
    :return: Band levels at ``(φ, θ)``, in dB, shape ``(F,)``.
    """
    az = np.asarray(hemisphere.azimuth, dtype=np.float64)
    po = np.asarray(hemisphere.polar, dtype=np.float64)
    lv = np.asarray(hemisphere.levels, dtype=np.float64)
    phi = float(np.clip(azimuth_deg, az[0], az[-1]))
    theta = float(np.clip(polar_deg, po[0], po[-1]))

    ia = int(np.clip(np.searchsorted(az, phi) - 1, 0, az.size - 2))
    ip = int(np.clip(np.searchsorted(po, theta) - 1, 0, po.size - 2))
    da = az[ia + 1] - az[ia]
    dp = po[ip + 1] - po[ip]
    wa = (phi - az[ia]) / da if da > 0.0 else 0.0
    wp = (theta - po[ip]) / dp if dp > 0.0 else 0.0
    corners = [(ia, ip, (1 - wa) * (1 - wp)), (ia + 1, ip, wa * (1 - wp)),
               (ia, ip + 1, (1 - wa) * wp), (ia + 1, ip + 1, wa * wp)]

    out = np.zeros(hemisphere.frequencies.shape, dtype=np.float64)
    energy = np.zeros_like(out)
    weight_ok = np.ones_like(out, dtype=bool)
    for i, j, w in corners:
        if w <= 0.0:
            continue
        band = lv[i, j, :]
        finite = np.isfinite(band)
        energy = np.where(finite, energy + w * 10.0 ** (band / 10.0), energy)
        weight_ok &= finite
    with np.errstate(divide="ignore"):
        out = np.where((energy > 0.0) & weight_ok, 10.0 * np.log10(energy), np.nan)

    # Nearest-bin fill (Eq. 14/15) for bands with any missing corner.
    missing = ~np.isfinite(out)
    if np.any(missing):
        target = _emission_unit_vector(phi, theta)
        best = _nearest_filled_bin(hemisphere, target, missing)
        out = np.where(missing, best, out)
    return out


def _nearest_filled_bin(
    hemisphere: RotorcraftHemisphere, target: "NDArray[np.float64]",
    missing: "NDArray[np.bool_]",
) -> "NDArray[np.float64]":
    """Angularly-nearest filled bin per band (Eq. 14/15, ρ=arccos(x·x_mn)).

    Where several bins are equally near (common on symmetric grids), their
    energetic average is taken, as required by the guidance under Eq. 14/15.
    """
    az = np.asarray(hemisphere.azimuth, dtype=np.float64)
    po = np.asarray(hemisphere.polar, dtype=np.float64)
    lv = np.asarray(hemisphere.levels, dtype=np.float64)
    tol = 1e-9
    best_rho = np.full(hemisphere.frequencies.shape, np.inf, dtype=np.float64)
    energy = np.zeros(hemisphere.frequencies.shape, dtype=np.float64)
    count = np.zeros(hemisphere.frequencies.shape, dtype=np.float64)
    for i in range(az.size):
        for j in range(po.size):
            band = lv[i, j, :]
            finite = np.isfinite(band) & missing
            if not np.any(finite):
                continue
            vec = _emission_unit_vector(az[i], po[j])
            rho = float(np.arccos(np.clip(np.dot(target, vec), -1.0, 1.0)))
            e = 10.0 ** (np.where(finite, band, 0.0) / 10.0)
            closer = finite & (rho < best_rho - tol)      # strictly nearer: reset
            best_rho = np.where(closer, rho, best_rho)
            energy = np.where(closer, e, energy)
            count = np.where(closer, 1.0, count)
            tie = finite & ~closer & (np.abs(rho - best_rho) <= tol)  # equidistant: accumulate
            energy = np.where(tie, energy + e, energy)
            count = np.where(tie, count + 1.0, count)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(count > 0.0, 10.0 * np.log10(energy / count), np.nan)
