#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Predicting railway vibration from third-octave spectra (E DIN 45672-3:2023-02).

Part 3 of DIN 45672 has never been published; the draft of February 2023 is
the only text of it, and it is the prediction method that E DIN 4150-2:2023-08
refers a planning approval to. Where Part 1 measures next to a line and Part 2
reduces what was measured, Part 3 says what a building that does not exist
yet, next to a line that does not exist yet, is going to feel: a third-octave
velocity spectrum on a floor, and from it the assessment quantities of
DIN 4150-2.

**The chain** (Clause 5.1, Formula (1)). The predicted spectrum on a floor is
an emission spectrum plus four level differences, band by band from 4 Hz to
250 Hz:

.. math::

   L_v(f_{Tn}) = L_{v,E}(f_{Tn}) + \Delta L_{v,BB}(f_{Tn}) + \Delta L_{v,FB}(f_{Tn})
   + \Delta L_{v,DF}(f_{Tn}) + D_e(f_{Tn})

the emission :math:`L_{v,E}` as a Max Hold spectrum of the Zuggattung at a
known distance (Clause 5.2), the transmission :math:`\Delta L_{v,BB}` through
the ground to the building (Clause 5.3), the transfer :math:`\Delta L_{v,FB}`
from the ground into the foundation and :math:`\Delta L_{v,DF}` from the
foundation to the floor (Clause 5.4), and the insertion loss :math:`D_e` of
whatever mitigation is planned (Clause 5.5). Every term is added as printed,
so a mitigation enters as a negative number.

**Emission** (Clause 5.2). A measured spectrum is carried to another speed of
the same category by :math:`20 \lg(v_2/v_1)` (Formula (3)), for a change of
speed of up to 30 %; beyond that the sleeper-passing frequency moves and the
spectrum with it.

**Transmission** (Clause 5.3). The ratio of the velocities at the distance
:math:`r` and at the reference distance :math:`r_0` is geometric spreading
times material damping (Formula (5)), :math:`(r/r_0)^{-n} e^{-\alpha_R (r -
r_0)}` with :math:`\alpha_R = 2\pi f D / c_s`, or a power law with an exponent
measured per band (Formula (6)); the level difference is 20 lg of it
(Formula (4)). On the surface the exponent is usually 0,2 to 0,4.

**Building** (Clause 5.4, Annex A). Six tables of level differences from
extensive building measurements: ground to floor for concrete and for timber
floors by the natural frequency of the floor (Tables A.1 and A.2), ground to
foundation for a basement and for a ground floor with a mean and a
deviation either way (Tables A.3 and A.4), and foundation to floor against
the ratio of the band to the natural frequency of the floor (Tables A.5 and
A.6). The prediction is run once per natural frequency the building may
have, never with the envelope over all of them.

**Assessment quantities** (Clause 7). The KB weighting of DIN 45669-1 as a
table of third-octave corrections (Table 2, Formula (8)) is added to the
predicted spectrum, the bands from 4 Hz to 80 Hz are summed, and the sum
level gives the clock maximum r.m.s. of the category (Formula (9)),
:math:`KB_{FTm,Zug} = c_{T1} v_0 10^{L/20}` with :math:`c_{T1} = 1` and
:math:`v_0 = 5 \cdot 10^{-5}` mm/s; 1,5 times it is :math:`KB_{F\mathrm{max},Zug}`
(Formula (10)), three times that the peak velocity a DIN 4150-3 comparison
wants (Formula (12)), and Formula (11) is the sum of Formula (6) of E DIN
4150-2:2023-08, printed without that formula's rule that a category whose
:math:`KB_{FTm,Zug}` is at or below 0,1 enters as zero; the assessment the
draft says it performs is that of DIN 4150-2, so
:func:`~phonometry.vibration.train_assessment_severity` of
:mod:`phonometry.vibration.immission.train_categories`, which applies the
rule, is what the chain ends in. Formula (13) turns a level spectrum back
into a velocity spectrum in micrometres per second, for the VC curves.

**A point source and a train** (Annex B). A train is a line of point sources
until the distance :math:`R_0 \approx L^2/\lambda` (Formula (B.1)) and a point
source beyond it, so a decay measured with a point excitation is made
shallower by 0,3 or 0,5 in the exponent up to :math:`R_0` (Formula (B.2)).

**What is not here.** Clause 6, the phases of a prediction, and Annex D are
work plans. The worked example of Annex C prints its emission and building
terms as inputs: its sum, its chain to a peak velocity and the arithmetic of
Formula (11) are conformance rows, and where the print does not reproduce
itself the entry is in ``docs/ERRATA.md``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.validation import (
    require_choice,
    require_finite_array,
    require_non_negative,
    require_positive,
)
from .railway import VELOCITY_LEVEL_REFERENCE_MM_S, band_sum_level
from .train_categories import TRAIN_KB_FMAX_FACTOR

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "FLOOR_NATURAL_FREQUENCIES_HZ",
    "FOUNDATION_TO_FLOOR_DB",
    "FOUNDATION_TO_FLOOR_RATIOS",
    "GEOMETRIC_DECAY_EXPONENT_RANGE",
    "GROUND_TO_FLOOR_DB",
    "GROUND_TO_FOUNDATION_DB",
    "KB_ASSESSMENT_BANDS_HZ",
    "KB_WEIGHTING_TABLE_DB",
    "LINE_SOURCE_EXPONENT_CORRECTION",
    "PEAK_VELOCITY_FACTOR",
    "PREDICTION_BAND_CENTRES_HZ",
    "RECOMMENDED_DISTANCES_M",
    "SPEED_RESCALING_LIMIT",
    "TAKT_MAXIMUM_FACTOR",
    "TrainCategoryPrediction",
    "foundation_to_floor_transfer_db",
    "ground_attenuation_coefficient_per_m",
    "ground_to_floor_transfer_db",
    "ground_to_foundation_transfer_db",
    "ground_transmission_db",
    "kb_weighted_levels_db",
    "line_source_correction_db",
    "peak_velocity_from_kb_mm_s",
    "point_to_line_transition_distance_m",
    "predict_floor_spectrum",
    "predict_train_category",
    "rescale_emission_for_speed",
    "takt_maximum_kb",
    "train_decay_exponent",
    "train_velocity_ratio",
    "velocity_spectrum_um_s",
]

