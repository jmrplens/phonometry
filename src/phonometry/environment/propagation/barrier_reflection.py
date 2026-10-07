#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""What a noise barrier sends back across the road, measured where it stands (EN 1793-5:2016).

EN 1793-1 rates the absorption of a barrier in a reverberation room, on a
sample lying on the floor and a sound field arriving from every direction.
Beside a road the sound arrives from one side, the product is standing up,
and it is not the sample that was tested. EN 1793-5 measures the same property
in place, with a loudspeaker and nine microphones in front of the device, and
calls it the **sound reflection index** :math:`RI`: the energy the device
reflects in each one-third octave band, as a fraction of what arrives.

The measurement
---------------

A loudspeaker stands :math:`d_S` = 1,50 m in front of the reference plane of
the device, at half its height. A vertical 3 x 3 grid of microphones, 0,40 m
apart, stands between them with its centre 0,25 m from the plane, so 1,25 m
from the loudspeaker. Each microphone records two impulse responses: one in
front of the device, and one in free field with the loudspeaker and the grid
turned away from everything, the ground included.

In front of the device the direct sound and the reflection overlap in the
first milliseconds. The free-field record *is* the direct sound, so it is
aligned onto the other record to a fiftieth of a sample, scaled to its peak and
subtracted (5.5.4, :func:`subtract_direct_sound`). What is left is the
reflection, and what cannot be removed is measured by the reduction factor
:math:`R_{sub}` of Formula (6).

The two components are then cut out with the **Adrienne temporal window**
(5.5.5, :func:`adrienne_reflection_window`): a 0,5 ms left half of a
four-term Blackman-Harris window, a flat part, and a right half whose length is
3/7 of the flat part. The marker point where the flat part begins is placed
0,2 ms before the peak of each component (5.5.6).

The index
---------

Formula (1) averages, over the microphones, the ratio of the reflected to the
incident energy in each band, with three corrections; the gain factor divides
here, as the library computes it (see below):

.. math::

   RI_j = \frac{1}{n_j} \sum_{k=1}^{n_j}
   \frac{\int_{\Delta f_j} |F[h_{r,k}(t)\, w_{r,k}(t)]|^2\, df}
        {\int_{\Delta f_j} |F[h_{i,k}(t)\, w_{i,k}(t)]|^2\, df}
   \, C_{geo,k}\, C_{dir,k}(\Delta f_j)\, /\, C_{gain,k}(\Delta f_g)

* :math:`C_{geo,k} = (d_{r,k}/d_{i,k})^2` puts back the spherical spreading of
  the longer reflected path (Formula (2), Table 2).
* :math:`C_{dir,k}` puts back the loudspeaker directivity: the reflection left
  the loudspeaker at another angle than the direct sound (Formula (3),
  :func:`source_directivity_corrections`).
* :math:`C_{gain,k}` takes out a change of amplifier or microphone gain
  between the free-field and the in-front configurations (Formula (4)).

The last correction is a **division** here. Formula (1) prints it as a
multiplier, but Formula (4) defines it as the in-front incident energy over
the free-field one, which is the gain change itself; multiplying by it would
square the change rather than remove it. docs/ERRATA.md records the case.

In the bands of 100 Hz, 125 Hz and 160 Hz the average is over microphones 1 to
6 with the 7,9 ms window; from 200 Hz over all nine with the 6,0 ms window
(5.5.5). A device measured at several grid positions averages every
microphone of every position (5.6.2.3); Annex B reports the positions one by
one and their mean, which :func:`reflection_index_from_positions` recomputes.

The single number
-----------------

:math:`DL_{RI}` weights :math:`RI` with the normalised traffic noise spectrum
of EN 1793-3 from the lowest reliable band upward (Formula (12)); it lives
with the other EN 1793 ratings as
:func:`~phonometry.environment.propagation.noise_reducing_devices.sound_reflection_rating`.

The low frequency limit
-----------------------

The window has to end before the ground reflection on the source side and the
waves diffracted by the edges of the device arrive, so a smaller device allows
a shorter window and a higher low frequency limit (5.5.7). The standard gives
the limit as three curves (Figure 14) without the formula behind them.
:func:`reflection_low_frequency_limit` computes it by the construction of the
method's authors (Garai and Guidorzi, J. Acoust. Soc. Am. 108 (2000) 1054,
section III.D): the window ends where the first unwanted component arrives,
and its low frequency limit is the first notch of its spectrum
(:func:`adrienne_low_frequency_limit_hz`, 162,5 Hz for 7,9 ms, which the
paper gives as about 160 Hz). Against the curves read off Figure 14 it
follows microphone 5 within 5 % from 2,75 m up (5,5 % below at 2,5 m). At
microphone 2 it comes out about 3 % to 10 % above the printed curve, set by
the top edge; at microphone 8 it is a third below the curve at 2,5 m, 6 %
below at 4,5 m and 3 % or less from 6 m up. The two outer curves
imply microphone heights the grid does not have, and could not be rebuilt.
The guide shows the comparison, and the lowest reliable band is left to the
caller.
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
from scipy.fft import next_fast_len
from scipy.optimize import minimize_scalar

from ..._internal.frozen import OwnsArrays, read_only
from ..._internal.validation import (
    require_choice,
    require_positive,
    require_ranks,
    require_same_length,
)
from ..._internal.warnings import PhonometryWarning
from ...io._resolve import (
    SignalInput,
    apply_calibration,
    like_input,
    require_signal_rate,
    resolve_pair_fs,
)
from ...io._signal import Signal
from ...materials.surfaces.road_absorption import max_sampled_area_radius
from . import noise_reducing_devices as _devices
from .noise_reducing_devices import RoadDeviceRating, sound_reflection_rating

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

#: The eighteen bands of EN 1793-3, 100 Hz to 5 kHz.
_BANDS_HZ: tuple[float, ...] = _devices.TRAFFIC_NOISE_BANDS_HZ

__all__ = [
    "ADRIENNE_CALIBRATION_LENGTH_S",
    "ADRIENNE_SHORT_LENGTH_S",
    "ADRIENNE_STANDARD_LENGTH_S",
    "REFLECTION_GRID_DISTANCES",
    "REFLECTION_GRID_SPACING_M",
    "REFLECTION_INDEX_PRECISION",
    "REFLECTION_LOW_BAND_MICROPHONES",
    "REFLECTION_MICROPHONE_DISTANCE_M",
    "REFLECTION_PATH_DIFFERENCES_M",
    "REFLECTION_PATH_TOLERANCE_M",
    "REFLECTION_RATING_PRECISION_DB",
    "REFLECTION_SOURCE_DISTANCE_M",
    "BarrierReflectionWarning",
    "DirectSoundSubtraction",
    "ReflectionFrequencyLimit",
    "ReflectionGridCheck",
    "ReflectionIndexResult",
    "adrienne_low_frequency_limit_hz",
    "adrienne_reflection_window",
    "check_reflection_grid_position",
    "geometric_divergence_corrections",
    "reflection_grid_paths_m",
    "reflection_index",
    "reflection_index_from_positions",
    "reflection_low_frequency_limit",
    "reflection_sampled_area_radius_m",
    "source_directivity_corrections",
    "subtract_direct_sound",
]

# --------------------------------------------------------------------------- #
# Printed constants
# --------------------------------------------------------------------------- #
#: 3.13: the horizontal distance :math:`d_S` from the loudspeaker front panel
#: to the reference plane of the device, in metres.
REFLECTION_SOURCE_DISTANCE_M = 1.50

#: 3.14: the horizontal distance :math:`d_M` from the central microphone
#: (number 5) to the reference plane, in metres. The loudspeaker is therefore
#: :math:`d_{SM}` = 1,25 m from the grid (3.15).
REFLECTION_MICROPHONE_DISTANCE_M = 0.25

#: 3.10, Note 1: the spacing :math:`s` between two neighbouring microphones of
#: the 3 x 3 grid, vertically and horizontally, in metres.
REFLECTION_GRID_SPACING_M = 0.40

#: Table 2 as printed, per microphone :math:`k` numbered as Figure 3.b (1 to 3
#: on the top row, seen from the loudspeaker): the distance :math:`d_{i,k}`
#: from the loudspeaker front panel to the microphone in metres, the specular
#: path :math:`d_{r,k}` via the reference plane in metres, and the correction
#: :math:`C_{geo,k} = (d_{r,k}/d_{i,k})^2` of Formula (2), all to two decimals.
#: :func:`reflection_grid_paths_m` and :func:`geometric_divergence_corrections`
#: give the unrounded values the table is printed from.
REFLECTION_GRID_DISTANCES: Mapping[int, tuple[float, float, float]] = MappingProxyType(
    {
        1: (1.37, 1.84, 1.80),
        2: (1.31, 1.80, 1.87),
        3: (1.37, 1.84, 1.80),
        4: (1.31, 1.80, 1.87),
        5: (1.25, 1.75, 1.96),
        6: (1.31, 1.80, 1.87),
        7: (1.37, 1.84, 1.80),
        8: (1.31, 1.80, 1.87),
        9: (1.37, 1.84, 1.80),
    }
)

