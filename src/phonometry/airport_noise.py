#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Noise-Power-Distance (NPD) event-level interpolation (ECAC Doc 29).

The ECAC Doc 29 airport-noise method describes an aircraft's noise emission with
**Noise-Power-Distance (NPD)** tables: the event noise level (``LAmax`` or the
sound exposure level ``SEL``) of an aircraft in steady straight flight on an
infinite path, tabulated over a grid of engine power settings and slant
distances at reference conditions. Placing an aircraft's noise at a receiver
starts by reading a level from this table for an arbitrary power and distance.

* :func:`npd_level` -- the interpolated event level ``L(P, d)``, linear in power
  and log-linear in distance (Eqs. 4-3/4-4), with extrapolation beyond the
  tabulated envelope.
* :func:`npd_curve` -- the level over a distance sweep at one power, returned as
  an :class:`NpdLevelResult` with a ``.plot()``.

The single-event stage segments a flight path and adjusts the NPD baseline per
segment (§4.3-4.5): :func:`impedance_adjustment` (Eq. 4-6/4-7),
:func:`lateral_attenuation` (β, ℓ), :func:`engine_installation_correction`
(φ, mounting), :func:`duration_correction` and the finite-segment
:func:`noise_fraction`. :func:`event_level` assembles and sums them into the
``SEL``/``LAmax`` of a movement, and :func:`noise_contour` evaluates it over a
ground grid. Start-of-roll ground-roll directivity (§4.5.7) is out of scope.

Source (clean-room, implemented from the standard text): ECAC Doc 29, 4th ed.,
Vol 2 (2016), §4.2-4.5. Validated per-term and end-to-end against the ECAC
Doc 29 5th ed. Vol 3 Part 1 reference workbook.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import NDArray


#: NPD reference speed (160 kn) in ft/s, used by the noise-fraction scaled
#: distance (ECAC Doc 29 §4.5.6).
_VREF_FTS = 270.05
#: Engine-installation coefficients (a, b, c) by mounting (Eq. 4-15).
_INSTALLATION = {
    "wing": (0.0039, 0.062, 0.8786),
    "fuselage": (0.1225, 0.329, 1.0),
}


def lateral_attenuation(elevation_deg: float, lateral_m: float) -> float:
    """Excess lateral attenuation ``Λ(β, ℓ)`` over soft ground (Eq. 4-18/4-19).

    :param elevation_deg: Elevation angle ``β`` of the (equivalent level) path,
        in degrees.
    :param lateral_m: Lateral displacement ``ℓ`` from the ground track, in metres.
    :return: The lateral attenuation ``Λ``, in dB (subtracted from the level).
    :raises ValueError: If ``lateral_m`` is negative or non-finite.
    """
    ell = float(lateral_m)
    beta = float(elevation_deg)
    if not np.isfinite(ell) or ell < 0.0 or not np.isfinite(beta):
        raise ValueError("'lateral_m' must be non-negative and inputs finite.")
    gamma = 1.089 * (1.0 - np.exp(-0.00274 * ell)) if ell <= 914.0 else 1.0
    if beta < 0.0:
        lam = 10.857
    elif beta <= 50.0:
        lam = 1.137 - 0.0229 * beta + 9.72 * np.exp(-0.142 * beta)
    else:
        lam = 0.0
    return float(gamma * lam)


def engine_installation_correction(depression_deg: float, mounting: str = "wing") -> float:
    """Engine-installation lateral-directivity correction ``ΔI(φ)`` (Eq. 4-15/4-16).

    :param depression_deg: Depression angle ``φ`` (from the wing plane), in degrees.
    :param mounting: ``"wing"``, ``"fuselage"`` or ``"propeller"``.
    :return: The correction ``ΔI``, in dB (added to the level).
    :raises ValueError: If ``mounting`` is unknown or the angle is non-finite.
    """
    phi = float(depression_deg)
    if not np.isfinite(phi):
        raise ValueError("'depression_deg' must be finite.")
    key = mounting.strip().lower()
    if key in ("propeller", "prop"):
        return 0.0
    if key not in _INSTALLATION:
        raise ValueError(f"'mounting' must be 'wing', 'fuselage' or 'propeller', got {mounting!r}.")
    a, b, c = _INSTALLATION[key]
    phi_eff = np.radians(max(phi, 0.0))  # for φ<0, ΔI(φ)=ΔI(0)
    num = (a * np.cos(phi_eff) ** 2 + np.sin(phi_eff) ** 2) ** b
    den = c * np.sin(2.0 * phi_eff) ** 2 + np.cos(2.0 * phi_eff) ** 2
    return float(10.0 * np.log10(num / den))