#: The nominal third-octave centres of a prediction, 4 Hz to 250 Hz (Clause
#: 5.2 and Tables A.1, A.2 and C.1). Annex A prints 6, 12 and 62,5 for three
#: of them; the axis here is the nominal one.
PREDICTION_BAND_CENTRES_HZ: tuple[float, ...] = (
    4.0, 5.0, 6.3, 8.0, 10.0, 12.5, 16.0, 20.0, 25.0, 31.5, 40.0, 50.0, 63.0,
    80.0, 100.0, 125.0, 160.0, 200.0, 250.0,
)  # fmt: skip

#: The bands Formula (9) sums for the assessment quantities of DIN 4150-2,
#: 4 Hz to 80 Hz, which are the bands Table 2 weights.
KB_ASSESSMENT_BANDS_HZ: tuple[float, float] = (4.0, 80.0)

#: Table 2 (printed page 22): the KB weighting of DIN 45669-1 as a
#: third-octave correction in decibels, by nominal centre. Each value is
#: :math:`10 \lg (1 / (1 + (5{,}6\ \mathrm{Hz} / f)^2))` rounded to a tenth:
#: the weighting alone, without the band limitation of the meter, whose
#: place the draft's limit of the sum to the bands from 4 Hz to 80 Hz takes.
KB_WEIGHTING_TABLE_DB: dict[float, float] = {
    4.0: -4.7,
    5.0: -3.5,
    6.3: -2.5,
    8.0: -1.7,
    10.0: -1.2,
    12.5: -0.8,
    16.0: -0.5,
    20.0: -0.3,
    25.0: -0.2,
    31.5: -0.1,
    40.0: -0.1,
    50.0: -0.1,
    63.0: 0.0,
    80.0: 0.0,
}

#: Table 1 (printed page 8): the distance from the line, in metres, within
#: which the guide values of DIN 4150-2 are found exceeded by experience and
#: a prediction is recommended, by Zuggattung and by whether the line runs in
#: a tunnel or on the surface. The tunnel distance is from the foundation to
#: the outer contour of the tunnel. Freight in a tunnel has no experience
#: behind it and is ``None``; freight on the surface is the soft-soil case.
RECOMMENDED_DISTANCES_M: dict[str, dict[str, float | None]] = {
    "freight_soft_soil": {"tunnel": None, "surface": 200.0},
    "mainline": {"tunnel": 30.0, "surface": 60.0},
    "s_bahn": {"tunnel": 20.0, "surface": 40.0},
    "urban": {"tunnel": 20.0, "surface": 25.0},
}

#: The exponent :math:`n` of Formula (5) that surface rail traffic usually
#: takes, frequency-independent, 0,2 to 0,4 (Clause 5.3).
GEOMETRIC_DECAY_EXPONENT_RANGE: tuple[float, float] = (0.2, 0.4)

#: How far Formula (3) carries an emission spectrum to another speed: a
#: change of 30 %. Beyond it the sleeper-passing frequency :math:`f_a = v / a`
#: moves, and the spectrum with it (Clause 5.2).
SPEED_RESCALING_LIMIT: float = 0.3

#: :math:`c_{T1}` of Formula (9): 1 for the Max Hold spectra with the time
#: weighting Fast that Clause 5.2 asks for.
TAKT_MAXIMUM_FACTOR: float = 1.0

#: :math:`\beta` of Formula (12): the peak velocity is 3 times
#: :math:`KB_{F\mathrm{max},Zug}`, an empirical factor.
PEAK_VELOCITY_FACTOR: float = 3.0

#: Annex B: what to take off the exponent measured with a point excitation
#: to get the exponent of a train, up to the transition distance of Formula
#: (B.1): 0,3 when the point fit separated spreading and damping (Formula
#: (5)), 0,5 when it lumped both into a power law (Formula (6)).
LINE_SOURCE_EXPONENT_CORRECTION: dict[str, float] = {
    "power_and_damping": 0.3,
    "power_law": 0.5,
}

#: The natural frequencies of a floor Tables A.1 and A.2 give a column for,
#: in hertz; the print writes the tenth as 62,5.
FLOOR_NATURAL_FREQUENCIES_HZ: tuple[float, ...] = (
    8.0, 10.0, 12.5, 16.0, 20.0, 25.0, 31.5, 40.0, 50.0, 63.0, 80.0,
)  # fmt: skip