#: Table 3 as printed, per microphone: the path difference
#: :math:`\Delta d_{k5}` between the direct sound at microphone :math:`k` and
#: at microphone 5 (the check of 5.6.2.5), and the path difference
#: :math:`\Delta d_k` between the direct and the reflected sound at microphone
#: :math:`k` (the check of 5.6.2.6), both in metres.
REFLECTION_PATH_DIFFERENCES_M: Mapping[int, tuple[float, float]] = MappingProxyType(
    {
        1: (0.122, 0.467),
        2: (0.062, 0.483),
        3: (0.122, 0.467),
        4: (0.062, 0.483),
        5: (0.000, 0.500),
        6: (0.062, 0.483),
        7: (0.122, 0.467),
        8: (0.062, 0.483),
        9: (0.122, 0.467),
    }
)

#: Table 3: the tolerance :math:`\varepsilon_k` on both path differences, the
#: same for every microphone, in metres (plus or minus).
REFLECTION_PATH_TOLERANCE_M = 0.025

#: 5.5.5: the standard total length :math:`T_{W,ADR}` of the Adrienne window,
#: in seconds: 0,5 ms leading edge, 5,18 ms flat, 2,22 ms trailing edge. It
#: processes microphones 1 to 6 in the bands of 100 Hz to 160 Hz.
ADRIENNE_STANDARD_LENGTH_S = 7.9e-3

#: 5.5.5: the shorter window that processes all nine microphones from the
#: 200 Hz band upward, in seconds: 0,5 ms, 3,85 ms flat, 1,65 ms trailing.
ADRIENNE_SHORT_LENGTH_S = 6.0e-3

#: 5.5.1: the window of the gain check of Formula (4), in seconds: 0,5 ms,
#: 0,56 ms flat, 0,24 ms trailing, short enough to end before the reflection
#: reaches the corner microphones about 1,3 ms after the direct sound.
ADRIENNE_CALIBRATION_LENGTH_S = 1.3e-3

#: 5.5.5: the microphones averaged in the bands of 100 Hz, 125 Hz and 160 Hz,
#: the two upper rows of the grid; from 200 Hz all nine are averaged.
REFLECTION_LOW_BAND_MICROPHONES: tuple[int, ...] = (1, 2, 3, 4, 5, 6)


def _precision_row(
    repeatability: tuple[float, float, float],
    reproducibility: tuple[float, float, float],
) -> Mapping[str, tuple[float, float, float]]:
    """One row of Table A.1, as a read-only mapping of its two column groups."""
    return MappingProxyType(
        {"repeatability": repeatability, "reproducibility": reproducibility}
    )


#: Table A.1 (informative), after the QUIESST inter-laboratory test: the
#: standard deviations of repeatability :math:`s_r` and of reproducibility
#: :math:`s_R` of the sound reflection index, per one-third octave band in
#: hertz, each as ``(median, low, high)``. A.2 takes :math:`s_R` as the
#: combined standard uncertainty; Annex B.5 takes the high column for a
#: conservative estimate.
REFLECTION_INDEX_PRECISION: Mapping[float, Mapping[str, tuple[float, float, float]]] = (
    MappingProxyType(
        {
            100.0: _precision_row((0.25, 0.21, 0.30), (0.27, 0.23, 0.32)),
            125.0: _precision_row((0.12, 0.10, 0.14), (0.14, 0.12, 0.18)),
            160.0: _precision_row((0.06, 0.05, 0.07), (0.09, 0.08, 0.12)),
            200.0: _precision_row((0.08, 0.07, 0.10), (0.11, 0.09, 0.14)),
            250.0: _precision_row((0.08, 0.06, 0.09), (0.10, 0.09, 0.13)),
            315.0: _precision_row((0.08, 0.07, 0.10), (0.10, 0.09, 0.13)),
            400.0: _precision_row((0.07, 0.06, 0.09), (0.10, 0.08, 0.12)),
            500.0: _precision_row((0.07, 0.06, 0.08), (0.09, 0.08, 0.12)),
            630.0: _precision_row((0.09, 0.08, 0.11), (0.11, 0.09, 0.14)),
            800.0: _precision_row((0.10, 0.09, 0.12), (0.12, 0.11, 0.15)),
            1000.0: _precision_row((0.09, 0.08, 0.10), (0.10, 0.09, 0.13)),
            1250.0: _precision_row((0.10, 0.08, 0.12), (0.12, 0.10, 0.15)),
            1600.0: _precision_row((0.12, 0.10, 0.14), (0.14, 0.12, 0.16)),
            2000.0: _precision_row((0.11, 0.09, 0.13), (0.13, 0.11, 0.15)),
            2500.0: _precision_row((0.11, 0.09, 0.13), (0.13, 0.11, 0.15)),
            3150.0: _precision_row((0.12, 0.10, 0.14), (0.14, 0.12, 0.17)),
            4000.0: _precision_row((0.15, 0.13, 0.18), (0.17, 0.15, 0.20)),
            5000.0: _precision_row((0.17, 0.14, 0.20), (0.19, 0.16, 0.23)),
        }
    )
)

#: Table A.1, last row: the same two standard deviations for the single-number
#: rating :math:`DL_{RI}`, in decibels, each as ``(median, low, high)``.
REFLECTION_RATING_PRECISION_DB: Mapping[str, tuple[float, float, float]] = (
    _precision_row((0.53, 0.44, 0.62), (0.68, 0.54, 0.81))
)

# Unexported constants of the processing, each printed in the clause cited.
#: 5.5.5: the fixed leading edge of the Adrienne window, in seconds.
_LEADING_EDGE_S = 0.5e-3
#: 5.5.5: the flat part and the trailing edge share the rest 7 to 3.
_FLAT_SHARE = 0.7
#: 5.5.6: the marker point sits this far before the peak, in seconds.
_MARKER_LEAD_S = 0.2e-3
#: 5.5.4: the moving step is about 1/50 of the sample step.
_STEPS_PER_SAMPLE = 50
#: 5.5.4: the search covers +/- 2 samples, that is +/- 100 moving steps.
_SEARCH_SAMPLES = 2
#: 5.5.4: the least squares run over about 50 samples around the main peak.
_FIT_POINTS = 50
#: 5.5.4, Formula (6): half the interval the reduction factor integrates.
_REDUCTION_HALF_WIDTH_S = 0.5e-3
#: 5.5.4: below this reduction factor the subtraction is not perfect, in dB.
_REDUCTION_WARNING_DB = 10.0
#: 5.5.1: the gain factor may be set to 1 within 5 %; beyond 20 % the
#: measurement settings are suspect.
_GAIN_WARNING = 0.20
#: 5.5.2: the lowest sample rate the method admits, in hertz.
_MINIMUM_SAMPLE_RATE_HZ = 44_000.0
#: 5.5.1: the gain check integrates over the bands of 500 Hz to 2 kHz.
_GAIN_BANDS_HZ = (500.0, 2000.0)
#: The microphone count of the grid.
_MICROPHONES = 9
#: Array ranks of one grid position ``(9, N)`` and of several ``(P, 9, N)``.
_ONE_GRID_RANK = 2
_GRIDS_RANK = 3
#: The shortest record that can hold an impulse response.
_MINIMUM_SAMPLES = 2
#: A phase below which the oscillating integral is taken as its limit.
_NEGLIGIBLE_PHASE = 1e-12
#: Slack on the 25 mm tolerance, so a deviation printed at the limit passes.
_TOLERANCE_SLACK_M = 1e-12
#: Frequency resolution of the band integrals, in hertz. The windowed
#: components last a few milliseconds, so their spectra vary over hundreds of
#: hertz; half a hertz leaves the band energies converged to better than a
#: part in a million.
_FREQUENCY_STEP_HZ = 0.5
#: The four Blackman-Harris coefficients of Formula (7).
_BLACKMAN_HARRIS = (0.35875, 0.48829, 0.14128, 0.01168)