def duration_correction(reference_speed: float, segment_speed: float) -> float:
    """Duration correction ``ΔV = 10·log10(Vref/Vseg)`` (Eq. 4-14, exposure only).

    :param reference_speed: NPD reference speed ``Vref`` (any consistent unit).
    :param segment_speed: Segment speed ``Vseg`` (same unit).
    :return: The duration correction ``ΔV``, in dB.
    :raises ValueError: If a speed is not strictly positive.
    """
    vref = float(reference_speed)
    vseg = float(segment_speed)
    if not (np.isfinite(vref) and vref > 0.0 and np.isfinite(vseg) and vseg > 0.0):
        raise ValueError("'reference_speed' and 'segment_speed' must be positive.")
    return float(10.0 * np.log10(vref / vseg))


def noise_fraction(q: float, segment_length: float, scaled_distance: float) -> float:
    """Finite-segment correction (noise fraction) ``ΔF`` (Eq. 4-20, exposure only).

    :param q: Signed distance from the segment start ``S1`` to the perpendicular
        foot ``Sp``, in metres (negative behind the segment).
    :param segment_length: Segment length ``λ``, in metres (``> 0``).
    :param scaled_distance: The scaled distance ``dλ`` (Appendix E), in metres
        (``> 0``).
    :return: The finite-segment correction ``ΔF``, in dB (``<= 0``, floored at
        −150 dB).
    :raises ValueError: If ``segment_length`` or ``scaled_distance`` is not
        positive.
    """
    lam = float(segment_length)
    dl = float(scaled_distance)
    if not (np.isfinite(lam) and lam > 0.0 and np.isfinite(dl) and dl > 0.0):
        raise ValueError("'segment_length' and 'scaled_distance' must be positive.")
    # Relative distances from the perpendicular foot Sp to the segment ends,
    # scaled by dλ: to the start S1 (−q) and to the end S2 (λ−q). The full
    # infinite path (α1→−∞, α2→+∞) then gives F=1, i.e. ΔF=0.
    a1 = -float(q) / dl
    a2 = (lam - float(q)) / dl
    frac = (a2 / (1.0 + a2**2) + np.arctan(a2) - a1 / (1.0 + a1**2) - np.arctan(a1)) / np.pi
    if frac <= 0.0:
        return -150.0
    return float(max(10.0 * np.log10(frac), -150.0))


#: Reference specific acoustic impedance of the NPD (ANP) data, in N·s/m³
#: (Eq. 4-6). #: Air impedance at the standard atmosphere (δ = θ = 1), Eq. 4-7.
_ZC_REF = 409.81
_ZC_STD = 416.86
#: Standard mean-sea-level pressure (kPa) and temperature (°C), Eq. 4-7.
_P0_KPA = 101.325
_T0_C = 15.0


def impedance_adjustment(temperature: float = _T0_C, pressure: float = _P0_KPA) -> float:
    """Acoustic-impedance adjustment of the standard NPD data (Eq. 4-6/4-7).

    The ANP NPD levels are normalised to a reference specific acoustic impedance
    of 409.81 N·s/m³. At the aerodrome's temperature and pressure the air
    impedance is ``ρc = 416.86·(δ/√θ)`` with ``δ = p/p0`` and
    ``θ = (T+273.15)/(T0+273.15)``, and the adjustment ``10·log10(ρc/409.81)`` is
    added to the NPD levels. Under the standard atmosphere it is +0.074 dB.

    :param temperature: Aerodrome air temperature ``T``, in °C (default 15 °C).
    :param pressure: Aerodrome air pressure ``p``, in kPa (default 101.325 kPa).
    :return: The impedance adjustment, in dB (added to the NPD level).
    :raises ValueError: If the pressure is not positive or inputs are non-finite.
    """
    t = float(temperature)
    p = float(pressure)
    if not (np.isfinite(t) and np.isfinite(p) and p > 0.0):
        raise ValueError("'pressure' must be positive and inputs finite.")
    delta = p / _P0_KPA
    theta = (t + 273.15) / (_T0_C + 273.15)
    zc = _ZC_STD * delta / np.sqrt(theta)
    return float(10.0 * np.log10(zc / _ZC_REF))