#: Tables A.1 and A.2 (printed pages 24 and 25): the level difference
#: :math:`\Delta L_{v,DB}` from the ground to a floor, in decibels, for a
#: building with concrete floors and one with timber floors, by the natural
#: frequency of the floor (the key) and along :data:`PREDICTION_BAND_CENTRES_HZ`.
#: Valid for every storey. From building measurements, not a formula.
GROUND_TO_FLOOR_DB: dict[str, dict[float, tuple[float, ...]]] = {
    "concrete": {
        8.0: (
            -0.51, 1.42, 6.88, 15.0, 5.87, 0.17, -1.26, -0.96, -2.58, -3.5, -3.47,
            -4.78, -5.0, -5.0, -5.0, -5.0, -5.0, -5.0, -5.0,
        ),
        10.0: (
            -1.34, -0.51, 1.42, 6.88, 15.0, 5.87, 0.17, -1.26, -0.96, -2.58, -3.5,
            -3.47, -4.78, -5.0, -5.0, -5.0, -5.0, -5.0, -5.0,
        ),
        12.5: (
            -1.48, -1.34, -0.51, 1.42, 6.88, 15.0, 5.87, 0.17, -1.26, -0.96, -2.58,
            -3.5, -3.47, -4.78, -5.0, -5.0, -5.0, -5.0, -5.0,
        ),
        16.0: (
            -1.38, -1.48, -1.34, -0.51, 1.42, 6.88, 15.0, 5.87, 0.17, -1.26, -0.96,
            -2.58, -3.5, -3.47, -4.78, -5.0, -5.0, -5.0, -5.0,
        ),
        20.0: (
            -1.41, -1.21, -1.3, -1.17, -0.44, 1.24, 6.02, 13.12, 5.13, 0.15, -1.1,
            -0.84, -2.26, -3.06, -3.47, -4.78, -5.0, -5.0, -5.0,
        ),
        25.0: (
            -1.3, -1.21, -1.04, -1.11, -1.0, -0.38, 1.07, 5.17, 11.26, 4.4, 0.13,
            -0.95, -0.72, -1.94, -2.26, -3.06, -3.47, -4.78, -5.0,
        ),
        31.5: (
            -1.25, -1.09, -1.02, -0.87, -0.94, -0.85, -0.32, 0.9, 4.36, 9.5, 3.72,
            0.11, -0.8, -0.72, -1.94, -2.26, -3.06, -3.47, -4.78,
        ),
        40.0: (
            -1.22, -1.25, -1.09, -1.02, -0.87, -0.94, -0.85, -0.32, 0.9, 4.36, 9.5,
            3.72, 0.11, -0.8, -0.72, -1.94, -2.26, -3.06, -3.47,
        ),
        50.0: (
            -1.63, -1.22, -1.25, -1.09, -1.02, -0.87, -0.94, -0.85, -0.32, 0.9,
            4.36, 9.5, 3.72, 0.11, -0.8, -0.72, -1.94, -2.26, -3.06,
        ),
        63.0: (
            -2.0, -1.63, -1.22, -1.25, -1.09, -1.02, -0.87, -0.94, -0.85, -0.32,
            0.9, 4.36, 9.5, 3.72, 0.11, -0.8, -0.72, -1.94, -2.26,
        ),
        80.0: (
            -2.5, -2.0, -1.63, -1.22, -1.25, -1.09, -1.02, -0.87, -0.94, -0.85,
            -0.32, 0.9, 4.36, 9.5, 3.72, 0.11, -0.8, -0.72, -1.94,
        ),
    },
    "timber": {
        8.0: (
            5.14, 7.55, 12.59, 20.0, 10.64, 4.36, 0.41, -2.25, -3.78, -4.6, -4.94,
            -5.0, -5.0, -5.0, -5.0, -5.0, -5.0, -5.0, -5.0,
        ),
        10.0: (
            3.77, 5.14, 7.55, 12.59, 20.0, 10.64, 4.36, 0.41, -2.25, -3.78, -4.6,
            -4.94, -5.0, -5.0, -5.0, -5.0, -5.0, -5.0, -5.0,
        ),
        12.5: (
            2.19, 3.39, 4.62, 6.79, 11.33, 18.0, 9.57, 3.92, 0.37, -2.03, -3.4,
            -4.14, -4.44, -4.51, -4.6, -4.94, -5.0, -5.0, -5.0,
        ),
        16.0: (
            0.99, 1.95, 3.01, 4.11, 6.03, 10.07, 16.0, 8.51, 3.49, 0.33, -1.8,
            -3.02, -3.67, -3.95, -4.14, -4.44, -4.51, -4.6, -4.94,
        ),
        20.0: (
            -0.18, 0.87, 1.71, 2.64, 3.6, 5.28, 8.81, 14.0, 7.45, 3.05, 0.29,
            -1.58, -2.65, -3.22, -3.67, -3.95, -4.14, -4.44, -4.51,
        ),
        25.0: (
            -0.49, -0.16, 0.74, 1.46, 2.26, 3.08, 4.53, 7.55, 12.0, 6.38, 2.61,
            0.24, -1.35, -2.27, -2.65, -3.22, -3.67, -3.95, -4.14,
        ),
        31.5: (
            -0.49, -0.41, -0.13, 0.62, 1.22, 1.88, 2.57, 3.77, 6.29, 10.0, 5.32,
            2.18, 0.2, -1.13, -1.35, -2.27, -2.65, -3.22, -3.67,
        ),
        40.0: (
            -0.24, -0.49, -0.41, -0.13, 0.62, 1.22, 1.88, 2.57, 3.77, 6.29, 10.0,
            5.32, 2.18, 0.2, -1.13, -1.35, -2.27, -2.65, -3.22,
        ),
        50.0: (
            -0.26, -0.24, -0.49, -0.41, -0.13, 0.62, 1.22, 1.88, 2.57, 3.77, 6.29,
            10.0, 5.32, 2.18, 0.2, -1.13, -1.35, -2.27, -2.65,
        ),
        63.0: (
            -0.5, -0.26, -0.24, -0.49, -0.41, -0.13, 0.62, 1.22, 1.88, 2.57, 3.77,
            6.29, 10.0, 5.32, 2.18, 0.2, -1.13, -1.35, -2.27,
        ),
        80.0: (
            -0.7, -0.5, -0.26, -0.24, -0.49, -0.41, -0.13, 0.62, 1.22, 1.88, 2.57,
            3.77, 6.29, 10.0, 5.32, 2.18, 0.2, -1.13, -1.35,
        ),
    },
}  # fmt: skip

#: Tables A.3 and A.4 (printed pages 26 and 27): the level difference
#: :math:`\Delta L_{v,FB}` from the ground into the foundation, in decibels,
#: for a basement and for a ground floor, as a mean over the buildings
#: measured with the deviation either way, along the 14 bands from 4 Hz to
#: 80 Hz. The print writes the 12,5 Hz row as 12.
GROUND_TO_FOUNDATION_DB: dict[str, dict[str, tuple[float, ...]]] = {
    "basement": {
        "lower": (
            -9.1, -8.2, -8.3, -8.7, -8.2, -8.3, -9.5, -12.5, -14.7, -15.6, -14.5,
            -13.1, -12.4, -11.6,
        ),
        "mean": (
            -4.0, -3.5, -3.6, -4.2, -4.2, -3.8, -4.6, -6.0, -8.2, -9.3, -7.4, -5.1,
            -4.4, -4.2,
        ),
        "upper": (
            1.0, 1.5, 1.1, 0.3, 0.1, 0.4, 0.3, -0.4, -2.1, -2.7, -0.1, 3.0, 3.4,
            3.1,
        ),
    },
    "ground_floor": {
        "lower": (
            -8.3, -7.0, -7.5, -6.4, -4.6, -4.3, -6.3, -7.0, -9.1, -10.7, -11.3,
            -10.0, -11.2, -9.8,
        ),
        "mean": (
            -3.2, -3.0, -3.9, -3.0, -2.2, -1.9, -3.1, -4.2, -5.8, -6.4, -5.7, -4.9,
            -5.3, -4.7,
        ),
        "upper": (
            1.7, 1.1, 0.0, 0.3, -0.5, 0.4, -0.4, -1.4, -1.8, -2.5, -0.7, 0.3, 0.4,
            0.8,
        ),
    },
}  # fmt: skip

#: The ratios :math:`f_{Tn} / f_e` of the band to the natural frequency of
#: the floor that Tables A.5 and A.6 tabulate, on the third-octave grid from
#: 0,05 to 8; the print writes 0,06, 0,12, 0,31 and 3,10 for four of them.
FOUNDATION_TO_FLOOR_RATIOS: tuple[float, ...] = (
    0.05, 0.063, 0.08, 0.1, 0.125, 0.16, 0.2, 0.25, 0.315, 0.4, 0.5, 0.63, 0.8,
    1.0, 1.25, 1.6, 2.0, 2.5, 3.15, 4.0, 5.0, 6.3, 8.0,
)  # fmt: skip