#: Figure 3.b: each microphone's (horizontal, vertical) offset from
#: microphone 5 in units of the spacing, seen from the loudspeaker.
_GRID_OFFSETS: tuple[tuple[int, int], ...] = (
    (-1, 1),
    (0, 1),
    (1, 1),
    (-1, 0),
    (0, 0),
    (1, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
)

#: The eighteen bands of EN 1793-3 as exact base-ten midbands, and their
#: edges, which are what the integrals of Formulas (1), (3) and (4) run over.
_BAND_INDEX = tuple(round(10.0 * math.log10(f / 1000.0)) for f in _BANDS_HZ)
_MIDBANDS_HZ = tuple(1000.0 * 10.0 ** (k / 10.0) for k in _BAND_INDEX)
_BAND_LOWER_HZ = tuple(f * 10.0 ** (-0.05) for f in _MIDBANDS_HZ)
_BAND_UPPER_HZ = tuple(f * 10.0**0.05 for f in _MIDBANDS_HZ)
#: The first band averaged over all nine microphones (5.5.5).
_FIRST_FULL_GRID_BAND = _BANDS_HZ.index(200.0)


class BarrierReflectionWarning(PhonometryWarning):
    """A reflection measurement the standard flags as suspect.

    Raised when the reduction factor of the subtraction falls below 10 dB
    (5.5.4), when the gain factor departs from 1 by more than 20 % (5.5.1),
    and when the sample rate is below the 44 kHz of 5.5.2.
    """


# --------------------------------------------------------------------------- #
# Geometry (Formula (2), Tables 2 and 3, Formula (8))
# --------------------------------------------------------------------------- #
def _grid_geometry(
    source_distance_m: float, microphone_distance_m: float, grid_spacing_m: float
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Lateral and vertical microphone offsets and the source-grid distance."""
    require_positive(source_distance_m, "source_distance_m")
    require_positive(microphone_distance_m, "microphone_distance_m")
    require_positive(grid_spacing_m, "grid_spacing_m")
    if microphone_distance_m >= source_distance_m:
        msg = (
            "'microphone_distance_m' must be smaller than 'source_distance_m': "
            "the grid stands between the loudspeaker and the device."
        )
        raise ValueError(msg)
    offsets = np.asarray(_GRID_OFFSETS, dtype=np.float64) * grid_spacing_m
    return (
        offsets[:, 0],
        offsets[:, 1],
        np.array(source_distance_m - microphone_distance_m),
    )


def reflection_grid_paths_m(
    *,
    source_distance_m: float = REFLECTION_SOURCE_DISTANCE_M,
    microphone_distance_m: float = REFLECTION_MICROPHONE_DISTANCE_M,
    grid_spacing_m: float = REFLECTION_GRID_SPACING_M,
) -> NDArray[np.float64]:
    r"""The direct and the specular path to each microphone (Table 2).

    :math:`d_{i,k}` runs from the centre of the loudspeaker front panel to
    microphone :math:`k`; :math:`d_{r,k}` runs from the same point to the
    reference plane and back to the microphone by specular reflection, which
    is the distance from the image of the loudspeaker in the plane. With the
    geometry of the standard these are the values Table 2 prints to two
    decimals (1,25 m and 1,75 m at microphone 5).

    :param source_distance_m: :math:`d_S`, loudspeaker to reference plane, m.
    :param microphone_distance_m: :math:`d_M`, grid to reference plane, m.
    :param grid_spacing_m: :math:`s`, microphone spacing, m.
    :return: A read-only ``(9, 2)`` array: column 0 is :math:`d_{i,k}` and
        column 1 is :math:`d_{r,k}`, rows in microphone order 1 to 9.
    :raises ValueError: If a distance is not positive or the grid does not
        stand between the loudspeaker and the plane.
    """
    lateral, vertical, source_grid = _grid_geometry(
        source_distance_m, microphone_distance_m, grid_spacing_m
    )
    image_grid = source_distance_m + microphone_distance_m
    direct = np.sqrt(source_grid**2 + lateral**2 + vertical**2)
    reflected = np.sqrt(image_grid**2 + lateral**2 + vertical**2)
    return read_only(np.column_stack([direct, reflected]))


def geometric_divergence_corrections(
    *,
    source_distance_m: float = REFLECTION_SOURCE_DISTANCE_M,
    microphone_distance_m: float = REFLECTION_MICROPHONE_DISTANCE_M,
    grid_spacing_m: float = REFLECTION_GRID_SPACING_M,
) -> NDArray[np.float64]:
    r""":math:`C_{geo,k} = (d_{r,k}/d_{i,k})^2`, Formula (2).

    The reflection travels further than the direct sound and spreads over a
    larger sphere; this puts that energy back. At microphone 5 it is
    :math:`(1{,}75/1{,}25)^2 = 1{,}96`; Table 2 prints all nine to two
    decimals (:data:`REFLECTION_GRID_DISTANCES`).

    :param source_distance_m: :math:`d_S`, loudspeaker to reference plane, m.
    :param microphone_distance_m: :math:`d_M`, grid to reference plane, m.
    :param grid_spacing_m: :math:`s`, microphone spacing, m.
    :return: A read-only array of the nine corrections, microphone 1 first.
    :raises ValueError: As :func:`reflection_grid_paths_m`.
    """
    paths = reflection_grid_paths_m(
        source_distance_m=source_distance_m,
        microphone_distance_m=microphone_distance_m,
        grid_spacing_m=grid_spacing_m,
    )
    return read_only((paths[:, 1] / paths[:, 0]) ** 2)


def reflection_sampled_area_radius_m(
    window_length_s: float = ADRIENNE_STANDARD_LENGTH_S,
    *,
    speed_of_sound: float,
) -> float:
    r"""The radius :math:`r` of the maximum sampled area, Formula (8).

    The circle on the reference plane, centred at the point of incidence,
    within which a reflecting object would still fall inside the reflected
    window. It is the ISO 13472-1 construction with the loudspeaker 1,50 m and
    the microphone 0,25 m from the plane, and it reuses
    :func:`~phonometry.materials.surfaces.road_absorption.max_sampled_area_radius`.
    NOTE 1 of 5.6.1 gives 1,96 m for the 7,9 ms window at 340 m/s.

    :param window_length_s: :math:`T_{W,ADR}` of the reflected component, s.
    :param speed_of_sound: Speed of sound at the air temperature of the
        test (5.7.3), in metres per second.
    :return: The radius, in metres.
    :raises ValueError: If the window length or the speed is not positive.
    """
    return max_sampled_area_radius(
        require_positive(window_length_s, "window_length_s"),
        source_height=REFLECTION_SOURCE_DISTANCE_M,
        mic_height=REFLECTION_MICROPHONE_DISTANCE_M,
        speed_of_sound=require_positive(speed_of_sound, "speed_of_sound"),
    )


# --------------------------------------------------------------------------- #
# The Adrienne temporal window (5.5.5, Formula (7))
# --------------------------------------------------------------------------- #
def _window_parts(window_length_s: float) -> tuple[float, float, float]:
    """Leading edge, flat part and trailing edge of a window, in seconds."""
    length = require_positive(window_length_s, "window_length_s")
    if length <= _LEADING_EDGE_S:
        msg = (
            f"'window_length_s' must exceed the fixed 0.5 ms leading edge of "
            f"5.5.5; got {length!r} s."
        )
        raise ValueError(msg)
    rest = length - _LEADING_EDGE_S
    return _LEADING_EDGE_S, _FLAT_SHARE * rest, (1.0 - _FLAT_SHARE) * rest


def _blackman_harris(t_s: NDArray[np.float64], length_s: float) -> NDArray[np.float64]:
    """Formula (7): the full four-term Blackman-Harris window of length ``length_s``."""
    a0, a1, a2, a3 = _BLACKMAN_HARRIS
    x = 2.0 * np.pi * t_s / length_s
    return np.asarray(
        a0 - a1 * np.cos(x) + a2 * np.cos(2.0 * x) - a3 * np.cos(3.0 * x),
        dtype=np.float64,
    )


def adrienne_reflection_window(
    fs: float, window_length_s: float = ADRIENNE_STANDARD_LENGTH_S
) -> NDArray[np.float64]:
    r"""The Adrienne temporal window of EN 1793-5, 5.5.5.

    A left half of a four-term Blackman-Harris window 0,5 ms long, a flat part,
    and a right half of a Blackman-Harris window; the flat part and the
    trailing edge share the rest of the length 7 to 3. The 7,9 ms standard
    window has a 5,18 ms flat part and a 2,22 ms trailing edge; the 6,0 ms one
    3,85 ms and 1,65 ms.

    The edges are Formula (7) sampled as printed: the leading edge is the
    first half of a Blackman-Harris window twice its length, taken at
    ``0, 1/fs, ...`` up to the sample before it reaches 1, which is the marker
    point; the trailing edge is the second half of one twice its length, from
    the sample after the flat part down to its last sample. The ISO 13472-1
    window of
    :func:`~phonometry.materials.surfaces.road_absorption.adrienne_window`
    is left free by its standard and rescales its halves instead; this one is
    the formula EN 1793-5 prints.

    :param fs: Sample rate, in hertz.
    :param window_length_s: Total length :math:`T_{W,ADR}`, in seconds.
    :return: The window, one sample per ``1 / fs``; its marker point, where
        the flat part begins, is sample ``round(0.5e-3 * fs)``.
    :raises ValueError: If ``fs`` is not positive, the length does not exceed
        the 0,5 ms leading edge, or the flat part is shorter than a sample.
    """
    rate = require_positive(fs, "fs")
    leading, flat, trailing = _window_parts(window_length_s)
    n_lead = round(leading * rate)
    n_flat = round(flat * rate)
    n_trail = round(trailing * rate)
    if n_flat < 1:
        msg = f"the flat part of a {window_length_s!r} s window is shorter than a sample at {rate:g} Hz."
        raise ValueError(msg)
    rising = _blackman_harris(np.arange(n_lead) / rate, 2.0 * n_lead / rate)
    falling = _blackman_harris(
        (n_trail + np.arange(1, n_trail + 1)) / rate, 2.0 * n_trail / rate
    )
    return np.concatenate([rising, np.ones(n_flat), falling])


def _window_spectrum(frequency_hz: float, window_length_s: float) -> float:
    r"""Magnitude of the Fourier transform of the continuous window, in seconds.

    Each of the three pieces is a sum of cosines over a finite interval, so
    the transform is a sum of closed forms and needs no sampling.
    """
    leading, flat, trailing = _window_parts(window_length_s)
    omega = 2.0 * math.pi * frequency_hz

    def piece(start: float, length: float, coefficients: tuple[float, ...]) -> complex:
        total = 0j
        for m, coefficient in enumerate(coefficients):
            omega_m = m * math.pi / length
            # integral over [0, length] of cos(omega_m u) exp(-j omega u) du
            term = 0j
            for sign in (1.0, -1.0):
                beta = sign * omega_m - omega
                if abs(beta) * length < _NEGLIGIBLE_PHASE:
                    term += 0.5 * length
                else:
                    term += 0.5 * (np.exp(1j * beta * length) - 1.0) / (1j * beta)
            total += coefficient * term
        return complex(total * np.exp(-1j * omega * start))

    a0, a1, a2, a3 = _BLACKMAN_HARRIS
    rising = piece(0.0, leading, (a0, -a1, a2, -a3))
    body = piece(leading, flat, (1.0,))
    falling = piece(leading + flat, trailing, (a0, a1, a2, a3))
    return abs(rising + body + falling)


def adrienne_low_frequency_limit_hz(window_length_s: float) -> float:
    r"""The first notch in the spectrum of an Adrienne window, in hertz.

    Garai and Guidorzi (J. Acoust. Soc. Am. 108 (2000) 1054, section III.D.4)
    take the first notch of the window's magnitude spectrum, the end of its
    main lobe, as the low frequency limit of a measurement made through it,
    and give about 160 Hz for the 7,9 ms window. EN 1793-5 states the limit
    only as the curves of Figure 14, without saying how they were drawn; this
    is the indicator of the method's authors. The transform of the continuous
    window is evaluated in closed form and the notch is located to a
    millihertz.

    :param window_length_s: Total length :math:`T_{W,ADR}`, in seconds.
    :return: The frequency of the first minimum of the magnitude spectrum, in
        hertz: 162,5 Hz for 7,9 ms and 216,5 Hz for 6,0 ms.
    :raises ValueError: If the length does not exceed the 0,5 ms leading edge.
    """
    _window_parts(window_length_s)
    step = 0.02 / window_length_s
    previous = _window_spectrum(0.0, window_length_s)
    frequency = step
    current = _window_spectrum(frequency, window_length_s)
    while current < previous:
        previous = current
        frequency += step
        current = _window_spectrum(frequency, window_length_s)
    found = minimize_scalar(
        lambda f: _window_spectrum(f, window_length_s),
        bounds=(frequency - 2.0 * step, frequency),
        method="bounded",
        options={"xatol": 1e-3},
    )
    return float(found.x)


# --------------------------------------------------------------------------- #
# Signal subtraction (5.5.4, Formula (6))
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DirectSoundSubtraction(OwnsArrays):
    r"""The direct sound taken out of an impulse response, 5.5.4.

    :ivar in_front: The impulse response measured in front of the device.
    :ivar aligned_free_field: The free-field impulse response after the shift
        and the amplitude adjustment of steps 2 to 5, the one that was
        subtracted. NOTE 1: it serves the subtraction only; the index is
        computed from the original free-field record.
    :ivar residual: What is left, the reflected component (step 6).

    The three records come back in the type they arrived as: a
    :class:`~phonometry.io.Signal` when the record was one (in pascals and
    carrying ``calibration_factor=1.0`` when it was calibrated), a bare array
    otherwise.

    :ivar fs: Sample rate, in hertz.
    :ivar peak_index: The sample of the first and main peak of the in-front
        record, the direct sound.
    :ivar shift_samples: The shift applied to the free-field record, in
        samples, positive for a delay: a whole number of the 1/50 sample
        moving steps, within the +/- 2 samples 5.5.4 allows.
    :ivar amplitude_factor: The factor that made the two main peaks equal.
    :ivar reduction_db: :math:`R_{sub}`, Formula (6): the energy of the
        free-field record within 0,5 ms of the peak over that of the residual
        in the same interval, in decibels. Below 10 dB the subtraction is not
        perfect; ``inf`` when nothing is left at all.
    """

    in_front: Signal | NDArray[np.float64]
    aligned_free_field: Signal | NDArray[np.float64]
    residual: Signal | NDArray[np.float64]
    fs: float
    peak_index: int
    shift_samples: float
    amplitude_factor: float
    reduction_db: float

    def __post_init__(self) -> None:
        """Refuse three records that cannot be read sample against sample.

        :raises ValueError: If a record is not one-dimensional, the three differ
            in length, or one is a Signal at a rate other than :attr:`fs`.
        """
        require_ranks(self, in_front=1, aligned_free_field=1, residual=1)
        require_same_length(self, "in_front", "aligned_free_field", axis="sample")
        require_same_length(self, "in_front", "residual", axis="sample")
        for field in ("in_front", "aligned_free_field", "residual"):
            require_signal_rate(self, field, self.fs)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the record, the aligned direct sound and what is left.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the residual ``Axes.plot`` call.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_direct_sound_subtraction

        return plot_direct_sound_subtraction(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _require_fs(fs: float) -> float:
    """A positive sample rate, with the 44 kHz floor of 5.5.2 as a warning."""
    rate = require_positive(fs, "fs")
    if rate < _MINIMUM_SAMPLE_RATE_HZ:
        msg = (
            f"EN 1793-5 5.5.2 asks for a sample rate of at least 44 kHz, so that "
            f"the subtraction can align the records to a fraction of a sample; "
            f"got {rate:g} Hz."
        )
        warnings.warn(msg, BarrierReflectionWarning, stacklevel=3)
    return rate


def _record(values: ArrayLike, name: str) -> NDArray[np.float64]:
    """A finite one-dimensional impulse response."""
    record = np.asarray(values, dtype=np.float64)
    if record.ndim != 1 or record.size < _MINIMUM_SAMPLES:
        msg = f"'{name}' must be a one-dimensional impulse response."
        raise ValueError(msg)
    if not np.all(np.isfinite(record)):
        msg = f"'{name}' must contain only finite samples."
        raise ValueError(msg)
    return record


def _subtract(
    in_front: NDArray[np.float64], free_field: NDArray[np.float64], fs: float
) -> DirectSoundSubtraction:
    """Steps 1 to 6 of 5.5.4 and Formula (6) on two checked records."""
    n = in_front.size
    peak = int(np.argmax(np.abs(in_front)))
    fit = slice(max(peak - _FIT_POINTS // 2, 0), min(peak + _FIT_POINTS // 2, n))
    spectrum = np.fft.rfft(free_field)
    bins = np.arange(spectrum.size, dtype=np.float64)
    steps = np.arange(
        -_SEARCH_SAMPLES * _STEPS_PER_SAMPLE, _SEARCH_SAMPLES * _STEPS_PER_SAMPLE + 1
    )
    target = in_front[fit]
    best_cost = math.inf
    best_shift = 0.0
    best_record = free_field
    # The shift is a phase ramp over the record itself, so no sample is added
    # (NOTE 2); the candidates are evaluated a few at a time to bound memory.
    for chunk in np.array_split(steps, max(1, steps.size // 16)):
        shifts = chunk / _STEPS_PER_SAMPLE
        ramps = np.exp(-2j * np.pi * np.outer(shifts, bins) / n)
        shifted = np.fft.irfft(spectrum * ramps, n=n, axis=-1)
        costs = np.sum((shifted[:, fit] - target) ** 2, axis=1)
        index = int(np.argmin(costs))
        if costs[index] < best_cost:
            best_cost = float(costs[index])
            best_shift = float(shifts[index])
            best_record = shifted[index]
    shifted_peak = int(np.argmax(np.abs(best_record)))
    factor = float(in_front[peak] / best_record[shifted_peak])
    aligned = factor * best_record
    residual = in_front - aligned
    half = round(_REDUCTION_HALF_WIDTH_S * fs)
    zone = slice(max(peak - half, 0), min(peak + half + 1, n))
    direct_energy = float(np.sum(free_field[zone] ** 2))
    left_energy = float(np.sum(residual[zone] ** 2))
    reduction = (
        10.0 * math.log10(direct_energy / left_energy)
        if left_energy > 0.0
        else math.inf
    )
    return DirectSoundSubtraction(
        in_front=in_front,
        aligned_free_field=read_only(np.asarray(aligned, dtype=np.float64)),
        residual=read_only(np.asarray(residual, dtype=np.float64)),
        fs=fs,
        peak_index=peak,
        shift_samples=best_shift,
        amplitude_factor=factor,
        reduction_db=reduction,
    )


def _warn_reduction(reduction_db: float, where: str) -> None:
    """The 10 dB warning of 5.5.4."""
    if reduction_db < _REDUCTION_WARNING_DB:
        msg = (
            f"the reduction factor R_sub of the subtraction is "
            f"{reduction_db:.1f} dB{where}, below the 10 dB under which EN 1793-5 "
            f"5.5.4 warns that the direct sound was not fully removed."
        )
        warnings.warn(msg, BarrierReflectionWarning, stacklevel=3)


def subtract_direct_sound(
    in_front_ir: SignalInput, free_field_ir: SignalInput, fs: float | None = None
) -> DirectSoundSubtraction:
    r"""Remove the direct sound from an impulse response, 5.5.4.

    The free-field record is the direct sound alone, measured with the same
    geometry. It is shifted in steps of a fiftieth of a sample, within two
    samples either way, by a phase ramp over its own transform (steps a and
    b); the shift that minimises the squared difference over 50 samples
    around the main peak of the in-front record is kept; the shifted record
    is scaled so the two main peaks are equal; and it is subtracted. The
    reduction factor :math:`R_{sub}` of Formula (6) measures what is left of
    the direct sound.

    :param in_front_ir: The impulse response in front of the device. Accepts
        a :class:`phonometry.io.Signal`, whose calibration is applied to the
        samples, so the records come back in pascals, and as Signals.
    :param free_field_ir: The free-field impulse response of the same
        microphone, same length and sample rate; same treatment.
    :param fs: Sample rate, in hertz. Required when both records are bare
        arrays; either may be a Signal and supply it, and two Signals recorded
        at different rates are refused rather than arbitrated.
    :return: The :class:`DirectSoundSubtraction`, with ``.plot()``.
    :raises ValueError: If the records are not one-dimensional, finite and of
        equal length, or the rate is missing or not positive.
    :warns BarrierReflectionWarning: If :math:`R_{sub}` is below 10 dB or the
        sample rate below 44 kHz.
    """
    rate = _require_fs(
        float(
            resolve_pair_fs(
                in_front_ir, free_field_ir, fs, names=("in_front_ir", "free_field_ir")
            )
        )
    )
    in_front = apply_calibration(
        in_front_ir, _record(in_front_ir, "in_front_ir"), name="in_front_ir"
    )
    free_field = apply_calibration(
        free_field_ir, _record(free_field_ir, "free_field_ir"), name="free_field_ir"
    )
    if in_front.size != free_field.size:
        msg = (
            f"'in_front_ir' and 'free_field_ir' must have the same length; got "
            f"{in_front.size} and {free_field.size} samples."
        )
        raise ValueError(msg)
    result = _subtract(in_front, free_field, rate)
    _warn_reduction(result.reduction_db, "")
    return DirectSoundSubtraction(
        in_front=like_input(in_front_ir, np.asarray(result.in_front)),
        aligned_free_field=like_input(
            free_field_ir, np.asarray(result.aligned_free_field)
        ),
        residual=like_input(in_front_ir, np.asarray(result.residual)),
        fs=result.fs,
        peak_index=result.peak_index,
        shift_samples=result.shift_samples,
        amplitude_factor=result.amplitude_factor,
        reduction_db=result.reduction_db,
    )


# --------------------------------------------------------------------------- #
# Band energies of windowed components (Formulas (1), (3) and (4))
# --------------------------------------------------------------------------- #
def _band_energies(
    segment: NDArray[np.float64],
    fs: float,
    lower_hz: Sequence[float],
    upper_hz: Sequence[float],
) -> NDArray[np.float64]:
    r"""The integrals :math:`\int |F[h\,w]|^2 df` of a windowed segment per band.

    The segment is zero-padded to a half-hertz resolution; each bin stands for
    the interval it is the centre of, so the running integral is exact at the
    bin boundaries and linear between them, and a band edge falling inside a
    bin takes its share of it.
    """
    size = int(next_fast_len(max(segment.size, math.ceil(fs / _FREQUENCY_STEP_HZ))))
    power = np.abs(np.fft.rfft(segment, n=size)) ** 2
    step = fs / size
    boundaries = np.concatenate(([-0.5 * step], (np.arange(power.size) + 0.5) * step))
    running = np.concatenate(([0.0], np.cumsum(power) * step))
    upper = np.interp(np.asarray(upper_hz, dtype=np.float64), boundaries, running)
    lower = np.interp(np.asarray(lower_hz, dtype=np.float64), boundaries, running)
    return np.asarray(upper - lower, dtype=np.float64)


def _windowed(
    record: NDArray[np.float64],
    peak: float,
    window: NDArray[np.float64],
    fs: float,
    what: str,
) -> NDArray[np.float64]:
    """The segment under a window whose marker is 0,2 ms before ``peak``."""
    leading = round(_LEADING_EDGE_S * fs)
    start = round(peak - _MARKER_LEAD_S * fs) - leading
    stop = start + window.size
    if start < 0 or stop > record.size:
        msg = (
            f"the Adrienne window of the {what} runs from sample {start} to "
            f"{stop}, outside the record of {record.size} samples; record more "
            f"before the direct sound and after the reflection."
        )
        raise ValueError(msg)
    return np.asarray(record[start:stop] * window, dtype=np.float64)


def _per_microphone(value: float | ArrayLike, name: str) -> NDArray[np.float64]:
    """One window length for all nine microphones, or one per microphone."""
    lengths = np.atleast_1d(np.asarray(value, dtype=np.float64))
    if lengths.size == 1:
        lengths = np.full(_MICROPHONES, float(lengths[0]))
    if lengths.shape != (_MICROPHONES,):
        msg = f"'{name}' must be one length or nine, one per microphone."
        raise ValueError(msg)
    for length in lengths:
        _window_parts(float(length))
    return lengths


def _directivity(values: ArrayLike | None) -> NDArray[np.float64]:
    """The (9, 18) directivity corrections, ones when there are none."""
    bands = len(_BANDS_HZ)
    if values is None:
        return np.ones((_MICROPHONES, bands))
    corrections = np.asarray(values, dtype=np.float64)
    if corrections.shape != (_MICROPHONES, bands):
        msg = (
            f"'directivity_corrections' must be a ({_MICROPHONES}, {bands}) array, "
            f"one row per microphone and one column per band; got "
            f"{corrections.shape}."
        )
        raise ValueError(msg)
    if not np.all(np.isfinite(corrections)) or np.any(corrections <= 0.0):
        msg = "'directivity_corrections' must be finite and positive."
        raise ValueError(msg)
    return corrections


def source_directivity_corrections(
    microphone_irs: SignalInput,
    specular_irs: SignalInput,
    fs: float | None = None,
    *,
    window_length_s: float | ArrayLike = ADRIENNE_SHORT_LENGTH_S,
    low_band_window_length_s: float | ArrayLike = ADRIENNE_STANDARD_LENGTH_S,
) -> NDArray[np.float64]:
    r""":math:`C_{dir,k}(\Delta f_j)`, Formula (3).

    The direct sound reaches microphone :math:`k` at the angle
    :math:`\alpha_k` from the loudspeaker axis, and the reflection leaves the
    loudspeaker at another angle :math:`\beta_k`, towards its specular point.
    Both are measured once per loudspeaker in free field, at the same distance
    :math:`d_{i,k}`: one at the microphone position, one on the specular path.
    The correction is the ratio of their windowed band energies, each window
    placed on its own record's peak (5.5.6).

    :param microphone_irs: ``(9, N)`` free-field impulse responses at the nine
        microphone positions (angle :math:`\alpha_k`). Accepts a nine-channel
        :class:`phonometry.io.Signal`, whose calibration is applied.
    :param specular_irs: ``(9, N)`` free-field impulse responses at the nine
        points on the specular paths (angle :math:`\beta_k`); same treatment.
    :param fs: Sample rate, in hertz. Required when both sets are bare
        arrays; either may be a Signal and supply it, and two Signals recorded
        at different rates are refused rather than arbitrated.
    :param window_length_s: Window from the 200 Hz band upward, one length
        or nine, in seconds.
    :param low_band_window_length_s: Window of the 100 Hz to 160 Hz bands,
        one length or nine, in seconds.
    :return: A read-only ``(9, 18)`` array, microphones by the bands of
        :data:`~phonometry.environment.propagation.noise_reducing_devices.TRAFFIC_NOISE_BANDS_HZ`,
        to pass as ``directivity_corrections`` to :func:`reflection_index`.
    :raises ValueError: If the records are not ``(9, N)``, finite and equal
        in shape, the rate is missing, disagrees or is not positive, or a
        window does not fit its record.
    """
    rate = _require_fs(
        float(
            resolve_pair_fs(
                microphone_irs,
                specular_irs,
                fs,
                names=("microphone_irs", "specular_irs"),
            )
        )
    )
    on_axis = _grid_record(microphone_irs, "microphone_irs")
    specular = _grid_record(specular_irs, "specular_irs")
    if on_axis.shape != specular.shape:
        msg = (
            f"'microphone_irs' and 'specular_irs' must have the same shape; got "
            f"{on_axis.shape} and {specular.shape}."
        )
        raise ValueError(msg)
    high = _per_microphone(window_length_s, "window_length_s")
    low = _per_microphone(low_band_window_length_s, "low_band_window_length_s")
    out = np.empty((_MICROPHONES, len(_BANDS_HZ)))
    for k in range(_MICROPHONES):
        for lengths, bands in (
            (low, slice(0, _FIRST_FULL_GRID_BAND)),
            (high, slice(_FIRST_FULL_GRID_BAND, None)),
        ):
            window = adrienne_reflection_window(rate, float(lengths[k]))
            energies = []
            for record in (on_axis[k], specular[k]):
                peak = float(np.argmax(np.abs(record)))
                segment = _windowed(record, peak, window, rate, "directivity record")
                energies.append(
                    _band_energies(
                        segment, rate, _BAND_LOWER_HZ[bands], _BAND_UPPER_HZ[bands]
                    )
                )
            out[k, bands] = energies[0] / energies[1]
    return read_only(out)


def _grid_record(entry: SignalInput, name: str) -> NDArray[np.float64]:
    """The ``(9, N)`` records of one grid position, in pascals when calibrated."""
    records = np.asarray(entry, dtype=np.float64)
    if records.ndim != _ONE_GRID_RANK or records.shape[0] != _MICROPHONES:
        msg = (
            f"'{name}' must be shaped (9, N) for one grid position, a nine-channel "
            f"Signal, or (positions, 9, N) for several; got {records.shape}."
        )
        raise ValueError(msg)
    if records.shape[-1] < _MINIMUM_SAMPLES or not np.all(np.isfinite(records)):
        msg = f"'{name}' must hold finite impulse responses."
        raise ValueError(msg)
    return apply_calibration(entry, records, name=name)


def _grid_positions(
    values: SignalInput | Sequence[SignalInput], name: str
) -> list[SignalInput]:
    """One entry per grid position: a ``(9, N)`` array or a nine-channel Signal.

    A Signal is one grid position, its nine channels the microphones; a
    sequence that holds a Signal is one entry per position; anything else is
    read as an array, ``(9, N)`` for one position or ``(positions, 9, N)``.
    """
    if isinstance(values, Signal):
        return [values]
    if isinstance(values, Sequence) and any(isinstance(v, Signal) for v in values):
        entries: list[SignalInput] = []
        for entry in values:
            if isinstance(entry, (int, float)):
                msg = (
                    f"'{name}' mixes Signals with bare numbers; give one (9, N) "
                    f"record or nine-channel Signal per grid position."
                )
                raise ValueError(msg)
            entries.append(entry)
        return entries
    records = np.asarray(values, dtype=np.float64)
    if records.ndim == _GRIDS_RANK:
        if records.shape[1] != _MICROPHONES:
            msg = (
                f"'{name}' must be shaped (9, N) for one grid position, a "
                f"nine-channel Signal, or (positions, 9, N) for several; got "
                f"{records.shape}."
            )
            raise ValueError(msg)
        return list(records)
    return [records]


def _grid_rate(
    fronts: Sequence[SignalInput], frees: Sequence[SignalInput], fs: float | None
) -> float:
    """The one sample rate of every record, from ``fs`` or from the Signals.

    Two records at different rates cannot be subtracted sample against sample,
    so every Signal among them has to agree with ``fs`` and with each other.
    """
    rate = None if fs is None else float(fs)
    source = ""
    for name, entries in (("in_front_irs", fronts), ("free_field_irs", frees)):
        for p, entry in enumerate(entries):
            if isinstance(entry, Signal):
                where = f"'{name}' of grid position {p + 1}"
                rate, source = _agree_rate(entry, where, rate, source, fs)
    if rate is None:
        msg = "fs is required when 'in_front_irs' and 'free_field_irs' are bare arrays"
        raise ValueError(msg)
    return rate


def _agree_rate(
    entry: Signal, where: str, rate: float | None, source: str, fs: float | None
) -> tuple[float, str]:
    """The rate so far and where it came from, held against one more Signal.

    The first Signal sets the rate when ``fs`` did not; every later one has
    to agree with it.

    :raises ValueError: for a Signal whose rate disagrees with ``fs`` or with
        an earlier Signal.
    """
    if rate is None:
        return float(entry.fs), where
    if not math.isclose(float(entry.fs), rate, rel_tol=1e-12, abs_tol=0.0):
        msg = (
            f"fs={fs} conflicts with the Signal's own fs={entry.fs} in "
            f"{where}; pass one or the other, not a disagreement"
            if not source
            else f"{source} and {where} are Signals recorded at different "
            f"rates ({rate:g} Hz and {entry.fs} Hz); resample one of them "
            f"before comparing them"
        )
        raise ValueError(msg)
    return rate, source


# --------------------------------------------------------------------------- #
# The sound reflection index (Formula (1))
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ReflectionIndexResult(OwnsArrays):
    r"""The sound reflection index of a device, per one-third octave band.

    :ivar bands_hz: The eighteen band centres, 100 Hz to 5 kHz.
    :ivar reflection_index: :math:`RI_j`, the average over every microphone of
        every grid position (5.6.2.3); ``nan`` in a band nothing measured.
    :ivar position_values: ``(positions, 18)``: the average of each grid
        position, the "particular values" of Table B.1.
    :ivar lowest_band_hz: The lowest reliable band, where the single number
        starts (the :math:`m` of Formula (12)).
    :ivar rating: :math:`DL_{RI}` over the bands from ``lowest_band_hz``, a
        :class:`~phonometry.environment.propagation.noise_reducing_devices.RoadDeviceRating`.
    :ivar microphone_values: ``(positions, 9, 18)``: the index of each
        microphone, ``nan`` where 5.5.5 leaves it out (microphones 7 to 9 below
        200 Hz by default); ``None`` for a result built from position values.
    :ivar gain_corrections: ``(positions, 9)``: :math:`C_{gain,k}` of
        Formula (4), or ``None``.
    :ivar subtraction_reductions_db: ``(positions, 9)``: :math:`R_{sub}` of
        each subtraction, in decibels, or ``None``.
    """

    bands_hz: NDArray[np.float64]
    reflection_index: NDArray[np.float64]
    position_values: NDArray[np.float64]
    lowest_band_hz: float
    rating: RoadDeviceRating
    microphone_values: NDArray[np.float64] | None = None
    gain_corrections: NDArray[np.float64] | None = None
    subtraction_reductions_db: NDArray[np.float64] | None = None

    def expanded_uncertainty(
        self,
        *,
        estimate: Literal["median", "low", "high"] = "high",
        coverage_factor: float = 1.96,
    ) -> tuple[NDArray[np.float64], float]:
        r"""Expanded uncertainty from the reproducibility of Table A.1 (A.2).

        :math:`U_j = k_p\, s_{R,j}`, with :math:`s_R` taken as the combined
        standard uncertainty. Annex B.5 takes the high column and
        :math:`k_p` = 1,96 for 95 % coverage, which is the default.

        :param estimate: The column of Table A.1, ``"median"``, ``"low"`` or
            ``"high"``.
        :param coverage_factor: :math:`k_p`.
        :return: The eighteen :math:`U_j` and the :math:`U` of
            :math:`DL_{RI}` in decibels.
        :raises ValueError: On an unknown column or a non-positive factor.
        """
        column = ("median", "low", "high").index(
            require_choice(estimate, "estimate", ("median", "low", "high"))
        )
        factor = require_positive(coverage_factor, "coverage_factor")
        per_band = np.array(
            [
                REFLECTION_INDEX_PRECISION[band]["reproducibility"][column]
                for band in _BANDS_HZ
            ]
        )
        rating = REFLECTION_RATING_PRECISION_DB["reproducibility"][column]
        return read_only(factor * per_band), factor * rating

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the index per band, each grid position and the rating.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the average ``Axes.plot`` call.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_reflection_index

        return plot_reflection_index(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _result(
    position_values: NDArray[np.float64],
    all_values: NDArray[np.float64],
    lowest_band_hz: float,
    *,
    microphone_values: NDArray[np.float64] | None = None,
    gain_corrections: NDArray[np.float64] | None = None,
    reductions_db: NDArray[np.float64] | None = None,
) -> ReflectionIndexResult:
    """Assemble a result; ``all_values`` is ``(partial results, 18)``."""
    counts = np.sum(np.isfinite(all_values), axis=0)
    sums = np.nansum(all_values, axis=0)
    average = np.full(counts.shape, np.nan)
    np.divide(sums, counts, out=average, where=counts > 0)
    rating = sound_reflection_rating(average, lowest_band_hz=lowest_band_hz)
    return ReflectionIndexResult(
        bands_hz=read_only(np.asarray(_BANDS_HZ, dtype=np.float64)),
        reflection_index=read_only(average),
        position_values=position_values,
        lowest_band_hz=rating.lowest_band_hz,
        rating=rating,
        microphone_values=None if microphone_values is None else microphone_values,
        gain_corrections=None if gain_corrections is None else gain_corrections,
        subtraction_reductions_db=None if reductions_db is None else reductions_db,
    )


def reflection_index_from_positions(
    position_values: ArrayLike, *, lowest_band_hz: float = 200.0
) -> ReflectionIndexResult:
    r"""Combine the index of several grid positions into the declared one.

    Each row is one grid position's :math:`RI` in the eighteen bands, the
    "particular values" of Table B.1; the declared index is their mean, band
    by band, which is the overall average 5.6.2.3 asks for when every position
    contributes the same microphones. A band a position did not measure may
    be ``nan``; it is left out of that band's mean.

    :param position_values: ``(positions, 18)`` or ``(18,)`` indices.
    :param lowest_band_hz: The lowest reliable band for :math:`DL_{RI}`, one
        of the eighteen centres; 200 Hz is the qualification sample of 5.3.
    :return: The :class:`ReflectionIndexResult` (without microphone detail).
    :raises ValueError: If a row does not have eighteen values, a value is
        negative or infinite, or a band from ``lowest_band_hz`` has no value.
    """
    values = np.atleast_2d(np.asarray(position_values, dtype=np.float64))
    bands = len(_BANDS_HZ)
    if values.ndim != _ONE_GRID_RANK or values.shape[1] != bands:
        msg = f"'position_values' must have {bands} values per position; got {values.shape}."
        raise ValueError(msg)
    if np.any(np.isinf(values)) or np.any(values[np.isfinite(values)] < 0.0):
        msg = "'position_values' must be non-negative, or nan where not measured."
        raise ValueError(msg)
    return _result(values, values, lowest_band_hz)


def reflection_index(
    in_front_irs: SignalInput | Sequence[SignalInput],
    free_field_irs: SignalInput | Sequence[SignalInput],
    fs: float | None = None,
    *,
    speed_of_sound: float,
    window_length_s: float | ArrayLike = ADRIENNE_SHORT_LENGTH_S,
    low_band_window_length_s: float | ArrayLike = ADRIENNE_STANDARD_LENGTH_S,
    low_band_microphones: Sequence[int] = REFLECTION_LOW_BAND_MICROPHONES,
    directivity_corrections: ArrayLike | None = None,
    lowest_band_hz: float = 200.0,
) -> ReflectionIndexResult:
    r"""The sound reflection index :math:`RI_j`, Formula (1).

    For every microphone of every grid position: the direct sound is
    subtracted (:func:`subtract_direct_sound`); the free-field record is
    windowed on its own peak and the residual on the specular arrival of the
    reflection, both with the marker point 0,2 ms before the peak (5.5.6);
    the band energies of the two are divided and corrected by
    :math:`C_{geo,k}`, :math:`C_{dir,k}` and :math:`C_{gain,k}`. The
    reflection's peak is placed by geometry, the direct peak plus
    :math:`(d_{r,k} - d_{i,k})/c`, which is what 5.5.6 prefers and what makes
    the reference plane the conventional reflection plane of a non-flat
    device.

    The gain factor is Formula (4), with the 1,3 ms window over the bands of
    500 Hz to 2 kHz, and it **divides**: Formula (1) prints it as a
    multiplier, which with Formula (4) would square a gain change instead of
    removing it (docs/ERRATA.md). 5.5.1 allows setting it to 1 when it is
    within 5 % of 1; the value computed is always used here.

    :param in_front_irs: Impulse responses in front of the device, ``(9, N)``
        for one grid position or ``(positions, 9, N)``, microphones in the
        order of Figure 3.b. A nine-channel :class:`phonometry.io.Signal` is
        one grid position, and a sequence of them (or of ``(9, N)`` arrays)
        one per position; a Signal's calibration is applied.
    :param free_field_irs: The free-field impulse responses of the same
        microphones, in the same form and shape.
    :param fs: Sample rate, in hertz. Required when every record is a bare
        array; a Signal supplies it, and a Signal that disagrees with it or
        with another Signal is refused rather than arbitrated.
    :param speed_of_sound: Speed of sound at the air temperature of the test
        (5.5.6, 5.7.3), in metres per second; it places the reflected window,
        and the standard asks for its temperature-dependent value.
    :param window_length_s: :math:`T_{W,ADR}` from the 200 Hz band upward,
        one length or nine (one per microphone); 6,0 ms by 5.5.5.
    :param low_band_window_length_s: :math:`T_{W,ADR}` of the 100 Hz to
        160 Hz bands; 7,9 ms by 5.5.5.
    :param low_band_microphones: The microphones averaged below 200 Hz;
        1 to 6 by 5.5.5.
    :param directivity_corrections: :math:`C_{dir,k}(\Delta f_j)` as a
        ``(9, 18)`` array (:func:`source_directivity_corrections`), or ``None``
        for none, which is what a report states as "none".
    :param lowest_band_hz: The lowest reliable band, where :math:`DL_{RI}`
        starts; 200 Hz for the qualification sample of 5.3.
    :return: The :class:`ReflectionIndexResult`, with ``.plot()``.
    :raises ValueError: If the records are not shaped as above, the rate is
        missing or disagrees, a window does not fit its record, or a
        parameter is out of range.
    :warns BarrierReflectionWarning: For an :math:`R_{sub}` below 10 dB, a
        gain factor more than 20 % from 1, or a sample rate below 44 kHz.
    """
    fronts = _grid_positions(in_front_irs, "in_front_irs")
    frees = _grid_positions(free_field_irs, "free_field_irs")
    rate = _require_fs(_grid_rate(fronts, frees, fs))
    speed = require_positive(speed_of_sound, "speed_of_sound")
    in_front = [_grid_record(entry, "in_front_irs") for entry in fronts]
    free_field = [_grid_record(entry, "free_field_irs") for entry in frees]
    shapes = [record.shape for record in in_front]
    if shapes != [record.shape for record in free_field]:
        msg = (
            f"'in_front_irs' and 'free_field_irs' must have the same shape; got "
            f"{shapes} and {[record.shape for record in free_field]}."
        )
        raise ValueError(msg)
    high = _per_microphone(window_length_s, "window_length_s")
    low = _per_microphone(low_band_window_length_s, "low_band_window_length_s")
    low_mics = sorted({int(k) for k in low_band_microphones})
    if not low_mics or low_mics[0] < 1 or low_mics[-1] > _MICROPHONES:
        msg = "'low_band_microphones' must name microphones between 1 and 9."
        raise ValueError(msg)
    directivity = _directivity(directivity_corrections)
    paths = reflection_grid_paths_m()
    divergence = (paths[:, 1] / paths[:, 0]) ** 2
    delays = (paths[:, 1] - paths[:, 0]) / speed * rate
    calibration = adrienne_reflection_window(rate, ADRIENNE_CALIBRATION_LENGTH_S)
    gain_lower = (_BAND_LOWER_HZ[_BANDS_HZ.index(_GAIN_BANDS_HZ[0])],)
    gain_upper = (_BAND_UPPER_HZ[_BANDS_HZ.index(_GAIN_BANDS_HZ[1])],)

    positions = len(in_front)
    bands = len(_BANDS_HZ)
    values = np.full((positions, _MICROPHONES, bands), np.nan)
    gains = np.empty((positions, _MICROPHONES))
    reductions = np.empty((positions, _MICROPHONES))
    low_bands = slice(0, _FIRST_FULL_GRID_BAND)
    high_bands = slice(_FIRST_FULL_GRID_BAND, None)
    for p in range(positions):
        for k in range(_MICROPHONES):
            where = f" at microphone {k + 1} of grid position {p + 1}"
            sub = _subtract(in_front[p][k], free_field[p][k], rate)
            _warn_reduction(sub.reduction_db, where)
            reductions[p, k] = sub.reduction_db
            direct_peak = float(sub.peak_index)
            free_peak = float(np.argmax(np.abs(free_field[p][k])))
            gain = float(
                _band_energies(
                    _windowed(
                        in_front[p][k], direct_peak, calibration, rate, "gain check"
                    ),
                    rate,
                    gain_lower,
                    gain_upper,
                )[0]
                / _band_energies(
                    _windowed(
                        free_field[p][k], free_peak, calibration, rate, "gain check"
                    ),
                    rate,
                    gain_lower,
                    gain_upper,
                )[0]
            )
            _warn_gain(gain, where)
            gains[p, k] = gain
            groups = [(high, high_bands)]
            if k + 1 in low_mics:
                groups.append((low, low_bands))
            for lengths, selected in groups:
                window = adrienne_reflection_window(rate, float(lengths[k]))
                incident = _band_energies(
                    _windowed(
                        free_field[p][k], free_peak, window, rate, "incident component"
                    ),
                    rate,
                    _BAND_LOWER_HZ[selected],
                    _BAND_UPPER_HZ[selected],
                )
                reflected = _band_energies(
                    _windowed(
                        np.asarray(sub.residual),
                        direct_peak + delays[k],
                        window,
                        rate,
                        "reflected component",
                    ),
                    rate,
                    _BAND_LOWER_HZ[selected],
                    _BAND_UPPER_HZ[selected],
                )
                values[p, k, selected] = (
                    reflected
                    / incident
                    * divergence[k]
                    * directivity[k, selected]
                    / gain
                )
    counts = np.sum(np.isfinite(values), axis=1)
    sums = np.nansum(values, axis=1)
    position_values = np.full(counts.shape, np.nan)
    np.divide(sums, counts, out=position_values, where=counts > 0)
    return _result(
        position_values,
        values.reshape(-1, bands),
        lowest_band_hz,
        microphone_values=values,
        gain_corrections=gains,
        reductions_db=reductions,
    )


def _warn_gain(gain: float, where: str) -> None:
    """The 20 % warning of 5.5.1."""
    if abs(gain - 1.0) > _GAIN_WARNING:
        msg = (
            f"the gain factor C_gain is {gain:.3f}{where}, more than 20 % from 1: "
            f"EN 1793-5 5.5.1 reads that as a change of the measurement settings "
            f"between the free-field and the in-front records, and asks to "
            f"recheck the data."
        )
        warnings.warn(msg, BarrierReflectionWarning, stacklevel=3)


# --------------------------------------------------------------------------- #
# Low frequency limit and sample size (5.5.7)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ReflectionFrequencyLimit(OwnsArrays):
    r"""How far down a device of a given size can be measured, 5.5.7.

    :ivar device_height_m: :math:`h_B`, the height of the device.
    :ivar device_length_m: The length of the sample, or ``None`` when its
        side edges were not considered.
    :ivar source_height_m: :math:`h_S`, the height of the loudspeaker and of
        microphone 5.
    :ivar window_length_s: Per microphone, the longest Adrienne window whose
        tail ends before the first unwanted component: the flat part and the
        trailing edge last as long as the delay between the reflection and
        that component, plus the 0,5 ms leading edge.
    :ivar low_frequency_limit_hz: Per microphone, the first notch of that
        window's spectrum (:func:`adrienne_low_frequency_limit_hz`).
    :ivar limiting_component: Per microphone, ``"ground"`` for the ground
        reflection on the source side, ``"top edge"`` or ``"side edge"`` for
        a diffraction by an edge of the device.
    """

    device_height_m: float
    device_length_m: float | None
    source_height_m: float
    window_length_s: NDArray[np.float64]
    low_frequency_limit_hz: NDArray[np.float64]
    limiting_component: tuple[str, ...]

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the limit at each microphone and what sets it.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the ``Axes.bar`` call.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_reflection_frequency_limit

        return plot_reflection_frequency_limit(
            self, ax=ax, language=check_language(language), **kwargs
        )


def reflection_low_frequency_limit(
    device_height_m: float,
    *,
    speed_of_sound: float,
    device_length_m: float | None = None,
    source_height_m: float | None = None,
) -> ReflectionFrequencyLimit:
    r"""The low frequency limit of each microphone for a device's size, 5.5.7.

    The reflected window has to end before the sound reflected by the ground on
    the source side and the sound diffracted by the edges of the device reach
    the microphone. With the loudspeaker at :math:`h_S` (half the height by
    default, 3.11) the ground reflection comes from the image of the
    loudspeaker below the ground; the edge diffraction takes the shortest path
    over the top edge, and over each side edge of a sample of the given
    length centred on the grid. The window's marker is 0,2 ms before the
    reflection and its tail is taken to end 0,2 ms before the unwanted
    component, as its own marker would sit, so the flat part and the trailing
    edge together last exactly the delay between the two; the limit is the
    first notch of that window's spectrum.

    This is the construction of Garai and Guidorzi (J. Acoust. Soc. Am. 108
    (2000) 1054, section III.D), not a formula of EN 1793-5, which prints the
    result only as Figure 14. At microphone 5 of a 4 m device it gives
    167 Hz, where 5.5.7 reads about 170 Hz; the guide compares all three
    curves.

    :param device_height_m: :math:`h_B`, in metres.
    :param speed_of_sound: Speed of sound at the air temperature of the
        test, in metres per second.
    :param device_length_m: The length of the sample, in metres, to include
        its two side edges; ``None`` considers the ground and the top edge,
        which is the case 5.5.7 treats for a device longer than it is high.
    :param source_height_m: :math:`h_S`, in metres; ``None`` for
        :math:`h_B/2`. 3.11 allows 2 m above a 4 m device.
    :return: The :class:`ReflectionFrequencyLimit`, with ``.plot()``.
    :raises ValueError: If a dimension is not positive, the grid does not fit
        between the ground and the top edge, the sample is narrower than the
        grid, or at some microphone the ground reflection or an edge arrives no
        later than the reflection itself (a device below about 1,7 m).
    """
    height = require_positive(device_height_m, "device_height_m")
    speed = require_positive(speed_of_sound, "speed_of_sound")
    source = (
        height / 2.0
        if source_height_m is None
        else require_positive(source_height_m, "source_height_m")
    )
    spacing = REFLECTION_GRID_SPACING_M
    if source - spacing <= 0.0 or source + spacing >= height:
        msg = (
            f"the grid, {spacing:g} m above and below the loudspeaker at "
            f"{source:g} m, must fit between the ground and the top edge of a "
            f"{height:g} m device."
        )
        raise ValueError(msg)
    length = (
        None
        if device_length_m is None
        else require_positive(device_length_m, "device_length_m")
    )
    if length is not None and length / 2.0 <= spacing:
        msg = f"a {length:g} m sample is narrower than the {2 * spacing:g} m grid."
        raise ValueError(msg)
    d_s = REFLECTION_SOURCE_DISTANCE_M
    d_m = REFLECTION_MICROPHONE_DISTANCE_M
    paths = reflection_grid_paths_m()
    windows = np.empty(_MICROPHONES)
    limits = np.empty(_MICROPHONES)
    components: list[str] = []
    for k, (lateral_steps, vertical_steps) in enumerate(_GRID_OFFSETS):
        lateral = lateral_steps * spacing
        z = source + vertical_steps * spacing
        candidates = {
            "ground": math.sqrt((d_s - d_m) ** 2 + lateral**2 + (z + source) ** 2),
            "top edge": math.hypot(
                math.hypot(d_s, height - source) + math.hypot(d_m, height - z), lateral
            ),
        }
        if length is not None:
            half = length / 2.0
            candidates["side edge"] = min(
                math.hypot(
                    math.hypot(d_s, half) + math.hypot(d_m, half - side * lateral),
                    z - source,
                )
                for side in (1.0, -1.0)
            )
        component = min(candidates, key=candidates.__getitem__)
        delay = (candidates[component] - float(paths[k, 1])) / speed
        if delay <= 0.0:
            msg = (
                f"at microphone {k + 1} the {component} arrives no later than the "
                f"reflection from the device, so no window separates the two: a "
                f"{height:g} m device is too low for the grid of EN 1793-5."
            )
            raise ValueError(msg)
        windows[k] = _LEADING_EDGE_S + delay
        limits[k] = adrienne_low_frequency_limit_hz(float(windows[k]))
        components.append(component)
    return ReflectionFrequencyLimit(
        device_height_m=height,
        device_length_m=length,
        source_height_m=source,
        window_length_s=read_only(windows),
        low_frequency_limit_hz=read_only(limits),
        limiting_component=tuple(components),
    )


# --------------------------------------------------------------------------- #
# Position checks (5.6.2.5, 5.6.2.6)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ReflectionGridCheck(OwnsArrays):
    r"""The position check of 5.6.2.5 or 5.6.2.6, against Table 3.

    The nominal path differences and the tolerance are Table 3's, so they are
    read from the check and are not fields: a check cannot be built, or
    rewritten with :func:`dataclasses.replace`, against other nominal values
    or another tolerance.

    :ivar check: ``"relative"`` (5.6.2.5, the loudspeaker against the grid,
        :math:`\Delta d_{k5}`) or ``"grid"`` (5.6.2.6, the grid against the
        reference plane, :math:`\Delta d_k`).
    :ivar path_differences_m: :math:`c\,\Delta t`, Formula (10) or (11), per
        microphone, microphone 1 first, in metres; microphone 5 does not take
        part in the relative check.
    """

    check: str
    path_differences_m: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Hold the path differences read-only and refuse an unknown check.

        :raises ValueError: If the check is not ``"relative"`` or ``"grid"``,
            or there are not nine finite path differences.
        """
        require_choice(self.check, "check", ("relative", "grid"))
        measured = np.asarray(self.path_differences_m, dtype=np.float64)
        if measured.shape != (_MICROPHONES,) or not np.all(np.isfinite(measured)):
            msg = (
                "ReflectionGridCheck: 'path_differences_m' must hold nine "
                "finite path differences, microphone 1 first."
            )
            raise ValueError(msg)
        object.__setattr__(self, "path_differences_m", read_only(measured))

    @property
    def nominal_m(self) -> NDArray[np.float64]:
        r"""The nominal values of Table 3 for this check, in metres.

        :return: :math:`\Delta d_{k5}` for the relative check, :math:`\Delta
            d_k` for the grid check, microphone 1 first.
        """
        column = 0 if self.check == "relative" else 1
        return read_only(
            np.array(
                [
                    REFLECTION_PATH_DIFFERENCES_M[k][column]
                    for k in range(1, _MICROPHONES + 1)
                ],
                dtype=np.float64,
            )
        )

    @property
    def deviations_m(self) -> NDArray[np.float64]:
        """Measured minus nominal, in metres.

        :return: One deviation per microphone; zero for microphone 5 in the
            relative check, which does not take part in it.
        """
        deviations = self.path_differences_m - self.nominal_m
        if self.check == "relative":
            deviations[4] = 0.0
        return read_only(deviations)

    @property
    def within(self) -> NDArray[np.bool_]:
        r"""Per microphone, whether the deviation is within :math:`\pm\varepsilon_k`.

        :return: ``True`` where the deviation is within the 25 mm of Table 3
            (:data:`REFLECTION_PATH_TOLERANCE_M`).
        """
        return read_only(
            np.abs(self.deviations_m)
            <= REFLECTION_PATH_TOLERANCE_M + _TOLERANCE_SLACK_M
        )

    @property
    def passes(self) -> bool:
        """Whether every microphone is within tolerance, so the set-up is correct.

        :return: ``True`` when step 8 finds the position correct.
        """
        return bool(np.all(self.within))

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a ReflectionGridCheck has no truth value; read '.passes'"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw each microphone's deviation against the 25 mm tolerance.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the deviation ``Axes.plot`` call.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_reflection_grid_check

        return plot_reflection_grid_check(
            self, ax=ax, language=check_language(language), **kwargs
        )


def check_reflection_grid_position(
    time_delays_s: ArrayLike,
    *,
    speed_of_sound: float,
    check: Literal["relative", "grid"] = "grid",
) -> ReflectionGridCheck:
    r"""Check the loudspeaker and grid positions with a reflecting plate.

    5.6.2.5 (``check="relative"``): with a plate 0,25 m behind microphone 5,
    the delays :math:`\Delta t_{k5}` between the direct sound at microphone
    :math:`k` and at microphone 5 give :math:`\Delta d_{k5} = c\,\Delta
    t_{k5}` (Formula (10)); microphone 5 does not take part. 5.6.2.6
    (``check="grid"``): with the plate on the reference plane, the delays
    :math:`\Delta t_k` between the direct and the reflected sound at each
    microphone give :math:`\Delta d_k = c\,\Delta t_k` (Formula (11)). Either
    way the set-up is correct when every path difference is within
    :math:`\pm 25` mm of Table 3.

    :param time_delays_s: The nine delays, microphone 1 first, in seconds; for
        the relative check the fifth is ignored.
    :param speed_of_sound: Speed of sound at the air temperature, in
        metres per second.
    :param check: ``"relative"`` or ``"grid"``.
    :return: The :class:`ReflectionGridCheck` verdict.
    :raises ValueError: If there are not nine finite delays, the speed is not
        positive or the check is unknown.
    """
    kind = require_choice(check, "check", ("relative", "grid"))
    speed = require_positive(speed_of_sound, "speed_of_sound")
    delays = np.asarray(time_delays_s, dtype=np.float64)
    if delays.shape != (_MICROPHONES,) or not np.all(np.isfinite(delays)):
        msg = "'time_delays_s' must hold nine finite delays, microphone 1 first."
        raise ValueError(msg)
    measured = speed * delays
    if kind == "relative":
        measured[4] = REFLECTION_PATH_DIFFERENCES_M[5][0]
    return ReflectionGridCheck(check=kind, path_differences_m=measured)
