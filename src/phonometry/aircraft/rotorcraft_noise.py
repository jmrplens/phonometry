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
  pure-tone coefficient (Eq. 26/27), reusing
  :func:`~phonometry.environmental.air_absorption.air_attenuation`.
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

from .._internal.validation import require_non_negative, require_positive, require_positive_array

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


def spherical_spreading_adjustment(
    distance: float, *, reference_distance: float = _RH,
) -> float:
    """Spherical-spreading adjustment ``ΔLs`` of the hemisphere level (Eq. 24).

    The hemisphere levels are defined at the reference distance ``rh`` (60 m in
    the standard database), so at slant distance ``r`` the geometric spreading
    adjustment is ``ΔLs = −20·log10(r/rh)``.

    :param distance: Slant distance ``r`` from the rotorcraft to the observer, in
        metres (``> 0``).
    :param reference_distance: Hemisphere reference distance ``rh``, in metres
        (default 60). Pass :attr:`RotorcraftHemisphere.distance` when the data
        uses a non-standard polar distance (e.g. 70 m hover rings).
    :return: The spreading adjustment ``ΔLs``, in dB (added to the level).
    :raises ValueError: If a distance is not strictly positive.
    """
    r = require_positive(distance, "distance")
    rh = require_positive(reference_distance, "reference_distance")
    return float(-20.0 * np.log10(r / rh))


def atmospheric_adjustment(
    frequencies: "NDArray[np.float64] | list[float]",
    distance: float,
    *,
    temperature: float = 25.0,
    relative_humidity: float = 70.0,
    pressure: float = 101.325,
    reference_distance: float = _RH,
) -> "NDArray[np.float64]":
    """Atmospheric-absorption adjustment ``ΔLa`` of the hemisphere level (Eq. 26/27).

    The hemisphere already includes absorption out to the reference distance
    ``rh``, so only the excess path ``r − rh`` is corrected:
    ``ΔLa = −α(f)·(r − rh)`` with the ISO 9613-1 pure-tone coefficient ``α``
    evaluated at the exact band centre (Eq. 26/27, ICAO reference atmosphere by
    default). This matches the guidance Eq. 27 to 0.02 dB/km and the NORAH2
    reference implementation. The guidance's alternative per-band mapping (SAE
    method by Rickley et al., its Table 4) coincides below 3.15 kHz and deviates
    by up to 2.2 dB/km at 8-10 kHz; for a path-dependent band mapping use
    :func:`~phonometry.aircraft.atmospheric_absorption.sae_band_attenuation`.

    .. note::
        The printed guidance Eq. 27 pairs the coefficient ``6.6928e-6`` with
        ``fr,O = 630.7`` Hz, which evaluates to nonsense (14.3 dB/km at 500 Hz
        against Table 4's 3.1). The physically correct pairing (``6.6928e-6``
        with the oxygen relaxation frequency, ``1.3415e-6`` with 630.7 Hz)
        reproduces Table 4 and this implementation to 0.02 dB/km; do not
        "fix" the code by transcribing the typo.

    Bands below the 50 Hz floor of the ISO 9613-1 tabulation (the NORAH grid
    starts at 10 Hz) use the same analytic formulas; the advisory out-of-range
    warning is suppressed because ``α`` is negligible there (Table 4 lists
    0.0 dB/km for every band up to 50 Hz). The suppression only applies while
    every band stays within the 10 kHz top of the NORAH grid; above that the
    advisory warning propagates, since ``α`` is large and extrapolated.

    :param frequencies: One-third-octave-band centre frequencies, in Hz.
    :param distance: Slant distance ``r``, in metres (``>= rh``; below ``rh``
        the adjustment is a small positive value, i.e. less absorption than the
        reference path).
    :param temperature: Air temperature, in °C (default 25 °C, ICAO reference).
    :param relative_humidity: Relative humidity, in % (default 70 %).
    :param pressure: Ambient pressure, in kPa (default 101.325).
    :param reference_distance: Hemisphere reference distance ``rh``, in metres
        (default 60). Pass :attr:`RotorcraftHemisphere.distance` when the data
        uses a non-standard polar distance.
    :return: The adjustment ``ΔLa`` per band, in dB (added to the level, ``<= 0``
        for ``r >= rh``).
    :raises ValueError: If a distance is not strictly positive.
    """
    import warnings

    from ..environmental.air_absorption import AtmosphericAbsorptionWarning, air_attenuation

    f = require_positive_array(frequencies, "frequencies")
    r = require_positive(distance, "distance")
    rh = require_positive(reference_distance, "reference_distance")
    with warnings.catch_warnings():
        if f.max() <= 10000.0:
            warnings.filterwarnings(
                "ignore", message="One or more frequencies are outside",
                category=AtmosphericAbsorptionWarning)
        alpha = air_attenuation(f, temperature, relative_humidity, pressure, exact_midband=True)
    return np.asarray(-alpha * (r - rh), dtype=np.float64)


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
        CNOSSOS class letter ``"A"``-``"H"``. The default ``"G"`` (20e6, hard
        surfaces) is the CNOSSOS class covering the paved surroundings typical
        of heliports; the guidance's own suggestions, concrete ``σ = 65e6`` for
        city areas and grass ``σ = 200e3`` for rural areas (§A.4.3), can be
        passed as numeric values.
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
    :ivar distance: Reference distance, in metres (default 60). The standard
        NORAH database uses 60 m; when the data uses another polar distance
        (e.g. 70 m hover rings), pass this value as ``reference_distance`` to
        :func:`spherical_spreading_adjustment` and :func:`atmospheric_adjustment`
        so the propagation chain honours it.
    """

    frequencies: "NDArray[np.float64]"
    azimuth: "NDArray[np.float64]"
    polar: "NDArray[np.float64]"
    levels: "NDArray[np.float64]"
    distance: float = _RH

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the hemisphere directivity for one band (polar section)."""
        from .._plot.aircraft import plot_rotorcraft_hemisphere

        return plot_rotorcraft_hemisphere(self, ax=ax, **kwargs)

    def _filled(self) -> "NDArray[np.float64]":
        """The gap-filled level grid (Eq. 14/15), computed once and cached.

        The cache relies on the frozen-dataclass contract: mutating the
        ``levels`` array in place after the first lookup leaves it stale.
        """
        cached = self.__dict__.get("_filled_cache")
        if cached is None:
            cached = _fill_grid(
                np.asarray(self.azimuth, dtype=np.float64),
                np.asarray(self.polar, dtype=np.float64),
                np.asarray(self.levels, dtype=np.float64))
            object.__setattr__(self, "_filled_cache", cached)
        return np.asarray(cached, dtype=np.float64)