def _clean_table(
    powers: "NDArray[np.float64] | list[float]",
    distances: "NDArray[np.float64] | list[float]",
    levels: "NDArray[np.float64] | list[list[float]]",
) -> "tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]":
    p = np.asarray(powers, dtype=np.float64).ravel()
    d = np.asarray(distances, dtype=np.float64).ravel()
    lv = np.asarray(levels, dtype=np.float64)
    if p.size < 2 or d.size < 2:
        raise ValueError("'powers' and 'distances' must each have at least two values.")
    if lv.shape != (p.size, d.size):
        raise ValueError("'levels' must have shape (len(powers), len(distances)).")
    if not (np.all(np.isfinite(p)) and np.all(np.isfinite(d)) and np.all(np.isfinite(lv))):
        raise ValueError("'powers', 'distances' and 'levels' must be finite.")
    if np.any(d <= 0.0):
        raise ValueError("'distances' must be strictly positive (slant range in m).")
    if np.any(np.diff(p) <= 0.0):
        raise ValueError("'powers' must be strictly increasing.")
    if np.any(np.diff(d) <= 0.0):
        raise ValueError("'distances' must be strictly increasing.")
    return p, d, lv


def _interp_distance(logd_tab: "NDArray[np.float64]", row: "NDArray[np.float64]",
                     logd: "NDArray[np.float64]") -> "NDArray[np.float64]":
    """Log-linear interpolation/extrapolation of one NPD row over distance (Eq. 4-4)."""
    idx = np.clip(np.searchsorted(logd_tab, logd) - 1, 0, logd_tab.size - 2)
    x0 = logd_tab[idx]
    x1 = logd_tab[idx + 1]
    y0 = row[idx]
    y1 = row[idx + 1]
    return np.asarray(y0 + (y1 - y0) / (x1 - x0) * (logd - x0), dtype=np.float64)


