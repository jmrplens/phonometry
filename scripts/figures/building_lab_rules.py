#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Figures for the laboratory application rules of ISO 10140-1:2021.

The three annexes that measure what a product adds rather than what an element
is: a lining on a standard basic element (Annex G), a floor covering on a
reference floor (Annex H), and rain on a rooflight (Annex K). Every panel is
drawn by the library's own ``.plot()``, so the figure is what a user gets.
Everything here is embedded by
``buildings/insulation/lab-application-rules``.
"""

import matplotlib.pyplot as plt
import numpy as np

from .i18n import _LANG
from .theme import (
    COLOR_FG,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_TERTIARY,
    save_figure,
)

#: One-third-octave bands of ISO 717-1:2020 Table E.1, 50 Hz to 5000 Hz.
_BANDS_50_5000 = [
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
    5000.0,
]
#: The 18 bands of ISO 10140-4, 100 Hz to 5000 Hz.
_BANDS_100_5000 = _BANDS_50_5000[3:]


def generate_lab_lining_improvement(output_dir: str) -> None:
    """ISO 10140-1 Annex G: a lining measured on the heavy wall, and its rating."""
    print("Generating lab_lining_improvement...")
    from phonometry import building

    # Gypsum board on free-standing studs with mineral wool, 50 mm off a heavy
    # calcium-silicate wall: the mass-spring-mass resonance near 63 Hz costs a
    # few decibels, and the board's own coincidence shows at 2500-3150 Hz.
    r_without = np.array(
        [36.1, 37.0, 38.2, 39.5, 40.3, 41.2, 40.6, 41.8, 43.9, 46.4, 48.9]
        + [51.6, 54.2, 56.5, 58.7, 61.4, 63.3, 64.2, 64.8, 65.9, 66.4]
    )
    delta_r = np.array(
        [-2.1, -5.4, -3.2, 1.5, 4.8, 7.9, 10.6, 12.9, 14.7, 16.2, 17.4]
        + [18.3, 19.1, 19.6, 19.9, 19.5, 18.2, 16.4, 15.8, 17.1, 18.0]
    )
    res = building.lab_lining_improvement(
        r_without, r_without + delta_r, _BANDS_50_5000
    )
    assert res.rating is not None

    _fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.6))
    res.plot(ax=ax1, language=_LANG, color=COLOR_PRIMARY)
    res.rating.plot(ax=ax2, language=_LANG, color=COLOR_SECONDARY)
    plt.tight_layout()
    save_figure(output_dir, "lab_lining_improvement.png")
    plt.close()


def generate_lab_floor_covering_improvement(output_dir: str) -> None:
    """ISO 10140-1 Annex H: the four reference floors, and a covering rated on No 3."""
    print("Generating lab_floor_covering_improvement...")
    from phonometry import building
    from phonometry._plot.building import _t
    from phonometry._plot.common import _band_axis

    # A resilient vinyl covering on the timber reference floor of type No 3:
    # it barely touches the low bands where a joist floor is loudest.
    l_n0 = np.array(
        [70.5, 73.4, 75.8, 77.2, 78.9, 78.1, 77.6, 78.3, 77.1]
        + [75.4, 73.8, 71.2, 68.9, 65.7, 62.8, 59.6, 56.9, 53.8]
    )
    delta_l = np.array(
        [0.4, 0.8, 1.5, 2.3, 3.4, 4.9, 6.8, 9.1, 11.6]
        + [14.2, 16.9, 19.8, 22.4, 25.1, 27.3, 29.4, 30.8, 31.9]
    )
    res = building.lab_floor_covering_improvement(
        l_n0, l_n0 - delta_l, _BANDS_100_5000, reference_floor="lightweight_3"
    )

    _fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.6))
    floors = building.IMPACT_REFERENCE_FLOORS
    positions = _band_axis(ax1, list(floors["heavyweight"]), language=_LANG)
    for key, label, colour, style in (
        ("heavyweight", "heavyweight floor", COLOR_FG, "s--"),
        ("lightweight_1", "lightweight floors No 1 and No 2", COLOR_PRIMARY, "o-"),
        ("lightweight_3", "lightweight floor No 3", COLOR_TERTIARY, "^-"),
    ):
        ax1.plot(
            positions,
            list(floors[key].values()),
            style,
            color=colour,
            lw=1.8,
            label=_t(label, _LANG),
        )
    ax1.set_ylabel(_t("Impact sound pressure level [dB]", _LANG))
    ax1.set_title(_t("Reference floors (ISO 717-2 Table 4)", _LANG))
    ax1.grid(visible=True, alpha=0.3)
    ax1.legend(loc="lower left", fontsize="small")
    res.plot(ax=ax2, language=_LANG, color=COLOR_PRIMARY)
    plt.tight_layout()
    save_figure(output_dir, "lab_floor_covering_improvement.png")
    plt.close()


def generate_rainfall_sound(output_dir: str) -> None:
    """ISO 10140-1 Annex K: the reference pane, and a rooflight under heavy rain."""
    print("Generating rainfall_sound...")
    from phonometry import building

    # The laboratory's 6 mm reference pane: mounted a little more lossily
    # than Table I.1 assumes (its structural reverberation time is 0.8 times
    # the one the reference loss factor would give).
    l_i_ref = np.array(
        [46.2, 45.8, 46.9, 46.5, 47.8, 47.2, 47.9, 48.1, 47.6]
        + [46.8, 44.9, 43.1, 43.8, 46.9, 51.6, 50.9, 46.8, 44.6]
    )
    t_s = np.array(
        [0.176, 0.177, 0.138, 0.139, 0.140, 0.111, 0.111, 0.088, 0.088]
        + [0.070, 0.070, 0.071, 0.055, 0.056, 0.044, 0.044, 0.035, 0.035]
    )
    correction = building.rainfall_reference_correction(l_i_ref, t_s)
    # A 1.25 m x 1.5 m polycarbonate rooflight under heavy rain in a 62 m3
    # test room.
    l_pr = np.array(
        [48.2, 51.0, 53.1, 55.4, 57.0, 58.3, 59.1, 59.8, 60.2]
        + [60.4, 60.1, 59.4, 58.6, 57.5, 56.2, 54.4, 52.3, 49.8]
    )
    t = np.array(
        [1.9, 1.8, 1.7, 1.6, 1.5, 1.45, 1.4, 1.35, 1.3]
        + [1.25, 1.2, 1.15, 1.1, 1.05, 1.0, 0.95, 0.9, 0.85]
    )
    res = building.rainfall_sound(
        l_pr,
        t,
        _BANDS_100_5000,
        volume_m3=62.0,
        excited_area_m2=1.875,
        reference_correction=correction,
    )

    _fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.6))
    correction.plot(ax=ax1, language=_LANG, color=COLOR_PRIMARY)
    res.plot(ax=ax2, language=_LANG, color=COLOR_PRIMARY)
    plt.tight_layout()
    save_figure(output_dir, "rainfall_sound.png")
    plt.close()
