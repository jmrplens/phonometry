#  Copyright (c) 2026. Jose M. Requena-Plens
"""
IEC 61260-1:2014 filter class verification.

Acceptance limits on relative attenuation transcribed from the official text
(BS EN 61260-1:2014, **Table 1**, standard pages 15-16): octave-band
breakpoint frequencies with class 1 and class 2 minimum/maximum limits.
Fractional-octave-band breakpoints are derived with Formulas (9) and (10)
(subclauses 5.10.3-5.10.4) and limits between breakpoints are interpolated
linearly in lg(Omega) per Formula (11) (subclause 5.10.6).

Relative attenuation is ``deltaA(Omega) = A(Omega) - Aref`` (Formula 8) with
``A = Lin - Lout`` (Formula 7); here ``Aref`` is the attenuation at the exact
mid-band frequency (subclause 5.9: the pass-band reference attenuation).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
from scipy import signal

from .core import OctaveFilterBank

_G = 10 ** (3 / 10)

# BS EN 61260-1:2014 Table 1, high side (Omega >= 1), as exponents x of the
# octave-band normalized frequency G**x with (min, max) limits per class.
# The low side mirrors these at 1/Omega (Formula 10). The band-edge rows
# G**(1/2 -+ epsilon) encode the discontinuity at the edge: the pass-band
# segment carries the max limits, the stop-band segment the min limits.
#
# Pass-band max limits (min is constant -0.4 dB class 1 / -0.6 dB class 2):
_PASSBAND_MAX: List[Tuple[float, float, float]] = [
    # (exponent, class 1 max, class 2 max)
    (0.0, 0.4, 0.6),      # Omega = 1
    (1 / 8, 0.5, 0.7),
    (1 / 4, 0.7, 0.9),
    (3 / 8, 1.4, 1.7),
    (1 / 2, 5.3, 5.8),    # G**(1/2) - epsilon
]
_PASSBAND_MIN = {1: -0.4, 2: -0.6}

# Stop-band min limits (max is +inf):
_STOPBAND_MIN: List[Tuple[float, float, float]] = [
    # (exponent, class 1 min, class 2 min)
    (1 / 2, 1.2, 0.8),    # G**(1/2) + epsilon
    (1.0, 16.6, 15.6),
    (2.0, 40.5, 39.5),
    (3.0, 60.0, 54.0),
    (4.0, 70.0, 60.0),    # and >= G**4: constant
]


def _map_breakpoint(exponent: float, fraction: float) -> float:
    """
    Map an octave-band breakpoint G**x to a fractional-octave-band one.

    BS EN 61260-1:2014 Formula (9): the high-frequency breakpoint for
    bandwidth designator 1/b is
    ``1 + (G**(1/(2b)) - 1) / (G**(1/2) - 1) * (Omega_h(1/1) - 1)``.
    """
    omega_octave = _G ** exponent
    scale = (_G ** (1 / (2 * fraction)) - 1) / (_G ** 0.5 - 1)
    return float(1 + scale * (omega_octave - 1))


def class_limits(
    fraction: float, filter_class: int, omega: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Acceptance limits on relative attenuation at normalized frequencies.

    :param fraction: Bandwidth designator denominator b (1 for octave,
        3 for one-third octave, ...).
    :param filter_class: 1 or 2 (IEC 61260-1:2014 performance class).
    :param omega: Normalized frequencies f/fm (> 0).
    :return: Tuple (minimum, maximum) relative attenuation in dB per point;
        the maximum is ``+inf`` outside the pass-band.
    """
    if filter_class not in (1, 2):
        raise ValueError("filter_class must be 1 or 2.")
    if fraction <= 0:
        raise ValueError("'fraction' must be positive.")
    col = 1 if filter_class == 1 else 2

    omega_arr = np.asarray(omega, dtype=np.float64)
    if np.any(omega_arr <= 0):
        raise ValueError("Normalized frequencies must be positive.")
    # Formula (10): low side mirrors the high side.
    omega_h = np.where(omega_arr < 1.0, 1.0 / omega_arr, omega_arr)

    pass_x = np.array([_map_breakpoint(x, fraction) for x, _, _ in _PASSBAND_MAX])
    pass_y = np.array([row[col] for row in _PASSBAND_MAX])
    stop_x = np.array([_map_breakpoint(x, fraction) for x, _, _ in _STOPBAND_MIN])
    stop_y = np.array([row[col] for row in _STOPBAND_MIN])

    edge = pass_x[-1]  # mapped G**(1/2): the band-edge frequency ratio
    in_pass = omega_h <= edge

    minimum = np.empty_like(omega_h)
    maximum = np.empty_like(omega_h)

    # Pass-band: constant min, interpolated max (linear in lg(Omega), Formula 11).
    minimum[in_pass] = _PASSBAND_MIN[filter_class]
    maximum[in_pass] = np.interp(np.log10(omega_h[in_pass]), np.log10(pass_x), pass_y)

    # Stop-band: interpolated min (constant beyond the last breakpoint), max +inf.
    lg = np.log10(omega_h[~in_pass])
    minimum[~in_pass] = np.interp(lg, np.log10(stop_x), stop_y)
    maximum[~in_pass] = np.inf

    return minimum, maximum