@dataclass(frozen=True)
class NpdLevelResult:
    """NPD event level over a distance sweep at one power (ECAC Doc 29).

    :ivar distance: Slant distances, in metres.
    :ivar level: Interpolated event level per distance, in dB.
    :ivar power: The engine power setting queried.
    :ivar table_distances: The tabulated slant distances, in metres.
    :ivar table_levels: The tabulated levels at the queried power, in dB.
    """

    distance: "NDArray[np.float64]"
    level: "NDArray[np.float64]"
    power: float
    table_distances: "NDArray[np.float64]"
    table_levels: "NDArray[np.float64]"

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the interpolated level versus slant distance (log axis)."""
        from ._plotting import plot_npd_level

        return plot_npd_level(self, ax=ax, **kwargs)


def npd_level(
    powers: "NDArray[np.float64] | list[float]",
    distances: "NDArray[np.float64] | list[float]",
    levels: "NDArray[np.float64] | list[list[float]]",
    power: float,
    distance: "NDArray[np.float64] | list[float] | float",
) -> "NDArray[np.float64]":
    """Interpolated NPD event level ``L(P, d)`` (ECAC Doc 29 §4.2, Eqs. 4-3/4-4).

    Interpolates log-linearly in slant distance (Eq. 4-4) at the two bracketing
    tabulated powers, then linearly in power (Eq. 4-3). Queries outside the
    tabulated envelope are extrapolated from the terminal segments.

    :param powers: Tabulated engine power settings (1-D, strictly increasing).
    :param distances: Tabulated slant distances, in metres (1-D, strictly
        increasing, positive).
    :param levels: Tabulated event levels, shape ``(len(powers), len(distances))``,
        in dB.
    :param power: Query engine power setting ``P``.
    :param distance: Query slant distance(s) ``d``, in metres.
    :return: The interpolated event level per query distance, in dB.
    :raises ValueError: If the table or inputs are invalid.
    """
    p, d, lv = _clean_table(powers, distances, levels)
    dq = np.atleast_1d(np.asarray(distance, dtype=np.float64))
    if dq.size == 0 or not np.all(np.isfinite(dq)) or np.any(dq <= 0.0):
        raise ValueError("'distance' must be finite and strictly positive.")
    pq = float(power)
    if not np.isfinite(pq):
        raise ValueError("'power' must be finite.")

    logd_tab = np.log10(d)
    logdq = np.log10(dq)
    # Log-linear interpolation over distance for every tabulated power row.
    rows = np.array([_interp_distance(logd_tab, lv[i], logdq) for i in range(p.size)])
    # Linear interpolation/extrapolation over power between the bracketing rows.
    j = int(np.clip(np.searchsorted(p, pq) - 1, 0, p.size - 2))
    frac = (pq - p[j]) / (p[j + 1] - p[j])
    return np.asarray(rows[j] + (rows[j + 1] - rows[j]) * frac, dtype=np.float64)


def npd_curve(
    powers: "NDArray[np.float64] | list[float]",
    distances: "NDArray[np.float64] | list[float]",
    levels: "NDArray[np.float64] | list[list[float]]",
    power: float,
    query_distances: "NDArray[np.float64] | list[float] | None" = None,
) -> NpdLevelResult:
    """NPD event level over a distance sweep at one power setting.

    :param powers: Tabulated engine power settings.
    :param distances: Tabulated slant distances, in metres.
    :param levels: Tabulated event levels, shape ``(len(powers), len(distances))``.
    :param power: Query engine power setting.
    :param query_distances: Distances to evaluate, in metres; defaults to a log
        sweep across the tabulated envelope.
    :return: An :class:`NpdLevelResult`.
    :raises ValueError: If the inputs are invalid.
    """
    p, d, lv = _clean_table(powers, distances, levels)
    if query_distances is None:
        dq = np.logspace(np.log10(d[0]), np.log10(d[-1]), 200)
    else:
        dq = np.atleast_1d(np.asarray(query_distances, dtype=np.float64))
    level = npd_level(p, d, lv, power, dq)
    row = npd_level(p, d, lv, power, d)  # tabulated levels at the queried power
    return NpdLevelResult(
        distance=dq,
        level=level,
        power=float(power),
        table_distances=d,
        table_levels=row,
    )


# ===========================================================================
# Single-event flight-path calculation (ECAC Doc 29 §4.3-4.5)
# ===========================================================================

#: Reference speed 160 kn in m/s and the noise-fraction d0 = (2/π)·Vref·t0 (m).
_VREF_MS = 160.0 * 0.514444
_D0_M = (2.0 / np.pi) * _VREF_MS * 1.0


def _segment_geometry(
    s1: "NDArray[np.float64]", s2: "NDArray[np.float64]", obs: "NDArray[np.float64]",
    bank_deg: float = 0.0,
) -> "tuple[float, float, float, float, float, float, float]":
    """Return ``(length, q, dp, ds, beta_deg, phi_deg, lateral_m)`` for a segment.

    ``s1``, ``s2`` and ``obs`` are 3-D points ``(x, y, z)`` (any consistent unit);
    the flight direction is ``s1 -> s2`` (ECAC Doc 29 Fig. 4-2). ``beta`` is the
    elevation angle for lateral attenuation (from the nearest actual segment
    point) and ``phi`` the depression angle for the engine-installation effect
    (from the perpendicular foot on the extended segment line), per §4.5.4-4.5.5.
    """
    seg = s2 - s1
    length = float(np.linalg.norm(seg))
    if length <= 0.0:  # degenerate (duplicate waypoints): caller skips it
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    u = seg / length
    q = float(np.dot(obs - s1, u))
    foot = s1 + q * u
    dp = float(np.linalg.norm(obs - foot))
    d1 = float(np.linalg.norm(obs - s1))
    d2 = float(np.linalg.norm(obs - s2))
    ds = d1 if q < 0.0 else (d2 if q > length else dp)
    # Horizontal perpendicular distance to the ground track (project to z = 0).
    seg_g = seg.copy()
    seg_g[2] = 0.0
    gl = float(np.linalg.norm(seg_g))
    if gl > 0.0:
        ug = seg_g / gl
        og = obs - s1
        og[2] = 0.0
        lateral = float(np.linalg.norm(og - np.dot(og, ug) * ug))
    else:  # vertical ground track (degenerate): use horizontal offset from s1
        lateral = float(np.hypot(obs[0] - s1[0], obs[1] - s1[1]))
    # Heights above the observer: perpendicular foot on the extended line (for φ)
    # and nearest actual segment point (for β) — §4.5.5 equivalent level path.
    z_foot = float(foot[2] - obs[2])
    z_near = float((s1[2] if q < 0.0 else (s2[2] if q > length else foot[2])) - obs[2])
    if lateral > 0.0:
        beta = float(np.degrees(np.arctan2(z_near, lateral)))
        phi = float(np.degrees(np.arctan2(z_foot, lateral))) - float(bank_deg)
    else:  # directly overhead: elevation/depression are ±90° by sign of height
        beta = 90.0 if z_near >= 0.0 else -90.0
        phi = (90.0 if z_foot >= 0.0 else -90.0) - float(bank_deg)
    return length, q, dp, ds, beta, phi, lateral


@dataclass(frozen=True)
class FlyoverResult:
    """Single-event noise level of an aircraft movement at a receiver.

    :ivar level: The event level, in dB (SEL for ``metric="exposure"``, else the
        maximum level).
    :ivar metric: ``"exposure"`` (SEL) or ``"maximum"`` (LAmax).
    :ivar segment_levels: Per-segment contribution, in dB.
    :ivar observer: Receiver position ``(x, y, z)``, in metres.
    """

    level: float
    metric: str
    segment_levels: "NDArray[np.float64]"
    observer: "NDArray[np.float64]"

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the per-segment contributions to the event level."""
        from ._plotting import plot_flyover

        return plot_flyover(self, ax=ax, **kwargs)