def hemisphere_source_level(
    hemisphere: RotorcraftHemisphere, azimuth_deg: float, polar_deg: float,
) -> "NDArray[np.float64]":
    """Interpolated source level ``L(fc, φ, θ)`` from a hemisphere (Eq. 13-15).

    The grid is first gap-filled by nearest-bin constant-value extrapolation
    (Eq. 14/15, computed once per hemisphere and cached), then the query is a
    bilinear interpolation in the energy domain over the four neighbouring
    azimuth/polar bins (Eq. 13). Filling the grid before interpolating keeps
    partially-measured cells continuous with their fully-measured neighbours
    (the valid corners still contribute) instead of snapping to a single bin.

    Queries outside the grid clamp to the boundary node and edge-interpolate;
    Eq. 14/15 taken literally would return the single nearest node, which
    coincides on the boundary nodes but is discontinuous alongside them, so the
    smoother clamp is intentional. Bands with no filled bin anywhere in the
    grid return ``NaN``.

    :param hemisphere: The :class:`RotorcraftHemisphere` source description.
    :param azimuth_deg: Emission azimuth ``φ``, in degrees.
    :param polar_deg: Emission polar angle ``θ``, in degrees.
    :return: Band levels at ``(φ, θ)``, in dB, shape ``(F,)``.
    """
    az = np.asarray(hemisphere.azimuth, dtype=np.float64)
    po = np.asarray(hemisphere.polar, dtype=np.float64)
    lv = hemisphere._filled()
    phi = float(np.clip(azimuth_deg, az[0], az[-1]))
    theta = float(np.clip(polar_deg, po[0], po[-1]))

    ia, wa = _axis_cell(az, phi)
    ip, wp = _axis_cell(po, theta)
    corners = [(ia, ip, (1 - wa) * (1 - wp)), (ia + 1, ip, wa * (1 - wp)),
               (ia, ip + 1, (1 - wa) * wp), (ia + 1, ip + 1, wa * wp)]

    energy = np.zeros(hemisphere.frequencies.shape, dtype=np.float64)
    for i, j, w in corners:
        if w <= 0.0:
            continue
        energy = energy + w * 10.0 ** (lv[i, j, :] / 10.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.asarray(10.0 * np.log10(energy), dtype=np.float64)


def _axis_cell(nodes: "NDArray[np.float64]", value: float) -> "tuple[int, float]":
    """Lower cell index and fractional weight of ``value`` on a node axis.

    Size-1 axes (a single measured row or column) are handled explicitly: the
    only node is the cell with zero fractional weight.
    """
    if nodes.size == 1:
        return 0, 0.0
    i = int(np.clip(np.searchsorted(nodes, value) - 1, 0, nodes.size - 2))
    step = nodes[i + 1] - nodes[i]
    return i, float((value - nodes[i]) / step) if step > 0.0 else 0.0


def _fill_grid(
    azimuth: "NDArray[np.float64]", polar: "NDArray[np.float64]",
    levels: "NDArray[np.float64]",
) -> "NDArray[np.float64]":
    """Nearest-bin gap fill of a hemisphere grid (Eq. 14/15).

    Every empty ``(φ, θ)`` bin of each band takes the level of its angularly
    nearest filled bin, ``ρ = arccos(x·x_{m,n})``, compared through the dot
    product itself (monotone in ``ρ`` and, unlike the angle, well-conditioned
    near ``ρ = 0``). Equally-near bins are energy-averaged, as required by the
    guidance under Eq. 14/15. Bands with no filled bin at all stay ``NaN``.
    """
    n_az, n_po, n_f = levels.shape
    # Unit emission directions (Eq. 11 with rh = 1): x = cosθ, y = sinθ·sinφ,
    # z = sinθ·cosφ, one row per (φ, θ) bin in row-major grid order.
    phi = np.radians(azimuth)[:, None]
    theta = np.radians(polar)[None, :]
    vecs = np.stack([np.broadcast_to(np.cos(theta), (n_az, n_po)),
                     np.sin(theta) * np.sin(phi),
                     np.sin(theta) * np.cos(phi)], axis=-1).reshape(-1, 3)
    dots = np.clip(vecs @ vecs.T, -1.0, 1.0)
    flat = levels.reshape(n_az * n_po, n_f).copy()
    for b in range(n_f):
        band = flat[:, b]
        filled = np.isfinite(band)
        if filled.all() or not filled.any():
            continue
        d = dots[np.ix_(~filled, filled)]
        nearest = d >= d.max(axis=1, keepdims=True) - 1e-9   # ties: energy average
        e = 10.0 ** (band[filled] / 10.0)
        flat[~filled, b] = 10.0 * np.log10(
            (nearest * e).sum(axis=1) / nearest.sum(axis=1))
    return flat.reshape(n_az, n_po, n_f)