#: Tables A.5 and A.6 (printed pages 27 to 29): the level difference
#: :math:`\Delta L_{v,DF}` from the foundation to a floor, in decibels, for
#: concrete and for timber floors, against :data:`FOUNDATION_TO_FLOOR_RATIOS`,
#: as a mean with the deviation either way; ``nan`` where the table prints
#: no value. The concrete table stops at a ratio of 5, the timber one begins
#: at 0,08 and its mean alone reaches 8. The timber table prints its lower
#: deviation above its mean at the ratios 0,2, 3,15, 4 and 5, and above its
#: upper one at 5, so no order between the three is enforced.
FOUNDATION_TO_FLOOR_DB: dict[str, dict[str, tuple[float, ...]]] = {
    "concrete": {
        "lower": (
            -1.52, -1.53, -1.74, -2.42, -2.63, -1.89, -1.81, -1.73, -1.27, -0.72,
            0.02, 1.43, 6.05, 9.78, 4.52, 0.12, -3.27, -4.14, -5.29, -1.96, -1.38,
            math.nan, math.nan,
        ),
        "mean": (
            0.29, 0.93, 0.72, 1.09, 0.98, 1.62, 1.6, 2.06, 2.52, 3.26, 4.19, 6.35,
            9.94, 17.26, 9.85, 4.41, 3.27, 3.25, 1.42, 3.89, 2.83, math.nan,
            math.nan,
        ),
        "upper": (
            2.37, 4.16, 3.85, 5.17, 5.15, 5.51, 5.49, 6.42, 6.88, 7.24, 8.74,
            11.76, 17.46, 24.23, 17.07, 11.11, 10.23, 10.21, 8.38, 10.25, 7.9,
            math.nan, math.nan,
        ),
    },
    "timber": {
        "lower": (
            math.nan, math.nan, 0.64, 1.05, 0.52, 1.87, 2.37, 2.45, 2.6, 2.76,
            3.43, 5.98, 8.62, 15.29, 9.88, 6.26, 5.13, 5.28, 5.26, 5.42, 7.63,
            math.nan, math.nan,
        ),
        "mean": (
            math.nan, math.nan, math.nan, math.nan, 3.14, 3.06, 2.19, 4.87, 6.55,
            7.74, 8.29, 10.47, 17.4, 21.93, 14.81, 11.54, 9.54, 5.4, 3.55, 3.24,
            3.01, 3.35, 1.85,
        ),
        "upper": (
            math.nan, math.nan, math.nan, math.nan, math.nan, math.nan, math.nan,
            8.1, 11.09, 14.84, 15.68, 16.61, 23.36, 28.84, 22.39, 18.26, 15.24,
            14.03, 10.07, 6.88, 5.4, math.nan, math.nan,
        ),
    },
}  # fmt: skip

_FLOORS = tuple(GROUND_TO_FLOOR_DB)
_LEVELS = tuple(GROUND_TO_FOUNDATION_DB)
_STATISTICS = ("mean", "lower", "upper")
_FITS = tuple(LINE_SOURCE_EXPONENT_CORRECTION)
#: Half a sixth of an octave, the tolerance within which a frequency is
#: taken to be a nominal centre.
_BAND_TOLERANCE = 2.0 ** (1.0 / 12.0)
#: The bands the KB assessment sums: Table 2 has 14 of them.
_KB_BAND_COUNT = len(KB_WEIGHTING_TABLE_DB)
#: The micrometres in a millimetre, for Formula (13).
_UM_PER_MM = 1000.0


def _levels(values: ArrayLike, name: str) -> NDArray[np.float64]:
    return require_finite_array(values, name)


def _nominal(frequencies_hz: ArrayLike, table: tuple[float, ...]) -> NDArray[np.intp]:
    """The index of each frequency in a nominal table, or an error."""
    freqs = require_finite_array(frequencies_hz, "frequencies_hz")
    if np.any(freqs <= 0.0):
        msg = "'frequencies_hz' must be positive."
        raise ValueError(msg)
    grid = np.asarray(table, dtype=np.float64)
    ratio = freqs[:, None] / grid[None, :]
    hit = (ratio < _BAND_TOLERANCE) & (ratio > 1.0 / _BAND_TOLERANCE)
    if not np.all(hit.any(axis=1)):
        missing = freqs[~hit.any(axis=1)]
        msg = (
            f"{missing.tolist()} Hz is not a nominal third-octave centre between "
            f"{grid[0]:g} Hz and {grid[-1]:g} Hz."
        )
        raise ValueError(msg)
    return np.asarray(hit.argmax(axis=1), dtype=np.intp)