def event_level(
    path: "NDArray[np.float64] | list[list[float]]",
    observer: "NDArray[np.float64] | list[float]",
    powers: "NDArray[np.float64] | list[float]",
    distances: "NDArray[np.float64] | list[float]",
    exposure_levels: "NDArray[np.float64] | list[list[float]]",
    maximum_levels: "NDArray[np.float64] | list[list[float]]",
    *,
    reference_speed: float = _VREF_MS,
    mounting: str = "wing",
    metric: str = "exposure",
    temperature: float = _T0_C,
    pressure: float = _P0_KPA,
) -> FlyoverResult:
    """Single-event noise level of a flight path at a receiver (ECAC Doc 29).

    Assembles the segment event levels (Eq. 4-8) — NPD baseline plus the duration,
    engine-installation, lateral-attenuation and finite-segment (noise-fraction)
    corrections — and combines them into the exposure level ``SEL`` (energy sum,
    Eq. 4-11) or the maximum level (Eq. 4-10). Airborne segments only (ground-roll
    start-of-roll directivity is out of scope).

    :param path: Flight-path points, shape ``(N, 5)``: columns ``x, y, z`` (m),
        engine power setting and speed (m/s). ``N-1`` segments are formed.
    :param observer: Receiver position ``(x, y, z)``, in metres.
    :param powers: NPD tabulated power settings.
    :param distances: NPD tabulated slant distances, in metres.
    :param exposure_levels: NPD exposure (SEL) levels, shape ``(P, D)``.
    :param maximum_levels: NPD maximum levels, shape ``(P, D)``.
    :param reference_speed: NPD reference speed, in m/s (default 160 kn).
    :param mounting: Engine mounting (``"wing"``/``"fuselage"``/``"propeller"``).
    :param metric: ``"exposure"`` (SEL) or ``"maximum"`` (LAmax).
    :param temperature: Aerodrome air temperature, in °C (impedance adjustment).
    :param pressure: Aerodrome air pressure, in kPa (impedance adjustment).
    :return: A :class:`FlyoverResult`.
    :raises ValueError: If the inputs are invalid.
    """
    pts = np.asarray(path, dtype=np.float64)
    if pts.ndim != 2 or pts.shape[1] != 5 or pts.shape[0] < 2:
        raise ValueError("'path' must have shape (N, 5) with N >= 2 (x,y,z,power,speed).")
    obs = np.asarray(observer, dtype=np.float64).ravel()
    if obs.shape != (3,) or not np.all(np.isfinite(obs)):
        raise ValueError("'observer' must be a finite (x, y, z) point.")
    key = metric.strip().lower()
    if key not in ("exposure", "maximum"):
        raise ValueError("'metric' must be 'exposure' or 'maximum'.")
    p, d, le = _clean_table(powers, distances, exposure_levels)
    _, _, lm = _clean_table(powers, distances, maximum_levels)
    vref = float(reference_speed)
    imp = impedance_adjustment(temperature, pressure)

    seg_levels = []
    for i in range(pts.shape[0] - 1):
        s1, s2 = pts[i, :3], pts[i + 1, :3]
        p1, p2 = pts[i, 3], pts[i + 1, 3]
        v1, v2 = pts[i, 4], pts[i + 1, 4]
        length, q, dp, ds, beta, phi, lateral = _segment_geometry(s1, s2, obs)
        if length <= 0.0:
            continue
        frac = np.clip(q / length, 0.0, 1.0)
        p_seg = np.sqrt(max(p1**2 + frac * (p2**2 - p1**2), 0.0))
        lam_att = lateral_attenuation(beta, lateral)
        di = engine_installation_correction(phi, mounting)
        if key == "maximum":
            base = float(npd_level(p, d, lm, p_seg, ds)[0])
            seg_levels.append(base + imp + di - lam_att)
        else:
            base = float(npd_level(p, d, le, p_seg, dp)[0])
            v_seg = np.sqrt(max(v1**2 + frac * (v2**2 - v1**2), 1e-9))
            dv = duration_correction(vref, v_seg)
            le_dp = float(npd_level(p, d, le, p_seg, dp)[0])
            lm_dp = float(npd_level(p, d, lm, p_seg, dp)[0])
            d_lambda = _D0_M * 10.0 ** ((le_dp - lm_dp) / 10.0)
            df = noise_fraction(q, length, d_lambda)
            seg_levels.append(base + imp + dv + di - lam_att + df)

    seg_arr = np.asarray(seg_levels, dtype=np.float64)
    if seg_arr.size == 0:
        total = float("-inf")
    elif key == "maximum":
        total = float(np.max(seg_arr))
    else:
        total = float(10.0 * np.log10(np.sum(10.0 ** (seg_arr / 10.0))))
    return FlyoverResult(level=total, metric=key, segment_levels=seg_arr, observer=obs)