def verify_filter_class(bank: OctaveFilterBank, num_points: int = 2 ** 15) -> Dict[str, Any]:
    """
    Verify a filter bank against the IEC 61260-1:2014 class limits.

    Each band's relative attenuation (referenced to the attenuation at its
    exact mid-band frequency) is checked against the class 1 and class 2
    acceptance limits of Table 1, evaluated on a dense frequency grid up to
    the band's processing Nyquist. The Table 1 breakpoint frequencies inside
    that range are always included in the evaluation, so the pass-band
    constraints are checked even if the grid were coarse. Frequencies beyond
    the processing Nyquist cannot carry signal energy at the band's decimated
    rate (the multirate anti-aliasing filter removes them), so they are
    treated as compliant.

    :param bank: The filter bank to verify (its designed SOS are analyzed;
        works for stateful and stateless banks alike).
    :param num_points: Number of frequency grid points per band (>= 16).
    :return: Dict with ``overall_class`` (1, 2 or None) and ``bands``: a list
        of ``{"freq", "class", "margin_class1_db", "margin_class2_db"}``
        where a positive margin means the limits are met with that much room.
    """
    if num_points < 16:
        raise ValueError("'num_points' must be at least 16.")

    bands: List[Dict[str, Any]] = []

    # Table 1 breakpoints (both sides) that must always be evaluated.
    breakpoint_omegas = np.array(
        [_map_breakpoint(x, bank.fraction) for x, _, _ in _PASSBAND_MAX + _STOPBAND_MIN]
    )
    breakpoint_omegas = np.concatenate([1.0 / breakpoint_omegas, breakpoint_omegas])

    for idx in range(bank.num_bands):
        fm = float(bank.freq[idx])
        fsd = bank.fs / float(bank.factor[idx])
        w, h = signal.sosfreqz(bank.sos[idx], worN=num_points, fs=fsd)

        # Attenuation relative to the mid-band attenuation (Formulas 7-8).
        attenuation = -20.0 * np.log10(np.abs(h) + np.finfo(float).eps)
        a_ref = float(np.interp(fm, w, attenuation))
        delta_all = attenuation - a_ref

        omega = w / fm
        valid = omega > 0
        omega, delta_a = omega[valid], delta_all[valid]

        # Guarantee the Table 1 breakpoints (pass-band included) are evaluated.
        omega_max = float(omega.max())
        extra = breakpoint_omegas[(breakpoint_omegas > 0) & (breakpoint_omegas <= omega_max)]
        if extra.size:
            delta_extra = np.interp(extra * fm, w, delta_all)
            omega = np.concatenate([omega, extra])
            delta_a = np.concatenate([delta_a, delta_extra])

        margins: Dict[int, float] = {}
        for cls in (1, 2):
            minimum, maximum = class_limits(bank.fraction, cls, omega)
            low_margin = float(np.min(delta_a - minimum))
            finite = np.isfinite(maximum)
            high_margin = (
                float(np.min(maximum[finite] - delta_a[finite])) if np.any(finite) else np.inf
            )
            margins[cls] = min(low_margin, high_margin)

        band_class = 1 if margins[1] >= 0 else (2 if margins[2] >= 0 else None)
        bands.append(
            {
                "freq": fm,
                "class": band_class,
                "margin_class1_db": margins[1],
                "margin_class2_db": margins[2],
            }
        )

    if not bands:
        # No bands to verify: never report compliance vacuously.
        return {"overall_class": None, "bands": []}

    classes = [band["class"] for band in bands]
    if all(c == 1 for c in classes):
        overall: int | None = 1
    elif all(c in (1, 2) for c in classes):
        overall = 2
    else:
        overall = None

    return {"overall_class": overall, "bands": bands}
