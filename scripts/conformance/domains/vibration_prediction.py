#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Predicting vibration before it is measured (DIN 4150-1:2001-06).

DIN 4150-1 prints seven formulas and no worked example that ends in a
number, but two of its figures are drawn from the formulas with every
parameter printed: Figure A.19 draws Formula (2), the decay with distance,
for 0,44 mm/s at 13 m with an attenuation of 0,005 1/m and the exponents
0, 0,5 and 1, and prints the damping ratio and wavelength the attenuation
comes from; Figure A.18 draws Formula (7), a hall of machines, for
0,44 mm/s measured with three of them, with the correction of Figure 3;
and Figure 2 draws the damping alone for a damping ratio of 0,01 and a wave
speed of 200 m/s at five frequencies.

The rows compare with what the curves show at the resolution of the page:
a hundredth of a millimetre per second where the axis is linear, and 6 %
where the correction is itself read off a nomogram. Figure A.18 lies above
Formula (7) with Figure 3 at every count, by 3 % at 20 and 60 machines and
1 % at 100, so the 6 % covers the standard's own drawing as much as the
reading of it.

Oracle: DIN 4150-1:2001-06, Figure 2 on printed page 7, Figure 3 on printed
page 14, Figure A.18 on printed page 33 and Figure A.19 on printed page 34.
"""

from __future__ import annotations

import functools

import phonometry as ph

from ..registry import Outcome, numeric, register

_PREDICTION = "Predicting vibration before it is measured (DIN 4150-1)"
_EDITION = "DIN 4150-1:2001-06"

#: Figure A.19 (printed page 34): the three curves at 80 m, as drawn.
_A19 = {0.0: 0.32, 0.5: 0.13, 1.0: 0.05}

#: Figure 2 (printed page 7): the five curves at 100 m, as drawn.
_FIGURE_2 = {10.0: 0.73, 20.0: 0.53, 30.0: 0.39, 40.0: 0.28, 50.0: 0.21}

#: Figure A.18 (printed page 33): the curve at 20, 60 and 100 machines, as drawn.
_A18 = {20: 0.78, 60: 1.03, 100: 1.27}


@register(
    _PREDICTION,
    f"{_EDITION} Annex A, Figure A.19",
    "alpha from D = 0,01 and lambda = 12,5 m, as printed, 1/m",
)
def _chk_alpha() -> Outcome:
    computed = ph.vibration.attenuation_coefficient_per_m(0.01, wavelength_m=12.5)
    return numeric(0.005, computed, 0.0005, unit="1/m", places=4)


def _chk_a19(exponent: float) -> Outcome:
    computed = float(
        ph.vibration.far_field_velocity_mm_s(
            0.44,
            [80.0],
            reference_distance_m=13.0,
            exponent=exponent,
            attenuation_per_m=0.005,
        )[0]
    )
    return numeric(_A19[exponent], computed, 0.01, unit="mm/s", places=3)


def _chk_figure_2(frequency_hz: float) -> Outcome:
    computed = float(
        ph.vibration.material_damping_factor(
            [100.0], damping_ratio=0.01, frequency_hz=frequency_hz, wave_speed_m_s=200.0
        )[0]
    )
    return numeric(_FIGURE_2[frequency_hz], computed, 0.02, places=3)


def _chk_a18(machines: int) -> Outcome:
    computed = float(
        ph.vibration.machine_hall_velocity_mm_s(
            0.44, [float(machines)], reference_count=3
        )[0]
    )
    return numeric(_A18[machines], computed, 0.06, unit="mm/s", rel=True, places=3)


def _register_rows() -> None:
    for exponent in _A19:
        register(
            _PREDICTION,
            f"{_EDITION} Annex A, Figure A.19",
            f"v at 80 m by Formula (2) with n = {exponent:g}, as drawn, mm/s",
        )(functools.partial(_chk_a19, exponent))
    for frequency in _FIGURE_2:
        register(
            _PREDICTION,
            f"{_EDITION} Figure 2",
            f"Damping factor at 100 m and {frequency:g} Hz, as drawn",
        )(functools.partial(_chk_figure_2, frequency))
    for machines in _A18:
        register(
            _PREDICTION,
            f"{_EDITION} Annex A, Figure A.18",
            f"v_N for {machines} machines by Formula (7) with chi of Figure 3, as drawn, mm/s",
        )(functools.partial(_chk_a18, machines))


_register_rows()