@dataclass(frozen=True)
class NoiseContourResult:
    """Single-event noise level over a ground grid (ECAC Doc 29).

    :ivar x: Grid x coordinates, in metres.
    :ivar y: Grid y coordinates, in metres.
    :ivar level: Event level over the grid ``(len(y), len(x))``, in dB.
    :ivar metric: ``"exposure"`` (SEL) or ``"maximum"`` (LAmax).
    """

    x: "NDArray[np.float64]"
    y: "NDArray[np.float64]"
    level: "NDArray[np.float64]"
    metric: str

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot filled noise contours over the ground plane."""
        from ._plotting import plot_noise_contour

        return plot_noise_contour(self, ax=ax, **kwargs)


def noise_contour(
    path: "NDArray[np.float64] | list[list[float]]",
    powers: "NDArray[np.float64] | list[float]",
    distances: "NDArray[np.float64] | list[float]",
    exposure_levels: "NDArray[np.float64] | list[list[float]]",
    maximum_levels: "NDArray[np.float64] | list[list[float]]",
    *,
    x: "NDArray[np.float64] | list[float]",
    y: "NDArray[np.float64] | list[float]",
    reference_speed: float = _VREF_MS,
    mounting: str = "wing",
    metric: str = "exposure",
    temperature: float = _T0_C,
    pressure: float = _P0_KPA,
) -> NoiseContourResult:
    """Single-event noise level over a ground grid (ECAC Doc 29 contour).

    Evaluates :func:`event_level` at every grid point ``(xi, yj, 0)``.

    :param path: Flight-path points, shape ``(N, 5)`` (see :func:`event_level`).
    :param powers: NPD tabulated power settings.
    :param distances: NPD tabulated slant distances, in metres.
    :param exposure_levels: NPD exposure (SEL) levels, shape ``(P, D)``.
    :param maximum_levels: NPD maximum levels, shape ``(P, D)``.
    :param x: Grid x coordinates, in metres.
    :param y: Grid y coordinates, in metres.
    :param reference_speed: NPD reference speed, in m/s.
    :param mounting: Engine mounting.
    :param metric: ``"exposure"`` (SEL) or ``"maximum"`` (LAmax).
    :param temperature: Aerodrome air temperature, in °C (impedance adjustment).
    :param pressure: Aerodrome air pressure, in kPa (impedance adjustment).
    :return: A :class:`NoiseContourResult`.
    :raises ValueError: If the inputs are invalid.
    """
    gx = np.asarray(x, dtype=np.float64).ravel()
    gy = np.asarray(y, dtype=np.float64).ravel()
    if gx.size < 2 or gy.size < 2:
        raise ValueError("'x' and 'y' must each have at least two grid points.")
    grid = np.empty((gy.size, gx.size), dtype=np.float64)
    for iy, yy in enumerate(gy):
        for ix, xx in enumerate(gx):
            grid[iy, ix] = event_level(
                path, [float(xx), float(yy), 0.0], powers, distances, exposure_levels,
                maximum_levels,
                reference_speed=reference_speed, mounting=mounting, metric=metric,
                temperature=temperature, pressure=pressure,
            ).level
    return NoiseContourResult(x=gx, y=gy, level=grid, metric=metric.strip().lower())