def predict_floor_spectrum(
    emission_db: ArrayLike,
    *,
    ground_db: ArrayLike = 0.0,
    foundation_db: ArrayLike = 0.0,
    floor_db: ArrayLike = 0.0,
    mitigation_db: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    r"""The predicted spectrum on a floor, Formula (1).

    Every term is added, band by band, as the formula prints it: the
    emission spectrum, the transmission through the ground, the transfer
    into the foundation, the transfer to the floor and the effect of the
    mitigation. The Annex A tables are negative where they attenuate, and a
    mitigation must be too, which is why the term is not called an insertion
    loss here: the formula prints :math:`D_e` with a plus sign and names
    DIN 45673-1 for it, and an insertion loss in the sense of DIN 45672-2
    Annex B, :func:`~phonometry.vibration.elastic_insertion_loss`, is
    positive where the element reduces the level, so it goes in with its
    sign changed. An emission spectrum measured at the foundation makes the
    foundation term zero (Annex C does exactly that).

    :param emission_db: :math:`L_{v,E}`, one level per band, in decibels.
    :param ground_db: :math:`\Delta L_{v,BB}`, per band or one value.
    :param foundation_db: :math:`\Delta L_{v,FB}`, per band or one value.
    :param floor_db: :math:`\Delta L_{v,DF}`, per band or one value.
    :param mitigation_db: :math:`D_e`, per band or one value, added as
        printed, so negative for a mitigation.
    :return: :math:`L_v`, one level per band.
    :raises ValueError: For a non-finite input or a term that does not
        broadcast to the emission spectrum.
    """
    levels = _levels(emission_db, "emission_db")
    total = levels.copy()
    for name, term in (
        ("ground_db", ground_db),
        ("foundation_db", foundation_db),
        ("floor_db", floor_db),
        ("mitigation_db", mitigation_db),
    ):
        values = np.asarray(term, dtype=np.float64)
        if not np.all(np.isfinite(values)):
            msg = f"'{name}' must be finite."
            raise ValueError(msg)
        try:
            total = total + np.broadcast_to(values, levels.shape)
        except ValueError as error:
            msg = f"'{name}' must be one value or one per band of 'emission_db'."
            raise ValueError(msg) from error
    return total


def rescale_emission_for_speed(
    levels_db: ArrayLike, *, speed_from_km_h: float, speed_to_km_h: float
) -> NDArray[np.float64]:
    r"""An emission spectrum carried to another train speed, Formula (3).

    :math:`L_{v,E2} = L_{v,E1} + 20 \lg (v_2 / v_1)`, the same shift in every
    band, for the same category of train under the same conditions and a
    change of speed of up to 30 %. Beyond that the frequencies bound to a
    length, the sleeper-passing frequency :math:`f_a = v / a` for one, move
    with the speed while the resonances do not, and the shift is refused.

    :param levels_db: :math:`L_{v,E1}`, the spectrum measured at the first
        speed, in decibels.
    :param speed_from_km_h: :math:`v_1`, the speed it was measured at.
    :param speed_to_km_h: :math:`v_2`, the speed wanted, in the same unit.
    :return: :math:`L_{v,E2}`.
    :raises ValueError: For a non-positive speed, a change of more than 30 %,
        or a non-finite spectrum.
    """
    levels = _levels(levels_db, "levels_db")
    v_1 = require_positive(speed_from_km_h, "speed_from_km_h")
    v_2 = require_positive(speed_to_km_h, "speed_to_km_h")
    change = abs(v_2 / v_1 - 1.0)
    if change > SPEED_RESCALING_LIMIT and not math.isclose(
        change, SPEED_RESCALING_LIMIT
    ):
        msg = (
            f"Formula (3) holds for a change of speed of up to {SPEED_RESCALING_LIMIT:.0%}; "
            f"{v_1:g} to {v_2:g} is {abs(v_2 / v_1 - 1.0):.0%}."
        )
        raise ValueError(msg)
    return levels + 20.0 * math.log10(v_2 / v_1)


def ground_attenuation_coefficient_per_m(
    frequencies_hz: ArrayLike, *, damping_ratio: float, shear_wave_speed_m_s: float
) -> NDArray[np.float64]:
    r"""The material damping of the ground, :math:`\alpha_R` of Clause 5.3.

    :math:`\alpha_R(f) = 2\pi D / \lambda_R = 2\pi f D / c_s`: the damping
    ratio of the ground over the wavelength, which the standard writes with
    the shear wave speed although the wave is the surface wave, and that is
    how it is computed here.

    :param frequencies_hz: The band centres, in hertz.
    :param damping_ratio: :math:`D`, the damping ratio of the ground.
    :param shear_wave_speed_m_s: :math:`c_s`, in metres per second.
    :return: :math:`\alpha_R`, in reciprocal metres, one per band.
    :raises ValueError: For a negative damping ratio, a non-positive speed
        or a non-positive frequency.
    """
    freqs = require_finite_array(frequencies_hz, "frequencies_hz")
    if np.any(freqs <= 0.0):
        msg = "'frequencies_hz' must be positive."
        raise ValueError(msg)
    damping = require_non_negative(damping_ratio, "damping_ratio")
    speed = require_positive(shear_wave_speed_m_s, "shear_wave_speed_m_s")
    return 2.0 * math.pi * freqs * damping / speed


def ground_transmission_db(
    frequencies_hz: ArrayLike,
    *,
    distance_m: float,
    reference_distance_m: float,
    exponent: ArrayLike,
    damping_ratio: float | None = None,
    shear_wave_speed_m_s: float | None = None,
) -> NDArray[np.float64]:
    r"""The transmission through the ground, Formulae (4) to (6).

    Formula (5) gives the ratio of the velocity at :math:`r` to that at
    :math:`r_0` as :math:`(r/r_0)^{-n} e^{-\alpha_R(f)(r - r_0)}`, geometric
    spreading with the exponent :math:`n` and material damping with
    :math:`\alpha_R` of :func:`ground_attenuation_coefficient_per_m`, and
    Formula (4) takes 20 lg of it. With the damping left out and an
    exponent per band it is Formula (6), the power law with the exponent
    measured on site for every band. On the surface the standard usually
    takes :math:`n` between 0,2 and 0,4, frequency-independent; a train is a
    line of point sources, and Annex B says what to take off an exponent
    measured with a point excitation.

    :param frequencies_hz: The band centres, in hertz.
    :param distance_m: :math:`r`, from the source to the ground in front of
        the building or to its foundation.
    :param reference_distance_m: :math:`r_0`, where the emission spectrum
        was taken.
    :param exponent: :math:`n`, one value or one per band.
    :param damping_ratio: :math:`D` of the ground; ``None`` (default) leaves
        the material damping out.
    :param shear_wave_speed_m_s: :math:`c_s`, needed with a damping ratio.
    :return: :math:`\Delta L_{v,BB}`, in decibels, one per band; negative
        where the building is further from the source than the reference.
    :raises ValueError: For a non-positive distance, a negative exponent or
        damping, a damping ratio without a wave speed, or an exponent that
        does not broadcast to the bands.
    """
    freqs = require_finite_array(frequencies_hz, "frequencies_hz")
    distance = require_positive(distance_m, "distance_m")
    reference = require_positive(reference_distance_m, "reference_distance_m")
    exponents = np.asarray(exponent, dtype=np.float64)
    if not np.all(np.isfinite(exponents)) or np.any(exponents < 0.0):
        msg = "'exponent' must be finite and not negative."
        raise ValueError(msg)
    try:
        exponents = np.broadcast_to(exponents, freqs.shape)
    except ValueError as error:
        msg = "'exponent' must be one value or one per band."
        raise ValueError(msg) from error
    spreading = -20.0 * exponents * math.log10(distance / reference)
    if damping_ratio is None:
        return np.asarray(spreading, dtype=np.float64)
    damping = require_non_negative(damping_ratio, "damping_ratio")
    if shear_wave_speed_m_s is None:
        msg = "a damping ratio needs the shear wave speed for alpha_R."
        raise ValueError(msg)
    alpha = ground_attenuation_coefficient_per_m(
        freqs, damping_ratio=damping, shear_wave_speed_m_s=shear_wave_speed_m_s
    )
    return spreading - 20.0 * math.log10(math.e) * alpha * (distance - reference)


def ground_to_floor_transfer_db(
    floor: str, *, floor_natural_frequency_hz: float
) -> NDArray[np.float64]:
    r"""The level difference from the ground to a floor, Tables A.1 and A.2.

    :math:`\Delta L_{v,DB}` for a building with concrete or with timber floors
    whose floors have the given natural frequency, along
    :data:`PREDICTION_BAND_CENTRES_HZ`, for any storey. The tables print a
    column for each of :data:`FLOOR_NATURAL_FREQUENCIES_HZ` and no rule for
    a frequency between two, so the frequency has to be one of them. Clause
    5.4.4: run the prediction once for each natural frequency the building
    may have, and never with the envelope over all of them, which
    overestimates considerably.

    :param floor: ``"concrete"`` or ``"timber"``.
    :param floor_natural_frequency_hz: :math:`f_e`, one of the tabulated
        frequencies.
    :return: :math:`\Delta L_{v,DB}`, in decibels, one per band.
    :raises ValueError: For an unknown floor or a frequency the tables have
        no column for.
    """
    table = GROUND_TO_FLOOR_DB[require_choice(str(floor), "floor", _FLOORS)]
    index = _nominal([floor_natural_frequency_hz], FLOOR_NATURAL_FREQUENCIES_HZ)
    return np.asarray(table[FLOOR_NATURAL_FREQUENCIES_HZ[int(index[0])]])


def ground_to_foundation_transfer_db(
    level: str, *, statistic: str = "mean"
) -> NDArray[np.float64]:
    r"""The level difference from the ground into the foundation, Tables A.3 and A.4.

    :math:`\Delta L_{v,FB}` for a basement or for a foundation at ground
    level, along the 14 bands from 4 Hz to 80 Hz, as the mean of the
    buildings measured or the mean less or plus its deviation. The tables
    stop at 80 Hz where the others run to 250 Hz, so the result enters
    :func:`predict_floor_spectrum` only with an emission spectrum cut to the
    same 14 bands, or padded with zeros above them by the caller.

    :param level: ``"basement"`` or ``"ground_floor"``.
    :param statistic: ``"mean"`` (default), ``"lower"`` or ``"upper"``.
    :return: :math:`\Delta L_{v,FB}`, in decibels, one per band from 4 Hz to
        80 Hz.
    :raises ValueError: For an unknown level or statistic.
    """
    table = GROUND_TO_FOUNDATION_DB[require_choice(str(level), "level", _LEVELS)]
    return np.asarray(table[require_choice(str(statistic), "statistic", _STATISTICS)])


def foundation_to_floor_transfer_db(
    frequencies_hz: ArrayLike,
    *,
    floor: str,
    floor_natural_frequency_hz: float,
    statistic: str = "mean",
) -> NDArray[np.float64]:
    r"""The level difference from the foundation to a floor, Tables A.5 and A.6.

    :math:`\Delta L_{v,DF}` against the ratio of the band to the natural
    frequency of the floor, for concrete or for timber floors, as the mean
    or the mean less or plus its deviation. The tables are read at the ratio
    of each band; a ratio between two tabulated ones is interpolated
    linearly in decibels over the logarithm of the ratio, and a ratio the
    table has no value for gives ``nan``.

    :param frequencies_hz: The band centres, in hertz.
    :param floor: ``"concrete"`` or ``"timber"``.
    :param floor_natural_frequency_hz: :math:`f_e`, positive.
    :param statistic: ``"mean"`` (default), ``"lower"`` or ``"upper"``.
    :return: :math:`\Delta L_{v,DF}`, in decibels, one per band, ``nan``
        outside the table.
    :raises ValueError: For an unknown floor or statistic, a non-positive
        frequency, or a non-finite input.
    """
    freqs = require_finite_array(frequencies_hz, "frequencies_hz")
    if np.any(freqs <= 0.0):
        msg = "'frequencies_hz' must be positive."
        raise ValueError(msg)
    natural = require_positive(floor_natural_frequency_hz, "floor_natural_frequency_hz")
    table = FOUNDATION_TO_FLOOR_DB[require_choice(str(floor), "floor", _FLOORS)]
    values = np.asarray(table[require_choice(str(statistic), "statistic", _STATISTICS)])
    known = np.isfinite(values)
    grid = np.log10(np.asarray(FOUNDATION_TO_FLOOR_RATIOS)[known])
    ratio = np.log10(freqs / natural)
    out = np.interp(ratio, grid, values[known], left=math.nan, right=math.nan)
    # A gap inside the table (the timber deviations) is not bridged: a ratio
    # between two tabulated ones with no value on one side stays nan.
    gaps = np.flatnonzero(~known)
    all_ratios = np.log10(np.asarray(FOUNDATION_TO_FLOOR_RATIOS))
    for gap in gaps:
        lower = all_ratios[gap - 1] if gap > 0 else -math.inf
        upper = all_ratios[gap + 1] if gap + 1 < len(all_ratios) else math.inf
        out[(ratio > lower) & (ratio < upper)] = math.nan
    return np.asarray(out, dtype=np.float64)


def kb_weighted_levels_db(
    levels_db: ArrayLike, frequencies_hz: ArrayLike
) -> NDArray[np.float64]:
    r"""The KB-weighted third-octave levels, Formula (8) with Table 2.

    :math:`L_{v,KB}(f_{Tn}) = L_v(f_{Tn}) + L_{KB}(f_{Tn})`: the correction of
    Table 2, the KB weighting of DIN 45669-1 rounded to a tenth of a
    decibel, added to each band from 4 Hz to 80 Hz. Bands outside those are
    not weighted by the table and are refused.

    :param levels_db: :math:`L_v`, one level per band, in decibels.
    :param frequencies_hz: The band centres, nominal, 4 Hz to 80 Hz.
    :return: :math:`L_{v,KB}`, one per band.
    :raises ValueError: For a band outside Table 2, or mismatched inputs.
    """
    levels = _levels(levels_db, "levels_db")
    index = _nominal(frequencies_hz, tuple(KB_WEIGHTING_TABLE_DB))
    if index.shape != levels.shape:
        msg = "'levels_db' and 'frequencies_hz' must match, one level per band."
        raise ValueError(msg)
    weights = np.asarray(list(KB_WEIGHTING_TABLE_DB.values()))[index]
    return levels + weights


def takt_maximum_kb(weighted_levels_db: ArrayLike) -> float:
    r"""The clock maximum r.m.s. of a category from its spectrum, Formula (9).

    :math:`KB_{FTm,Zug} = c_{T1} v_0 10^{L_{v,ges}/20}` with :math:`L_{v,ges}`
    the energy sum of the KB-weighted bands from 4 Hz to 80 Hz,
    :math:`c_{T1}` = 1 for Max Hold spectra with the time weighting Fast and
    :math:`v_0 = 5 \cdot 10^{-5}` mm/s, the reference of the velocity level;
    the value is the KB quantity because KB is the velocity in millimetres
    per second. Annex C prints 0,4 for a sum level of 78,1 dB.

    :param weighted_levels_db: :math:`L_{v,KB}`, as
        :func:`kb_weighted_levels_db` gives them, one per band.
    :return: :math:`KB_{FTm,Zug}`, dimensionless.
    :raises ValueError: For an empty or non-finite input.
    """
    levels = _levels(weighted_levels_db, "weighted_levels_db")
    total = band_sum_level(levels)
    return float(
        TAKT_MAXIMUM_FACTOR * VELOCITY_LEVEL_REFERENCE_MM_S * 10.0 ** (total / 20.0)
    )


def peak_velocity_from_kb_mm_s(kb_fmax_zug: float) -> float:
    r"""The peak velocity of a category, Formula (12).

    :math:`v_{\max} = \beta \, KB_{F\mathrm{max},Zug}` with :math:`\beta` = 3,
    an empirical factor, which is the number a DIN 4150-3 comparison wants.

    :param kb_fmax_zug: :math:`KB_{F\mathrm{max},Zug}` of Formula (10).
    :return: :math:`v_{\max}`, in millimetres per second.
    :raises ValueError: For a negative input.
    """
    return PEAK_VELOCITY_FACTOR * require_non_negative(kb_fmax_zug, "kb_fmax_zug")


def velocity_spectrum_um_s(levels_db: ArrayLike) -> NDArray[np.float64]:
    r"""A level spectrum as a velocity spectrum, Formula (13).

    :math:`v_{RMS}(f_{Tn}) = 1000 \, v_0 \, 10^{L_v(f_{Tn})/20}` in micrometres
    per second, the form the VC curves of VDI 2038 Blatt 2 are drawn in.

    :param levels_db: :math:`L_v`, one level per band, in decibels.
    :return: :math:`v_{RMS}`, one per band, in micrometres per second.
    :raises ValueError: For a non-finite input.
    """
    levels = _levels(levels_db, "levels_db")
    return _UM_PER_MM * VELOCITY_LEVEL_REFERENCE_MM_S * 10.0 ** (levels / 20.0)


@dataclass(frozen=True)
class TrainCategoryPrediction:
    r"""The prediction for one category of train, Clauses 5 and 7.

    :ivar frequencies_hz: The band centres.
    :ivar emission_db: :math:`L_{v,E}` the prediction started from.
    :ivar floor_db: :math:`L_v` of Formula (1), the spectrum on the floor.
    :ivar weighted_frequencies_hz: The band centres from 4 Hz to 80 Hz the
        KB assessment sums.
    :ivar weighted_db: :math:`L_{v,KB}` of Formula (8) over those bands.
    :ivar sum_level_db: :math:`L_{v,ges}` of Formula (9), the energy sum of
        the weighted bands.
    :ivar kb_ftm: :math:`KB_{FTm,Zug}` of Formula (9).
    :ivar kb_fmax: :math:`KB_{F\mathrm{max},Zug}` of Formula (10).
    :ivar peak_velocity_mm_s: :math:`v_{\max}` of Formula (12).
    """

    frequencies_hz: NDArray[np.float64]
    emission_db: NDArray[np.float64]
    floor_db: NDArray[np.float64]
    weighted_frequencies_hz: NDArray[np.float64]
    weighted_db: NDArray[np.float64]
    sum_level_db: float
    kb_ftm: float
    kb_fmax: float
    peak_velocity_mm_s: float

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the emission, the floor spectrum and the KB-weighted bands.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.vibration.plot_train_category_prediction`.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_train_category_prediction

        check_language(language)
        return plot_train_category_prediction(self, ax=ax, language=language, **kwargs)


def predict_train_category(
    emission_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike = PREDICTION_BAND_CENTRES_HZ,
    ground_db: ArrayLike = 0.0,
    foundation_db: ArrayLike = 0.0,
    floor_db: ArrayLike = 0.0,
    mitigation_db: ArrayLike = 0.0,
) -> TrainCategoryPrediction:
    r"""Run the chain from an emission spectrum to the assessment quantities.

    Formula (1) for the spectrum on the floor, Formula (8) for the
    KB-weighted bands from 4 Hz to 80 Hz, Formula (9) for the clock maximum
    r.m.s. of the category, Formula (10) for its :math:`KB_{F\mathrm{max}}`
    and Formula (12) for the peak velocity. The assessment vibration
    severity over the categories of a timetable is Formula (11), the sum of
    :func:`~phonometry.vibration.train_assessment_severity`, which also
    applies the rule of E DIN 4150-2:2023-08 that Formula (11) leaves out, a
    category at or below 0,1 counting as zero.

    :param emission_db: :math:`L_{v,E}`, one level per band, in decibels.
    :param frequencies_hz: The band centres, nominal; the 19 bands from 4 Hz
        to 250 Hz by default, and at least the 14 from 4 Hz to 80 Hz.
    :param ground_db: :math:`\Delta L_{v,BB}`, per band or one value.
    :param foundation_db: :math:`\Delta L_{v,FB}`, per band or one value.
    :param floor_db: :math:`\Delta L_{v,DF}`, per band or one value.
    :param mitigation_db: :math:`D_e`, per band or one value, added as
        printed, so negative for a mitigation.
    :return: The chain, as a :class:`TrainCategoryPrediction`.
    :raises ValueError: For a spectrum that does not hold the 14 bands of
        the KB assessment, or a bad term.
    """
    freqs = require_finite_array(frequencies_hz, "frequencies_hz")
    levels = _levels(emission_db, "emission_db")
    if freqs.shape != levels.shape:
        msg = "'emission_db' and 'frequencies_hz' must match, one level per band."
        raise ValueError(msg)
    floor = predict_floor_spectrum(
        levels,
        ground_db=ground_db,
        foundation_db=foundation_db,
        floor_db=floor_db,
        mitigation_db=mitigation_db,
    )
    low, high = KB_ASSESSMENT_BANDS_HZ
    inside = (freqs >= low / _BAND_TOLERANCE) & (freqs <= high * _BAND_TOLERANCE)
    if int(np.count_nonzero(inside)) != _KB_BAND_COUNT:
        msg = (
            f"the KB assessment sums the {_KB_BAND_COUNT} bands from {low:g} Hz to "
            f"{high:g} Hz; the spectrum holds {int(np.count_nonzero(inside))} of them."
        )
        raise ValueError(msg)
    weighted = kb_weighted_levels_db(floor[inside], freqs[inside])
    kb_ftm = takt_maximum_kb(weighted)
    kb_fmax = TRAIN_KB_FMAX_FACTOR * kb_ftm
    return TrainCategoryPrediction(
        frequencies_hz=freqs,
        emission_db=levels,
        floor_db=floor,
        weighted_frequencies_hz=freqs[inside],
        weighted_db=weighted,
        sum_level_db=band_sum_level(weighted),
        kb_ftm=kb_ftm,
        kb_fmax=kb_fmax,
        peak_velocity_mm_s=peak_velocity_from_kb_mm_s(kb_fmax),
    )


def point_to_line_transition_distance_m(
    train_length_m: float, *, wavelength_m: float
) -> float:
    r"""Where a train stops being a line source, Formula (B.1).

    :math:`R_0 \approx L^2 / \lambda`: nearer than that a train of length
    :math:`L` is a line of point sources and its surface waves spread less
    than a point's; further away it is a point source. Within the distances
    of Table 1 the line behaviour is the rule.

    :param train_length_m: :math:`L`, in metres.
    :param wavelength_m: :math:`\lambda` at the band of interest, in metres.
    :return: :math:`R_0`, in metres.
    :raises ValueError: For a non-positive length or wavelength.
    """
    length = require_positive(train_length_m, "train_length_m")
    wavelength = require_positive(wavelength_m, "wavelength_m")
    return length**2 / wavelength


def line_source_correction_db(
    distance_m: float, *, reference_distance_m: float, exponent_correction: float
) -> float:
    r"""The correction of a point-source decay to a train, Formula (B.2).

    :math:`\Delta L_{v,Korr} = 20 \, n_{Korr} \lg(r / r_0)`, added to the level
    a point excitation predicts, with :math:`n_{Korr}` between 0,3 and 0,5:
    the train spreads less than the point did, up to the distance of
    Formula (B.1).

    :param distance_m: :math:`r`, in metres.
    :param reference_distance_m: :math:`r_0`, in metres.
    :param exponent_correction: :math:`n_{Korr}`, 0,3 to 0,5.
    :return: :math:`\Delta L_{v,Korr}`, in decibels.
    :raises ValueError: For a non-positive distance or a correction outside
        0,3 to 0,5.
    """
    distance = require_positive(distance_m, "distance_m")
    reference = require_positive(reference_distance_m, "reference_distance_m")
    low, high = sorted(LINE_SOURCE_EXPONENT_CORRECTION.values())
    correction = float(exponent_correction)
    if not low <= correction <= high:
        msg = f"'exponent_correction' is {low:g} to {high:g} in Annex B, got {correction!r}."
        raise ValueError(msg)
    return 20.0 * correction * math.log10(distance / reference)


def train_decay_exponent(
    point_exponent: float, *, fitted_with: str = "power_and_damping"
) -> float:
    r"""The decay exponent of a train from that of a point excitation, Annex B.

    :math:`n_{Zug} = n_{Punkt} - 0{,}3` when the point measurement was fitted
    with spreading and damping apart (Formula (5)), :math:`n_{Punkt} - 0{,}5`
    when it was fitted as a power law alone (Formula (6)); both up to the
    transition distance of Formula (B.1), beyond which the point exponent
    holds as it is. The annex prints no floor, so a point exponent below the
    correction gives a negative result, as printed.

    :param point_exponent: :math:`n_{Punkt}`, not negative.
    :param fitted_with: ``"power_and_damping"`` (default) or ``"power_law"``.
    :return: :math:`n_{Zug}`.
    :raises ValueError: For a negative exponent or an unknown fit.
    """
    exponent = require_non_negative(point_exponent, "point_exponent")
    correction = LINE_SOURCE_EXPONENT_CORRECTION[
        require_choice(str(fitted_with), "fitted_with", _FITS)
    ]
    return exponent - correction


def train_velocity_ratio(
    distance_m: ArrayLike,
    *,
    reference_distance_m: float,
    transition_distance_m: float,
    point_exponent: float,
    exponent_correction: float,
) -> NDArray[np.float64]:
    r"""The decay of a train's vibration with distance, Figure B.1.

    The ratio of the velocity at :math:`r` to that at :math:`r_0`, as the
    figure draws it: a power law with the exponent
    :math:`n_{Punkt} - n_{Korr}` up to the transition distance :math:`R_0` of
    Formula (B.1), and the point exponent :math:`n_{Punkt}` beyond it,
    continuous at :math:`R_0`. The figure is a sketch and prints no closed
    form; this is its reading.

    :param distance_m: :math:`r`, in metres, one or many.
    :param reference_distance_m: :math:`r_0`, in metres.
    :param transition_distance_m: :math:`R_0`, in metres.
    :param point_exponent: :math:`n_{Punkt}`.
    :param exponent_correction: :math:`n_{Korr}`, 0,3 to 0,5.
    :return: :math:`v(r) / v(r_0)`, one per distance.
    :raises ValueError: For a non-positive distance, a reference beyond the
        transition, a negative exponent or a correction outside Annex B.
    """
    distances = require_finite_array(distance_m, "distance_m")
    if np.any(distances <= 0.0):
        msg = "'distance_m' must be positive."
        raise ValueError(msg)
    reference = require_positive(reference_distance_m, "reference_distance_m")
    transition = require_positive(transition_distance_m, "transition_distance_m")
    if transition < reference:
        msg = "'transition_distance_m' must not be nearer than 'reference_distance_m'."
        raise ValueError(msg)
    exponent = require_non_negative(point_exponent, "point_exponent")
    low, high = sorted(LINE_SOURCE_EXPONENT_CORRECTION.values())
    correction = float(exponent_correction)
    if not low <= correction <= high:
        msg = f"'exponent_correction' is {low:g} to {high:g} in Annex B, got {correction!r}."
        raise ValueError(msg)
    line = exponent - correction
    near = (distances / reference) ** (-line)
    at_transition = (transition / reference) ** (-line)
    far = at_transition * (distances / transition) ** (-exponent)
    return np.asarray(np.where(distances <= transition, near, far), dtype=np.float64)
