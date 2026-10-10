#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Headphones and earphones: the characteristics of IEC 60268-7:2010 that are computations.

IEC 60268-7:2010 (Edition 3.0) lists what the manufacturer of a headphone,
headset, earphone or earset states, and how each characteristic is measured.
Most of the clauses describe a set-up and a reading; this module holds the
parts that are arithmetic on what was read, and the verdicts where the part
sets a limit. The simulated programme signal several of them use is the one
of IEC 60268-1:1985 Clause 7, in
:mod:`phonometry.electroacoustics.programme_signal`.

The code (Clause 4)
-------------------

A headphone is classified by the code ``60268-7-IEC-XXXX-NNRN-N``: four
letters for the transducer principle, the type of earphone, the acoustic
coupling to the ear canal and the radiation to the outside
(:data:`TRANSDUCER_PRINCIPLES`, :data:`EARPHONE_TYPES`,
:data:`ACOUSTIC_COUPLINGS`, :data:`BACK_RADIATIONS`), the impedance in ohms in
"mantissa and exponent" form, and the number of channels. The clause prints
three impedances, 8 ohm as ``08R0``, 32 ohm as ``32R0`` and 600 ohm as
``06R2``: a two-digit mantissa times ten to the digit after the ``R``. The
600 ohm example settles the one choice the rule leaves open, between ``06R2``
and ``60R1``: the exponent takes every trailing zero, so 150 ohm is ``15R1``
and 300 ohm ``03R2`` (:func:`impedance_code`). :class:`HeadphoneClassification`
writes the code and :func:`parse_classification_code` reads it.

Impedance (8.2)
---------------

The rated impedance is a pure resistance the manufacturer states, "chosen so
that the lowest value of the modulus of the actual impedance within the rated
frequency range is not less than 80 % of the rated value"; a dip below that
anywhere from 0 kHz to 20 kHz "should be stated in the specification". The
modulus is measured "at least over the frequency range 20 Hz to 20 kHz"
(8.2.2.2). :func:`verify_rated_impedance` judges both.

Voltages, powers and sound pressure levels (8.3 to 8.5)
-------------------------------------------------------

Every input of IEC 60268-7 is a source e.m.f. :math:`E` applied through the
rated source impedance :math:`R_\mathrm{s}`. The **characteristic voltage**
(8.3.3) is the 500 Hz sinusoidal e.m.f. that produces 94 dB in the coupler or
ear simulator; the headphone is linear there, so one reading :math:`L` at an
e.m.f. :math:`E` gives it as :math:`E\,10^{(94 - L)/20}`
(:func:`characteristic_voltage`). The **simulated programme signal
characteristic voltage** (8.3.4) is the same with the programme signal, and
8.3.5 adds the A-weighting of IEC 61672-1 and the inverse of the free-field
response of the head and torso simulator of IEC 60959 to the coupler's output.
The NOTE under Figure 3 says how to do that without filters: "Power summation
of the 1/3-octave-analized data multiplied by filtering coefficients given by
IEC 61672-1 and/or IEC 60969 gives the corrected voltage" (the second
standard is IEC 60959, see ``docs/ERRATA.md``). :func:`programme_signal_level`
is that power sum,

.. math::

   L = 10\lg \sum_k 10^{(L_k + A_k - F_k)/10},

with :math:`A_k` the A-weighting at the exact centre of band :math:`k` and
:math:`F_k` the free-field response, and
:func:`programme_characteristic_voltage` turns it into the e.m.f. for 94 dB,
for each fitting of the headphone, and averages the e.m.f. of the fittings as
8.3.5 g) asks ("3 to 5 measurements").

8.4 states each of these as a power instead, "derived from the corresponding
voltages (8.3) and the rated impedance": the power the e.m.f. dissipates in a
pure resistance equal to the rated impedance :math:`R` connected in place of
the headphone, :math:`P = E^2 R/(R + R_\mathrm{s})^2`
(:func:`headphone_input_power`, and :func:`headphone_source_emf` the other way
round). The **working sound pressure level** of 8.5.2 b) to d) is the level at
the e.m.f. that dissipates 1 mW that way (:func:`working_sound_pressure_level`).
The method of 8.5.3 c) sets the e.m.f. differently, so that the voltage
across the headphone's own input connector is :math:`\sqrt{1\ \mathrm{mW}
\cdot R}`; the two agree only when the headphone's impedance at 500 Hz is the
rated one, and the function gives the second reading when that impedance is
passed (see ``docs/ERRATA.md``).

8.3.1 NOTE 3 recommends that the rated source e.m.f. "should, preferably, not
exceed the characteristic voltage (see 8.3.3) by more than 10 dB to 15 dB";
the excess is :math:`20\lg` of their ratio, and a preference stated as a range
is not a limit, so no verdict is offered on it.

The clipped programme signal of 8.3.2, which rates the voltages a headphone
survives, has "a frequency distribution as specified in IEC 60268-1, and a
peak-to-r.m.s ratio between 1,8 and 2,2" (:func:`check_limiting_test_signal`).
A protective device "causes a change of at least 1 dB in the sensitivity" at
its protection voltage (8.3.6.2 b), which :func:`protection_voltage` finds in a
sweep of e.m.f. and level.

Frequency responses (8.6) and crosstalk (8.12)
----------------------------------------------

The coupler or ear simulator frequency response (8.6.2) is the level against
frequency at the rated e.m.f., and its graph has "the same length
representing 50 dB as represents one decade of frequency"
(:func:`coupler_frequency_response`). The crosstalk attenuation (8.12) is the
difference of two such curves (:func:`crosstalk_attenuation`).

The two subjective responses (8.6.3, 8.6.4) are the quotient of the reference
field's sound pressure by the e.m.f. that makes the headphone equally loud,
"expressed in decibels referred to the value at the standard reference
frequency", averaged over at least eight test persons with the standard
deviation in each band (:func:`field_comparison_response`); a headphone
calibrated on at least 16 persons may then serve as the reference of the
substitution method. The ear-canal responses (8.6.5) read a probe microphone
in the ear canal instead of a loudness judgement, by Formula (1),

.. math::

   L_\mathrm{f} = L_\mathrm{e} - L_\mathrm{s} - (L_\mathrm{e} - L_\mathrm{s})_{500},

after averaging the two fittings of the headphone and the two readings of the
sound field, with the procedure repeated when the two fittings differ by more
than 2,5 dB in any band (:func:`ear_canal_frequency_response`). A headphone
measured that way on at least 16 persons may replace the sound field of the
indirect method (8.6.5.3, whose two references to 8.6.4.2 are read as 8.6.5.2,
see ``docs/ERRATA.md``). The microphone in the ear canal is specified by
Annex B (:func:`verify_ear_canal_microphone`).

The two reference frequencies are not the same. Formula (1) prints its
reference band, 500 Hz, the standard measuring frequency of 7.2 b). The
comparison responses are referred to "the standard reference frequency", a
term IEC 60268-7 uses without defining; IEC 60268-1:1985 Clause 3, which it
cites, sets it at 1 000 Hz "in the absence of a clear reason to the
contrary", and 8.6.3.2 c) and 8.6.4.2 c) begin and end the test sequence on
that band, so :func:`field_comparison_response` refers to 1 000 Hz by default.
The coupler response keeps 500 Hz, for the reason the NOTE of 8.3.3.1 gives:
the coupler's own resonances, leakage and standing waves at other frequencies.
The frequency response itself has no tolerance: "It is not at present
possible to set limits for the frequency range based on deviations from a
flat, or defined, frequency response" (8.6.6 NOTE 2), so the rated frequency
range is the manufacturer's statement and enters only as the range a
measurement has to cover.

Distortion (8.7)
----------------

The harmonic, modulation and difference-frequency distortions are those of
IEC 60268-2, read with :func:`~phonometry.electroacoustics.harmonic_distortion`,
:func:`~phonometry.electroacoustics.modulation_distortion` and
:func:`~phonometry.electroacoustics.difference_frequency_distortion`, and
expressed in decibels as :math:`20\lg` of the ratio. What 60268-7 adds are the
test signals: 70 Hz and 600 Hz in the amplitude ratio 4:1 with the peak of the
rated input voltage, "−1,9 dB at 70 Hz and −14,0 dB at 600 Hz" (NOTE 1 of
8.7.3.3; :func:`headphone_modulation_signal`), and two tones 80 Hz apart, each
at half the rated input voltage (:func:`headphone_difference_frequency_signal`).
The third-order modulation products are at 460 Hz and 740 Hz, as 8.7.3.3 b)
says; Formula (3) prints :math:`U_{470}` (see ``docs/ERRATA.md``).

What is not here
----------------

The rated conditions (7.1, 8.6.6, 8.8, 8.13, 8.14) are stated, not computed.
The external field (8.9) and the unwanted radiation (8.10) are readings. The
sound attenuation of 8.11 is measured "as specified in ISO 4869-1", which
:func:`phonometry.hearing.real_ear_attenuation` computes from the open and
occluded thresholds of the subjects; for a headphone with active noise
compensation, which the NOTE of 8.11.2 says "may require a modified
procedure", :func:`phonometry.hearing.anr_total_attenuation` follows ISO
4869-6. Annex A is the geometry of a pinna simulator and Annexes C to E are
informative practical conditions.
"""

from __future__ import annotations

import cmath
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from .._internal.boundary import settled
from .._internal.frozen import OwnsArrays, read_only
from .._internal.validation import require_count, require_positive, require_scalar
from .programme_signal import ProgrammeSignalCheck, check_programme_signal

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

    from ..io._signal import Signal

__all__ = [
    "ACOUSTIC_COUPLINGS",
    "BACK_RADIATIONS",
    "EARPHONE_TYPES",
    "TRANSDUCER_PRINCIPLES",
    "CouplerFrequencyResponse",
    "CrosstalkAttenuation",
    "EarCanalFrequencyResponse",
    "EarCanalMicrophoneVerification",
    "FieldComparisonResponse",
    "HeadphoneClassification",
    "LimitingTestSignalCheck",
    "ProgrammeCharacteristicVoltage",
    "ProtectionVoltage",
    "RatedImpedanceVerification",
    "characteristic_voltage",
    "check_limiting_test_signal",
    "coupler_frequency_response",
    "crosstalk_attenuation",
    "ear_canal_frequency_response",
    "field_comparison_response",
    "headphone_difference_frequency_signal",
    "headphone_input_power",
    "headphone_modulation_signal",
    "headphone_source_emf",
    "impedance_code",
    "parse_classification_code",
    "programme_characteristic_voltage",
    "programme_signal_level",
    "protection_voltage",
    "verify_ear_canal_microphone",
    "verify_rated_impedance",
    "working_sound_pressure_level",
]

# ---------------------------------------------------------------------------
# Clause 4: classification, designation and coding
# ---------------------------------------------------------------------------

#: The first letter of the code, the principle of the transducer
#: (IEC 60268-7:2010 Clause 4, PDF page 11, printed page 9).
TRANSDUCER_PRINCIPLES: Mapping[str, str] = MappingProxyType(
    {
        "D": "electrodynamic (moving coil)",
        "E": "electret (self-polarizing)",
        "F": "piezo-electric (polymer)",
        "M": "electromagnetic (moving armature or diaphragm)",
        "P": "piezo-electric (ceramic)",
        "S": "electrostatic (externally polarized)",
    }
)

#: The second letter, the type of earphone (Clause 4).
EARPHONE_TYPES: Mapping[str, str] = MappingProxyType(
    {
        "C": "circumaural",
        "E": "intra-concha",
        "H": "earshell",
        "I": "insert",
        "M": "supra-concha",
        "S": "supra-aural",
        "T": "stethoscopic",
    }
)

#: The third letter, the intended acoustic coupling to the ear canal (Clause 4).
ACOUSTIC_COUPLINGS: Mapping[str, str] = MappingProxyType(
    {
        "L": "acoustically open (controlled leakage)",
        "S": "acoustically closed (minimum leakage)",
    }
)

#: The fourth letter, the intended radiation to the external environment
#: (Clause 4, with 3.14 and 3.15).
BACK_RADIATIONS: Mapping[str, str] = MappingProxyType(
    {
        "C": "closed-back",
        "O": "open-back",
    }
)

#: The prefix of the code, "the standard form of prefix" (Clause 4).
_CODE_PREFIX = "60268-7-IEC"

#: The largest mantissa and exponent of the NNRN form: two digits and one.
_MAX_MANTISSA = 99
_MAX_EXPONENT = 9
#: The largest number of channels the one-digit N of the code can hold.
_MAX_CHANNELS = 9

#: How close an impedance must be to a whole number of ohms to be coded.
_WHOLE_OHM_RTOL = 1e-9

_CODE_PATTERN = re.compile(
    r"^60268-7-IEC-([A-Z])([A-Z])([A-Z])([A-Z])-(\d\d)R(\d)-(\d)$"
)


def impedance_code(impedance_ohm: float) -> str:
    """The NNRN form of an impedance in the code of IEC 60268-7 Clause 4.

    A two-digit mantissa, ``R``, and a one-digit exponent of ten: "8 Ω as
    "08R0", 32 Ω as "32R0" and 600 Ω as "06R2"". The exponent takes every
    trailing zero of the whole number of ohms, which is the reading the 600 ohm
    example fixes (``06R2``, not ``60R1``).

    :param impedance_ohm: The impedance, in ohms: a whole number whose digits
        before the trailing zeros number at most two.
    :return: The four characters, for instance ``"32R0"``.
    :raises ValueError: If the impedance is not a positive whole number of
        ohms or does not fit the form: ``4.7`` ohm is not whole, and ``123``
        ohm needs a mantissa of three digits.
    """
    value = require_positive(impedance_ohm, "impedance_ohm")
    whole = round(value)
    if whole < 1 or not math.isclose(value, whole, rel_tol=_WHOLE_OHM_RTOL):
        msg = f"'impedance_ohm' must be a whole number of ohms; got {value:g}."
        raise ValueError(msg)
    mantissa, exponent = whole, 0
    while mantissa % 10 == 0:
        mantissa //= 10
        exponent += 1
    if mantissa > _MAX_MANTISSA or exponent > _MAX_EXPONENT:
        msg = (
            f"{whole} ohm does not fit the NNRN form of a two-digit mantissa "
            "and a one-digit exponent."
        )
        raise ValueError(msg)
    return f"{mantissa:02d}R{exponent}"


def _require_letter(value: str, name: str, table: Mapping[str, str]) -> str:
    """A code letter that is one of ``table``'s keys."""
    if value not in table:
        options = ", ".join(sorted(table))
        msg = f"'{name}' must be one of {options}; got {value!r}."
        raise ValueError(msg)
    return value


@dataclass(frozen=True)
class HeadphoneClassification:
    """The classification of a headphone by IEC 60268-7:2010 Clause 4.

    :ivar principle: The principle of the transducer, a key of
        :data:`TRANSDUCER_PRINCIPLES`.
    :ivar earphone_type: The type of earphone, a key of
        :data:`EARPHONE_TYPES`.
    :ivar coupling: The acoustic coupling to the ear canal, a key of
        :data:`ACOUSTIC_COUPLINGS`.
    :ivar radiation: The radiation to the external environment, a key of
        :data:`BACK_RADIATIONS`.
    :ivar impedance_ohm: The impedance, in ohms, as coded by
        :func:`impedance_code`.
    :ivar channels: The number of channels, 1 to 9.
    """

    principle: str
    earphone_type: str
    coupling: str
    radiation: str
    impedance_ohm: float
    channels: int

    def __post_init__(self) -> None:
        """Refuse a letter the clause does not define or a value it cannot code.

        :raises ValueError: If a letter is not in its table, the impedance
            does not fit the NNRN form or the channels are not 1 to 9.
        """
        _require_letter(self.principle, "principle", TRANSDUCER_PRINCIPLES)
        _require_letter(self.earphone_type, "earphone_type", EARPHONE_TYPES)
        _require_letter(self.coupling, "coupling", ACOUSTIC_COUPLINGS)
        _require_letter(self.radiation, "radiation", BACK_RADIATIONS)
        impedance_code(self.impedance_ohm)
        channels = require_count(self.channels, "channels")
        if channels > _MAX_CHANNELS:
            msg = f"'channels' must be 1 to {_MAX_CHANNELS}, one digit of the code."
            raise ValueError(msg)

    @property
    def code(self) -> str:
        """The code, for instance ``"60268-7-IEC-DCSC-32R0-2"``."""
        letters = self.principle + self.earphone_type + self.coupling + self.radiation
        return (
            f"{_CODE_PREFIX}-{letters}-{impedance_code(self.impedance_ohm)}-"
            f"{self.channels}"
        )

    @property
    def description(self) -> str:
        """The four letters in words, in the clause's terms."""
        return ", ".join(
            (
                TRANSDUCER_PRINCIPLES[self.principle],
                EARPHONE_TYPES[self.earphone_type],
                ACOUSTIC_COUPLINGS[self.coupling],
                BACK_RADIATIONS[self.radiation],
            )
        )


def parse_classification_code(code: str) -> HeadphoneClassification:
    """Read a classification code of IEC 60268-7:2010 Clause 4.

    Spaces around the hyphens are ignored, so the clause's own layout,
    ``60268-7 - IEC - XXXX - NNRN - N``, reads as well as the compact one.

    :param code: The code, for instance ``"60268-7-IEC-DCSC-32R0-2"``.
    :return: A :class:`HeadphoneClassification`.
    :raises ValueError: If the code does not have the form of the clause or a
        letter or number is not one it defines.
    """
    compact = "-".join(part.strip() for part in str(code).split("-")).upper()
    match = _CODE_PATTERN.match(compact)
    if match is None:
        msg = f"{code!r} is not a code of the form 60268-7-IEC-XXXX-NNRN-N."
        raise ValueError(msg)
    principle, earphone, coupling, radiation, mantissa, exponent, channels = (
        match.groups()
    )
    return HeadphoneClassification(
        principle=principle,
        earphone_type=earphone,
        coupling=coupling,
        radiation=radiation,
        impedance_ohm=float(int(mantissa) * 10 ** int(exponent)),
        channels=int(channels),
    )


# ---------------------------------------------------------------------------
# Shared input handling
# ---------------------------------------------------------------------------

#: The standard measuring frequency of 7.2 b), in hertz, which is also the
#: reference band of Formula (1) and of the coupler response (8.3.3.1 NOTE).
_MEASURING_FREQUENCY_HZ = 500.0

#: The standard reference frequency of IEC 60268-1:1985 Clause 3, in hertz,
#: to which 8.6.3.1 and 8.6.4.1 refer the comparison responses.
_STANDARD_REFERENCE_FREQUENCY_HZ = 1000.0

#: The sound pressure level of the standard conditions, 7.2 b), in dB re 20 µPa.
_STANDARD_LEVEL_DB = 94.0

#: The power of the working sound pressure level, 8.5.2 b), in watts.
_WORKING_POWER_W = 1e-3

#: The lowest modulus of the impedance in the rated frequency range, as a
#: fraction of the rated impedance (8.2.1 b).
_RATED_IMPEDANCE_FRACTION = 0.8

#: The range over which the impedance is stated and measured (8.2.1 b,
#: 8.2.2.2 c), in hertz.
_IMPEDANCE_RANGE_HZ = (20.0, 20000.0)

#: The peak-to-RMS ratio of the clipped programme signal (8.3.2.2 b).
_LIMITING_PEAK_TO_RMS = (1.8, 2.2)

#: The exact base-ten centres of the bands of IEC 60268-1 Table II, 20 Hz to
#: 20 kHz, in hertz (19,95 Hz to 19,95 kHz), and the ratio of a band's upper
#: edge to its centre.
_TABLE_II_EXACT: tuple[float, ...] = tuple(
    1000.0 * 10.0 ** (n / 10.0) for n in range(-17, 14)
)
_THIRD_OCTAVE_EDGE = 10.0 ** (1.0 / 20.0)

#: The sensitivity change that marks a protective device's operation, and the
#: steps either side of it at which the impedance and level are measured
#: (8.3.6.2 b), in dB.
_PROTECTION_STEP_DB = 1.0

#: The fewest test persons of a direct measurement (8.6.3.2 d, 8.6.4.2 d,
#: 8.6.5.2 h) and of the reference headphone of the substitution and indirect
#: methods (8.6.3.3, 8.6.4.3, and 8.6.5.3 read as calibrated by 8.6.5.2).
_MIN_PERSONS = 8
_MIN_REFERENCE_PERSONS = 16

#: The largest difference between the two fittings of an ear-canal
#: measurement (8.6.5.2 f), and the window within which the earphone's 500 Hz
#: band is set against the sound field's (8.6.5.2 c), in dB.
_MAX_FITTING_DIFFERENCE_DB = 2.5
_LEVEL_MATCH_DB = 3.0

#: The fittings averaged for the corrected characteristic voltage, 8.3.5 g).
_FITTINGS_RANGE = (3, 5)

#: The modulation and difference-frequency test signals of 8.7.3 and 8.7.4.
_MODULATION_FREQUENCIES_HZ = (70.0, 600.0)
_MODULATION_RATIO = 4.0
_DIFFERENCE_FREQUENCY_HZ = 80.0

#: Annex B: the microphone in the ear canal.
_MAX_ENTRANCE_AREA_MM2 = 5.0
_MAX_CANAL_AREA_RATIO = 0.6
_ADULT_EAR_CANAL_AREA_MM2 = 45.0
_MAX_VOLUME_MM3 = 130.0
_MAX_NEIGHBOUR_DIFFERENCE_DB = 3.0
_MIN_SEALED_ATTENUATION_DB = 15.0

#: Slack on a printed limit, in dB or as a ratio: a value printed exactly on
#: its limit is on the side the limit includes, whatever the last bits of the
#: arithmetic make of it.
_LIMIT_SLACK = 1e-9

#: The fewest points a spread, a change, a neighbour or a relative spectrum
#: needs, and the rank of a (rows, bands) matrix.
_FEWEST_POINTS = 2
_MATRIX_NDIM = 2

#: The shape of the ear-canal readings: (persons, readings, bands), with the
#: two readings of 8.6.5.2, items c) and d) or b) and e).
_PANEL_NDIM = 3
_READINGS = 2

#: How far a frequency may sit from a requested one and still be read as it.
_FREQUENCY_MATCH_RTOL = 1e-6


def _frequencies(
    frequencies_hz: ArrayLike, name: str = "frequencies_hz"
) -> NDArray[np.float64]:
    """Positive, finite, strictly ascending frequencies, 1-D."""
    f = np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64))
    if f.ndim != 1 or f.size == 0:
        msg = f"'{name}' must be a non-empty 1-D sequence."
        raise ValueError(msg)
    if not (np.all(np.isfinite(f)) and np.all(f > 0.0)):
        msg = f"'{name}' must hold positive, finite frequencies."
        raise ValueError(msg)
    if np.any(np.diff(f) <= 0.0):
        msg = f"'{name}' must be strictly ascending."
        raise ValueError(msg)
    return f


def _levels(values: ArrayLike, name: str) -> NDArray[np.float64]:
    """A finite float array of levels."""
    levels = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(levels)):
        msg = f"'{name}' must be finite."
        raise ValueError(msg)
    return levels


def _band_index(frequencies: NDArray[np.float64], target_hz: float) -> int:
    """The index of the band at ``target_hz``, which must be among them."""
    matches = np.flatnonzero(
        np.isclose(frequencies, target_hz, rtol=_FREQUENCY_MATCH_RTOL, atol=0.0)
    )
    if matches.size == 0:
        msg = f"The frequencies must include the reference band at {target_hz:g} Hz."
        raise ValueError(msg)
    return int(matches[0])


def _db20(ratio: ArrayLike) -> NDArray[np.float64]:
    """Twenty times the decimal logarithm."""
    return np.asarray(20.0 * np.log10(ratio), dtype=np.float64)


# ---------------------------------------------------------------------------
# 8.2: impedance
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RatedImpedanceVerification(OwnsArrays):
    """A rated impedance judged against the measured modulus (IEC 60268-7 8.2).

    :ivar frequencies_hz: The measurement frequencies, in Hz, ascending.
    :ivar impedance_ohm: The modulus of the impedance at each frequency, in
        ohms.
    :ivar rated_impedance_ohm: The rated impedance, in ohms.
    :ivar rated_frequency_range_hz: The rated frequency range, (lower, upper),
        in Hz.
    """

    frequencies_hz: NDArray[np.float64]
    impedance_ohm: NDArray[np.float64]
    rated_impedance_ohm: float
    rated_frequency_range_hz: tuple[float, float]

    @property
    def limit_ohm(self) -> float:
        """80 % of the rated impedance, in ohms (8.2.1 b)."""
        return _RATED_IMPEDANCE_FRACTION * self.rated_impedance_ohm

    def _in_rated_range(self) -> NDArray[np.bool_]:
        lower, upper = self.rated_frequency_range_hz
        return (self.frequencies_hz >= lower) & (self.frequencies_hz <= upper)

    @property
    def minimum_ohm(self) -> float:
        """The lowest modulus within the rated frequency range, in ohms."""
        return float(np.min(self.impedance_ohm[self._in_rated_range()]))

    @property
    def minimum_frequency_hz(self) -> float:
        """The frequency of :attr:`minimum_ohm`, in Hz."""
        inside = self._in_rated_range()
        index = int(np.argmin(self.impedance_ohm[inside]))
        return float(self.frequencies_hz[inside][index])

    @property
    def minimum_ratio(self) -> float:
        """:attr:`minimum_ohm` over the rated impedance."""
        return self.minimum_ohm / self.rated_impedance_ohm

    @property
    def frequencies_to_state_hz(self) -> NDArray[np.float64]:
        """The frequencies from 0 kHz to 20 kHz where the modulus is below 80 %.

        8.2.1 b): "If the impedance at any frequency between 0 kHz and 20 kHz
        is less than this value, this should be stated in the specification."
        """
        below = self.impedance_ohm < self.limit_ohm * (1.0 - _LIMIT_SLACK)
        audio = self.frequencies_hz <= _IMPEDANCE_RANGE_HZ[1]
        return np.asarray(self.frequencies_hz[below & audio], dtype=np.float64)

    @property
    def covers_measurement_range(self) -> bool:
        """Whether the modulus was measured at least from 20 Hz to 20 kHz (8.2.2.2 c)."""
        lower, upper = _IMPEDANCE_RANGE_HZ
        return bool(
            self.frequencies_hz[0] <= lower * (1.0 + _LIMIT_SLACK)
            and self.frequencies_hz[-1] >= upper * (1.0 - _LIMIT_SLACK)
        )

    @property
    def passes(self) -> bool:
        """Whether the rated impedance is at most 1,25 times the lowest modulus in range."""
        return self.minimum_ratio >= _RATED_IMPEDANCE_FRACTION * (1.0 - _LIMIT_SLACK)

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a RatedImpedanceVerification has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the modulus against frequency with the rated value and its 80 %.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the impedance curve's ``Axes.plot``.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.headphones import plot_rated_impedance

        check_language(language)
        return plot_rated_impedance(self, ax, language=language, **kwargs)


def verify_rated_impedance(
    frequencies_hz: ArrayLike,
    impedance_ohm: ArrayLike,
    *,
    rated_impedance_ohm: float,
    rated_frequency_range_hz: tuple[float, float],
) -> RatedImpedanceVerification:
    """Is the rated impedance of a headphone chosen as IEC 60268-7 8.2.1 asks?

    The rated impedance passes when the lowest modulus of the measured
    impedance within the rated frequency range is at least 80 % of it. The
    result also lists the frequencies up to 20 kHz where the modulus falls
    below that value, which the specification should state, and whether the
    measurement covered 20 Hz to 20 kHz as 8.2.2.2 c) requires.

    :param frequencies_hz: Measurement frequencies, in Hz, strictly ascending.
    :param impedance_ohm: The impedance at each frequency, in ohms: the
        modulus, or the complex impedance whose modulus is taken.
    :param rated_impedance_ohm: The rated impedance, in ohms.
    :param rated_frequency_range_hz: The rated frequency range (8.6.6), as
        (lower, upper), in Hz.
    :return: A :class:`RatedImpedanceVerification`.
    :raises ValueError: If the inputs differ in length, are not positive and
        finite, or no measurement frequency falls in the rated range.
    """
    f = _frequencies(frequencies_hz)
    z = np.abs(np.atleast_1d(np.asarray(impedance_ohm, dtype=np.complex128)))
    if z.shape != f.shape:
        msg = "'frequencies_hz' and 'impedance_ohm' must have the same length."
        raise ValueError(msg)
    if not (np.all(np.isfinite(z)) and np.all(z > 0.0)):
        msg = "'impedance_ohm' must be positive and finite."
        raise ValueError(msg)
    rated = require_positive(rated_impedance_ohm, "rated_impedance_ohm")
    lower, upper = (float(value) for value in rated_frequency_range_hz)
    if not (0.0 < lower < upper and math.isfinite(upper)):
        msg = (
            "'rated_frequency_range_hz' must be (lower, upper) with 0 < lower < upper."
        )
        raise ValueError(msg)
    if not np.any((f >= lower) & (f <= upper)):
        msg = "No measurement frequency falls in the rated frequency range."
        raise ValueError(msg)
    return RatedImpedanceVerification(
        frequencies_hz=f,
        impedance_ohm=read_only(np.asarray(z, dtype=np.float64)),
        rated_impedance_ohm=rated,
        rated_frequency_range_hz=(lower, upper),
    )


# ---------------------------------------------------------------------------
# 8.3 to 8.5: voltages, powers, sound pressure levels
# ---------------------------------------------------------------------------


def characteristic_voltage(
    source_emf_v: float, sound_pressure_level_db: float
) -> float:
    r"""The source e.m.f. that produces 94 dB in the coupler (IEC 60268-7 8.3.3).

    The characteristic voltage is "the sinusoidal source e.m.f. at 500 Hz
    which, when applied to the headphone through the rated source impedance,
    produces a sound pressure level in the coupler or ear simulator of 94 dB".
    The headphone is linear at that level, so a reading of
    ``sound_pressure_level_db`` at ``source_emf_v`` scales to it:
    :math:`E\,10^{(94 - L)/20}`. The same scaling serves the programme signal
    of 8.3.4 with the level of the whole signal
    (:func:`programme_signal_level`).

    :param source_emf_v: The source e.m.f. of the reading, in volts (RMS).
    :param sound_pressure_level_db: The level it produced in the coupler or ear
        simulator, in dB re 20 µPa.
    :return: The characteristic voltage, in volts (RMS).
    :raises ValueError: If the e.m.f. is not positive or the level not finite.
    """
    emf = require_positive(source_emf_v, "source_emf_v")
    require_scalar(sound_pressure_level_db, "sound_pressure_level_db")
    level = float(sound_pressure_level_db)
    if not math.isfinite(level):
        msg = "'sound_pressure_level_db' must be finite."
        raise ValueError(msg)
    return float(emf * 10.0 ** ((_STANDARD_LEVEL_DB - level) / 20.0))


def _impedances(
    rated_impedance_ohm: float, rated_source_impedance_ohm: float
) -> tuple[float, float]:
    """The rated impedance (positive) and the rated source impedance (not negative)."""
    rated = require_positive(rated_impedance_ohm, "rated_impedance_ohm")
    require_scalar(rated_source_impedance_ohm, "rated_source_impedance_ohm")
    source = float(rated_source_impedance_ohm)
    if not (math.isfinite(source) and source >= 0.0):
        msg = "'rated_source_impedance_ohm' must be finite and not negative."
        raise ValueError(msg)
    return rated, source


def headphone_input_power(
    source_emf_v: float,
    *,
    rated_impedance_ohm: float,
    rated_source_impedance_ohm: float,
) -> float:
    r"""The power corresponding to a source e.m.f. (IEC 60268-7 8.4).

    "Specifications in terms of power can be derived from the corresponding
    voltages (8.3) and the rated impedance": the power the e.m.f.
    :math:`E` dissipates, through the rated source impedance
    :math:`R_\mathrm{s}`, in a pure resistance equal to the rated impedance
    :math:`R` connected in place of the headphone, the arrangement 8.5.2 b)
    describes for 1 mW,

    .. math::

       P = \frac{E^2 R}{(R + R_\mathrm{s})^2}.

    :param source_emf_v: The source e.m.f., in volts (RMS).
    :param rated_impedance_ohm: The rated impedance, in ohms.
    :param rated_source_impedance_ohm: The rated source impedance, in ohms
        (IEC 61938 specifies 120 ohm for a headphone output, 7.1 NOTE).
    :return: The input power, in watts.
    :raises ValueError: If an input is out of range.
    """
    emf = require_positive(source_emf_v, "source_emf_v")
    rated, source = _impedances(rated_impedance_ohm, rated_source_impedance_ohm)
    return emf * emf * rated / (rated + source) ** 2


def headphone_source_emf(
    input_power_w: float,
    *,
    rated_impedance_ohm: float,
    rated_source_impedance_ohm: float,
) -> float:
    r"""The source e.m.f. that corresponds to a power (IEC 60268-7 8.4, 8.5.2).

    The inverse of :func:`headphone_input_power`,
    :math:`E = \sqrt{P R}\,(R + R_\mathrm{s})/R`. With 1 mW it is the e.m.f.
    of the working sound pressure level of 8.5.2 b) to d).

    :param input_power_w: The power, in watts.
    :param rated_impedance_ohm: The rated impedance, in ohms.
    :param rated_source_impedance_ohm: The rated source impedance, in ohms.
    :return: The source e.m.f., in volts (RMS).
    :raises ValueError: If an input is out of range.
    """
    power = require_positive(input_power_w, "input_power_w")
    rated, source = _impedances(rated_impedance_ohm, rated_source_impedance_ohm)
    return math.sqrt(power * rated) * (rated + source) / rated


def working_sound_pressure_level(
    sound_pressure_level_db: float,
    source_emf_v: float,
    *,
    rated_impedance_ohm: float,
    rated_source_impedance_ohm: float,
    headphone_impedance_ohm: complex | None = None,
) -> float:
    r"""The working sound pressure level of IEC 60268-7 8.5.2 b) to d).

    The level produced by the e.m.f. "of such value that 1 mW would be
    dissipated in a pure resistance equal to the rated impedance of the
    headphone, connected in place of it", scaled from a reading at another
    e.m.f. With a 500 Hz sine it is 8.5.2 b); with the level of the
    simulated programme signal (:func:`programme_signal_level`) it is c), and
    d) when that level is A-weighted and free-field compensated.

    The method of 8.5.3 c) sets that e.m.f. another way: "so that the
    voltage across the input connector of the headphone is such that it
    would cause 1 mW to be dissipated in a pure resistance equal to the rated
    impedance", :math:`\sqrt{P R}` across the headphone itself, whose
    impedance :math:`Z` at 500 Hz takes its share of the e.m.f.,
    :math:`E = \sqrt{P R}\,|Z + R_\mathrm{s}|/|Z|`. The two readings agree
    when :math:`Z` is the rated impedance and part when it is not: a 32 ohm
    headphone of 40 ohm at 500 Hz on a 120 ohm source reads 1,49 dB lower by
    8.5.3 c). Pass ``headphone_impedance_ohm`` for the reading of 8.5.3 c)
    (see ``docs/ERRATA.md``); it applies to the 500 Hz sine of 8.5.2 b),
    since a noise signal has no single impedance to divide by.

    :param sound_pressure_level_db: The level read in the coupler or ear
        simulator, in dB re 20 µPa.
    :param source_emf_v: The source e.m.f. of the reading, in volts (RMS).
    :param rated_impedance_ohm: The rated impedance, in ohms.
    :param rated_source_impedance_ohm: The rated source impedance, in ohms.
    :param headphone_impedance_ohm: The headphone's measured impedance at
        500 Hz, in ohms, complex or its modulus for a resistive one, to set
        the e.m.f. by 8.5.3 c); ``None`` (default) for the definition of
        8.5.2 b) to d).
    :return: The working sound pressure level, in dB re 20 µPa.
    :raises ValueError: If an input is out of range.
    """
    emf = require_positive(source_emf_v, "source_emf_v")
    require_scalar(sound_pressure_level_db, "sound_pressure_level_db")
    level = float(sound_pressure_level_db)
    if not math.isfinite(level):
        msg = "'sound_pressure_level_db' must be finite."
        raise ValueError(msg)
    if headphone_impedance_ohm is None:
        working = headphone_source_emf(
            _WORKING_POWER_W,
            rated_impedance_ohm=rated_impedance_ohm,
            rated_source_impedance_ohm=rated_source_impedance_ohm,
        )
    else:
        rated, source = _impedances(rated_impedance_ohm, rated_source_impedance_ohm)
        impedance = complex(headphone_impedance_ohm)
        if not (cmath.isfinite(impedance) and abs(impedance) > 0.0):
            msg = "'headphone_impedance_ohm' must be finite and not zero."
            raise ValueError(msg)
        terminal = math.sqrt(_WORKING_POWER_W * rated)
        working = terminal * abs(impedance + source) / abs(impedance)
    return level + 20.0 * math.log10(working / emf)


def _band_corrections(
    frequencies: NDArray[np.float64],
    *,
    a_weighted: bool,
    free_field_response_db: ArrayLike | None,
) -> NDArray[np.float64]:
    """The per-band A-weighting minus the free-field response, in dB."""
    from ..filters.weighting_compliance import _analytic_weighting_db, _exact_base10

    corrections = np.zeros_like(frequencies)
    if a_weighted:
        corrections += _analytic_weighting_db("A", _exact_base10(frequencies))
    if free_field_response_db is not None:
        response = _levels(free_field_response_db, "free_field_response_db")
        if response.shape != frequencies.shape:
            msg = "'free_field_response_db' must have one value per band."
            raise ValueError(msg)
        corrections -= response
    return np.asarray(corrections, dtype=np.float64)


def programme_signal_level(
    frequencies_hz: ArrayLike,
    band_levels_db: ArrayLike,
    *,
    a_weighted: bool = False,
    free_field_response_db: ArrayLike | None = None,
) -> float:
    r"""The level of the simulated programme signal from its one-third-octave bands.

    IEC 60268-7:2010 Figure 3, NOTE: "The output signal correction can be
    done numerically without use of any filtering devices. Power summation of
    the 1/3-octave-analized data multiplied by filtering coefficients given by
    IEC 61672-1 and/or IEC 60969 gives the corrected voltage." The
    coefficients are the A-weighting of IEC 61672-1, taken at the exact
    base-ten centre of each band (where its Table 3 is computed), and the
    inverse of the free-field response of the head and torso simulator of IEC
    60959 (printed "IEC 60969", see ``docs/ERRATA.md``):

    .. math::

       L = 10\lg \sum_k 10^{(L_k + A_k - F_k)/10}.

    :param frequencies_hz: The band centre frequencies, in Hz, ascending.
    :param band_levels_db: The band levels read in the coupler or ear
        simulator, in dB re 20 µPa.
    :param a_weighted: Apply the A-weighting (8.3.5, 8.5.2 d).
    :param free_field_response_db: The free-field response of the head and
        torso simulator at 0° azimuth in each band, in dB, whose inverse
        compensates the output; ``None`` for no compensation.
    :return: The level of the whole signal, in dB re 20 µPa.
    :raises ValueError: If the inputs differ in length or are not finite.
    """
    f = _frequencies(frequencies_hz)
    levels = _levels(band_levels_db, "band_levels_db")
    if levels.shape != f.shape:
        msg = "'frequencies_hz' and 'band_levels_db' must have the same length."
        raise ValueError(msg)
    corrections = _band_corrections(
        f, a_weighted=a_weighted, free_field_response_db=free_field_response_db
    )
    return float(10.0 * np.log10(np.sum(10.0 ** ((levels + corrections) / 10.0))))


@dataclass(frozen=True)
class ProgrammeCharacteristicVoltage(OwnsArrays):
    """The simulated programme signal characteristic voltage (IEC 60268-7 8.3.4, 8.3.5).

    :ivar frequencies_hz: The band centre frequencies, in Hz.
    :ivar band_levels_db: The band levels read in the coupler or ear
        simulator, one row per fitting, in dB re 20 µPa.
    :ivar source_emf_v: The source e.m.f. of each fitting's reading, in volts
        (RMS).
    :ivar corrections_db: The correction added to each band, in dB: the
        A-weighting minus the free-field response, zero when neither applies.
    :ivar a_weighted: Whether the A-weighting was applied.
    :ivar free_field_compensated: Whether the free-field response was
        compensated.
    """

    frequencies_hz: NDArray[np.float64]
    band_levels_db: NDArray[np.float64]
    source_emf_v: NDArray[np.float64]
    corrections_db: NDArray[np.float64]
    a_weighted: bool
    free_field_compensated: bool

    @property
    def levels_db(self) -> NDArray[np.float64]:
        """The corrected level of the whole signal in each fitting, in dB re 20 µPa."""
        corrected = self.band_levels_db + self.corrections_db
        return np.asarray(
            10.0 * np.log10(np.sum(10.0 ** (corrected / 10.0), axis=1)),
            dtype=np.float64,
        )

    @property
    def voltages_v(self) -> NDArray[np.float64]:
        """The e.m.f. that gives 94 dB in each fitting, in volts (RMS)."""
        return np.asarray(
            self.source_emf_v * 10.0 ** ((_STANDARD_LEVEL_DB - self.levels_db) / 20.0),
            dtype=np.float64,
        )

    @property
    def characteristic_voltage_v(self) -> float:
        """The arithmetic mean of :attr:`voltages_v`, in volts: 8.3.5 g)."""
        return float(np.mean(self.voltages_v))

    @property
    def fittings_conform(self) -> bool:
        """Whether 3 to 5 fittings were averaged, as 8.3.5 g) asks."""
        lowest, highest = _FITTINGS_RANGE
        return lowest <= self.voltages_v.size <= highest

    @property
    def band_levels_at_characteristic_db(self) -> NDArray[np.float64]:
        """The corrected band levels at the characteristic voltage, in dB re 20 µPa.

        The mean of the fittings' corrected bands, each scaled to the
        characteristic voltage; their power sum is 94 dB when the fittings
        agree.
        """
        corrected = self.band_levels_db + self.corrections_db
        scale = _db20(self.characteristic_voltage_v / self.source_emf_v)
        scaled = corrected + scale[:, None]
        return np.asarray(
            10.0 * np.log10(np.mean(10.0 ** (scaled / 10.0), axis=0)),
            dtype=np.float64,
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the band levels at the characteristic voltage and their 94 dB sum.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the bars' ``Axes.bar``.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.headphones import plot_programme_characteristic_voltage

        check_language(language)
        return plot_programme_characteristic_voltage(
            self, ax, language=language, **kwargs
        )


def programme_characteristic_voltage(
    source_emf_v: ArrayLike,
    frequencies_hz: ArrayLike,
    band_levels_db: ArrayLike,
    *,
    a_weighted: bool = False,
    free_field_response_db: ArrayLike | None = None,
) -> ProgrammeCharacteristicVoltage:
    """The simulated programme signal characteristic voltage of IEC 60268-7.

    The source e.m.f. of the simulated programme signal of IEC 60268-1 that
    produces 94 dB in the coupler or ear simulator (8.3.4), or 94 dB after the
    A-weighting and the free-field compensation of 8.3.5. Each fitting's
    one-third-octave band levels, read at a known e.m.f., are power-summed as
    the NOTE under Figure 3 describes (:func:`programme_signal_level`) and
    scaled to 94 dB; 8.3.5 g) removes and refits the headphone between
    readings and states "the average value of source e.m.f. of 3 to 5
    measurements".

    :param source_emf_v: The source e.m.f. of each fitting's reading, in volts
        (RMS): one value for all, or one per fitting.
    :param frequencies_hz: The band centre frequencies, in Hz, ascending.
    :param band_levels_db: The band levels, in dB re 20 µPa, shape
        ``(bands,)`` for one fitting or ``(fittings, bands)``.
    :param a_weighted: Apply the A-weighting (8.3.5).
    :param free_field_response_db: The free-field response of the head and
        torso simulator in each band, in dB, compensated by its inverse
        (8.3.5); ``None`` for none.
    :return: A :class:`ProgrammeCharacteristicVoltage`.
    :raises ValueError: If the shapes disagree or a value is out of range.
    """
    f = _frequencies(frequencies_hz)
    levels = np.atleast_2d(_levels(band_levels_db, "band_levels_db"))
    if levels.ndim != _MATRIX_NDIM or levels.shape[1] != f.size:
        msg = "'band_levels_db' must be (bands,) or (fittings, bands) over 'frequencies_hz'."
        raise ValueError(msg)
    emf = np.broadcast_to(
        np.atleast_1d(np.asarray(source_emf_v, dtype=np.float64)), (levels.shape[0],)
    )
    if not (np.all(np.isfinite(emf)) and np.all(emf > 0.0)):
        msg = "'source_emf_v' must be positive and finite."
        raise ValueError(msg)
    corrections = _band_corrections(
        f, a_weighted=a_weighted, free_field_response_db=free_field_response_db
    )
    return ProgrammeCharacteristicVoltage(
        frequencies_hz=f,
        band_levels_db=levels,
        source_emf_v=emf,
        corrections_db=read_only(corrections),
        a_weighted=bool(a_weighted),
        free_field_compensated=free_field_response_db is not None,
    )


# ---------------------------------------------------------------------------
# 8.3.2: the clipped programme signal of the limiting voltages
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LimitingTestSignalCheck:
    """The test signal of the limiting voltages judged by IEC 60268-7 8.3.2.2 b).

    :ivar peak_to_rms: The ratio of the record's peak value to its RMS value.
    :ivar spectrum: Its one-third-octave spectrum judged against IEC 60268-1
        Table II.
    """

    peak_to_rms: float
    spectrum: ProgrammeSignalCheck

    @property
    def peak_to_rms_passes(self) -> bool:
        """Whether the peak-to-RMS ratio is between 1,8 and 2,2."""
        lower, upper = _LIMITING_PEAK_TO_RMS
        return (
            lower * (1.0 - _LIMIT_SLACK)
            <= self.peak_to_rms
            <= upper * (1.0 + _LIMIT_SLACK)
        )

    @property
    def passes(self) -> bool:
        """Whether both the ratio and the spectrum conform."""
        return self.peak_to_rms_passes and self.spectrum.passes

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a LimitingTestSignalCheck has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the spectrum against Table II, with the ratio in the title.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the band levels' ``Axes.plot``.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.headphones import plot_limiting_test_signal_check

        check_language(language)
        return plot_limiting_test_signal_check(self, ax, language=language, **kwargs)


def check_limiting_test_signal(
    signal: Signal | NDArray[np.float64] | list[float], fs: int | None = None
) -> LimitingTestSignalCheck:
    """Is this the clipped programme signal IEC 60268-7 8.3.2.2 b) asks for?

    "The clipped noise signal at the output of the amplifier shall have a
    frequency distribution as specified in IEC 60268-1, and a peak-to-r.m.s
    ratio between 1,8 and 2,2." The record's one-third-octave bands from
    20 Hz up to the highest whose upper edge lies below the Nyquist frequency
    are judged against Table II of IEC 60268-1
    (:func:`~phonometry.electroacoustics.check_programme_signal`), and its
    peak over its RMS against the two limits.
    :func:`~phonometry.electroacoustics.simulated_programme_signal` with
    ``peak_to_rms`` generates such a record.

    :param signal: The record (1-D), or a :class:`phonometry.io.Signal`.
    :param fs: Sample rate, in Hz; required for a bare array.
    :return: A :class:`LimitingTestSignalCheck`.
    :raises ValueError: If the record is not 1-D and finite, or too short.
    """
    from ..filters.core import octave_filter
    from ..io._resolve import resolve_fs

    rate = resolve_fs(signal, fs, name="signal")
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim != 1 or x.size < _FEWEST_POINTS:
        msg = "'signal' must be a 1-D record of at least two samples."
        raise ValueError(msg)
    if not np.all(np.isfinite(x)):
        msg = "'signal' must be finite."
        raise ValueError(msg)
    # The ratio is read on the record as given, the voltage at the amplifier's
    # output; the band analysis removes any offset on its own.
    rms = float(np.sqrt(np.mean(x * x)))
    if rms <= 0.0:
        msg = "'signal' is constant; it has no RMS value to judge."
        raise ValueError(msg)
    peak_to_rms = float(np.max(np.abs(x))) / rms
    nyquist = 0.5 * float(rate)
    bands = [
        centre for centre in _TABLE_II_EXACT if centre * _THIRD_OCTAVE_EDGE < nyquist
    ]
    if len(bands) < _FEWEST_POINTS:
        msg = "The sample rate leaves fewer than two bands of Table II below the Nyquist frequency."
        raise ValueError(msg)
    # The bank adds bands from the one holding the lower limit until a band's
    # upper edge passes the upper limit, so the two centres select exactly
    # the bands wanted.
    analysis = octave_filter(x, int(rate), fraction=3, limits=[bands[0], bands[-1]])
    if analysis.levels is None:  # pragma: no cover - the bank always returns levels
        msg = "The one-third-octave analysis returned no band levels."
        raise RuntimeError(msg)
    spectrum = check_programme_signal(analysis.frequencies, analysis.levels)
    return LimitingTestSignalCheck(peak_to_rms=peak_to_rms, spectrum=spectrum)


# ---------------------------------------------------------------------------
# 8.3.6: protective devices
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProtectionVoltage(OwnsArrays):
    """A protective device's operating point from a level sweep (IEC 60268-7 8.3.6).

    :ivar source_emf_v: The source e.m.f. of each step, in volts (RMS),
        ascending.
    :ivar sound_pressure_level_db: The level at each step, in dB re 20 µPa.
    :ivar protection_voltage_v: The e.m.f. at which the sensitivity has
        changed by 1 dB from the first step, interpolated, in volts; ``None``
        when the sweep never reaches that change.
    """

    source_emf_v: NDArray[np.float64]
    sound_pressure_level_db: NDArray[np.float64]
    protection_voltage_v: float | None

    @property
    def sensitivity_change_db(self) -> NDArray[np.float64]:
        """The sensitivity at each step relative to the first, in dB."""
        sensitivity = self.sound_pressure_level_db - _db20(self.source_emf_v)
        return np.asarray(sensitivity - sensitivity[0], dtype=np.float64)

    @property
    def measurement_voltages_v(self) -> tuple[float, float] | None:
        """The e.m.f.s 1 dB below and 1 dB above the protection voltage, in volts.

        8.3.6.2 b): "measurements are then made of the impedance and sound
        pressure level at voltages 1 dB lower and 1 dB higher than the noted
        voltage".
        """
        if self.protection_voltage_v is None:
            return None
        step = 10.0 ** (_PROTECTION_STEP_DB / 20.0)
        return (self.protection_voltage_v / step, self.protection_voltage_v * step)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the sensitivity change against the e.m.f., with the 1 dB line.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the sensitivity curve's ``Axes.plot``.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.headphones import plot_protection_voltage

        check_language(language)
        return plot_protection_voltage(self, ax, language=language, **kwargs)


def protection_voltage(
    source_emf_v: ArrayLike, sound_pressure_level_db: ArrayLike
) -> ProtectionVoltage:
    r"""The protection voltage of a headphone's protective device (IEC 60268-7 8.3.6).

    8.3.6.2 b): "The source e.m.f., at the standard reference frequency, is
    increased until operation of the protective device causes a change of at
    least 1 dB in the sensitivity of the headphone." The sensitivity at each
    step is :math:`L - 20\lg E`; the first step, the lowest e.m.f., is taken
    as the linear one, and the protection voltage is where the change from it
    first reaches 1 dB either way, interpolated linearly in :math:`20\lg E`
    between the two steps that straddle it.

    :param source_emf_v: The source e.m.f. of each step, in volts (RMS),
        strictly ascending.
    :param sound_pressure_level_db: The level at each step, in dB re 20 µPa.
    :return: A :class:`ProtectionVoltage`.
    :raises ValueError: If the inputs differ in length, are not finite, the
        e.m.f.s are not positive and ascending, or there are fewer than two.
    """
    emf = _frequencies(source_emf_v, "source_emf_v")
    if emf.size < _FEWEST_POINTS:
        msg = "At least two steps are needed to see a change of sensitivity."
        raise ValueError(msg)
    levels = _levels(sound_pressure_level_db, "sound_pressure_level_db")
    if levels.shape != emf.shape:
        msg = "'source_emf_v' and 'sound_pressure_level_db' must have the same length."
        raise ValueError(msg)
    change = np.abs(levels - _db20(emf) - (levels[0] - _db20(emf[0])))
    reached = np.flatnonzero(change >= _PROTECTION_STEP_DB * (1.0 - _LIMIT_SLACK))
    voltage: float | None = None
    if reached.size:
        k = int(reached[0])
        x0, x1 = float(_db20(emf[k - 1])), float(_db20(emf[k]))
        c0, c1 = float(change[k - 1]), float(change[k])
        fraction = (_PROTECTION_STEP_DB - c0) / (c1 - c0) if c1 > c0 else 1.0
        voltage = 10.0 ** ((x0 + min(max(fraction, 0.0), 1.0) * (x1 - x0)) / 20.0)
    return ProtectionVoltage(
        source_emf_v=emf,
        sound_pressure_level_db=levels,
        protection_voltage_v=voltage,
    )


# ---------------------------------------------------------------------------
# 8.6.2 and 8.12: coupler frequency response and crosstalk
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CouplerFrequencyResponse(OwnsArrays):
    """The coupler or ear simulator frequency response (IEC 60268-7 8.6.2).

    :ivar frequencies_hz: The frequencies, in Hz, ascending.
    :ivar sound_pressure_level_db: The level in the coupler or ear simulator at
        each frequency, in dB re 20 µPa.
    :ivar rated_frequency_range_hz: The rated frequency range, (lower, upper),
        in Hz, or ``None`` when not stated.
    """

    frequencies_hz: NDArray[np.float64]
    sound_pressure_level_db: NDArray[np.float64]
    rated_frequency_range_hz: tuple[float, float] | None

    @property
    def covers_rated_range(self) -> bool | None:
        """Whether the frequencies span the rated range (8.6.2.2 b), ``None`` if unstated."""
        if self.rated_frequency_range_hz is None:
            return None
        lower, upper = self.rated_frequency_range_hz
        return bool(
            self.frequencies_hz[0] <= lower * (1.0 + _LIMIT_SLACK)
            and self.frequencies_hz[-1] >= upper * (1.0 - _LIMIT_SLACK)
        )

    def relative_response_db(
        self, *, reference_frequency_hz: float = _MEASURING_FREQUENCY_HZ
    ) -> NDArray[np.float64]:
        """The level relative to its value at a reference frequency, in dB.

        :param reference_frequency_hz: The reference frequency, in Hz; one of
            the measured frequencies (500 Hz by default, the standard
            measuring frequency of 7.2 b), chosen in the coupler "to avoid the
            effects of diaphragm resonance, leakage and standing waves",
            8.3.3.1 NOTE).
        :return: The relative response at each frequency, in dB.
        :raises ValueError: If the reference frequency was not measured.
        """
        index = _band_index(self.frequencies_hz, float(reference_frequency_hz))
        return np.asarray(
            self.sound_pressure_level_db - self.sound_pressure_level_db[index],
            dtype=np.float64,
        )

    def plot(
        self,
        ax: Axes | None = None,
        *,
        language: str = "en",
        iec_scale: bool = True,
        **kwargs: Any,
    ) -> Axes:
        """Draw the level against frequency, 50 dB to the length of a decade.

        8.6.2.2 c): "the preferred scale has the same length representing
        50 dB as represents one decade of frequency (see IEC 60268-1 and
        IEC 60263)". Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param iec_scale: Fix that aspect (default); ``False`` lets the axes
            fill their box.
        :param kwargs: Forwarded to the response curve's ``Axes.plot``.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.headphones import plot_coupler_frequency_response

        check_language(language)
        return plot_coupler_frequency_response(
            self, ax, language=language, iec_scale=iec_scale, **kwargs
        )


def coupler_frequency_response(
    frequencies_hz: ArrayLike,
    sound_pressure_level_db: ArrayLike,
    *,
    rated_frequency_range_hz: tuple[float, float] | None = None,
) -> CouplerFrequencyResponse:
    """The coupler or ear simulator frequency response of IEC 60268-7 8.6.2.

    "The variation of the sound pressure (level) in the coupler or ear
    simulator as a function of frequency", at the rated source e.m.f. through
    the rated source impedance, over "at least the rated frequency range".

    :param frequencies_hz: Frequencies, in Hz, strictly ascending.
    :param sound_pressure_level_db: The level at each, in dB re 20 µPa.
    :param rated_frequency_range_hz: The rated frequency range (8.6.6), as
        (lower, upper), in Hz, to judge the coverage; ``None`` if not stated.
    :return: A :class:`CouplerFrequencyResponse`.
    :raises ValueError: If the inputs differ in length or are not finite.
    """
    f = _frequencies(frequencies_hz)
    levels = _levels(sound_pressure_level_db, "sound_pressure_level_db")
    if levels.shape != f.shape:
        msg = (
            "'frequencies_hz' and 'sound_pressure_level_db' must have the same length."
        )
        raise ValueError(msg)
    rated: tuple[float, float] | None = None
    if rated_frequency_range_hz is not None:
        lower, upper = (float(value) for value in rated_frequency_range_hz)
        if not (0.0 < lower < upper and math.isfinite(upper)):
            msg = "'rated_frequency_range_hz' must be (lower, upper) with 0 < lower < upper."
            raise ValueError(msg)
        rated = (lower, upper)
    return CouplerFrequencyResponse(
        frequencies_hz=f,
        sound_pressure_level_db=levels,
        rated_frequency_range_hz=rated,
    )


@dataclass(frozen=True)
class CrosstalkAttenuation(OwnsArrays):
    """The crosstalk attenuation of a multi-channel headphone (IEC 60268-7 8.12).

    :ivar frequencies_hz: The frequencies, in Hz, ascending.
    :ivar driven_level_db: The level in the coupler of the channel under test
        with the rated e.m.f. on that channel, in dB re 20 µPa.
    :ivar other_level_db: The level in the same coupler with the rated e.m.f.
        on the other, stated channel, in dB re 20 µPa.
    """

    frequencies_hz: NDArray[np.float64]
    driven_level_db: NDArray[np.float64]
    other_level_db: NDArray[np.float64]

    @property
    def attenuation_db(self) -> NDArray[np.float64]:
        """The difference of the two levels at each frequency, in dB."""
        return np.asarray(self.driven_level_db - self.other_level_db, dtype=np.float64)

    @property
    def minimum_db(self) -> float:
        """The smallest attenuation over the frequencies, in dB."""
        return float(np.min(self.attenuation_db))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the attenuation against frequency.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the attenuation curve's ``Axes.plot``.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.headphones import plot_crosstalk_attenuation

        check_language(language)
        return plot_crosstalk_attenuation(self, ax, language=language, **kwargs)


def crosstalk_attenuation(
    frequencies_hz: ArrayLike, driven_level_db: ArrayLike, other_level_db: ArrayLike
) -> CrosstalkAttenuation:
    """The crosstalk attenuation of IEC 60268-7 8.12.

    "The ratio of the sound pressure produced in the coupler or ear simulator
    due to rated source e.m.f. applied to the channel under test to the sound
    pressure produced by rated source e.m.f. applied to another, stated
    channel", expressed as the difference of the two levels against frequency.

    :param frequencies_hz: Frequencies, in Hz, strictly ascending.
    :param driven_level_db: The level with the channel under test driven, in
        dB re 20 µPa.
    :param other_level_db: The level with the other channel driven, in dB re
        20 µPa.
    :return: A :class:`CrosstalkAttenuation`.
    :raises ValueError: If the inputs differ in length or are not finite.
    """
    f = _frequencies(frequencies_hz)
    driven = _levels(driven_level_db, "driven_level_db")
    other = _levels(other_level_db, "other_level_db")
    if driven.shape != f.shape or other.shape != f.shape:
        msg = "The levels must have one value per frequency."
        raise ValueError(msg)
    return CrosstalkAttenuation(
        frequencies_hz=f,
        driven_level_db=driven,
        other_level_db=other,
    )


# ---------------------------------------------------------------------------
# 8.6.3 to 8.6.5: the responses measured with test persons
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FieldComparisonResponse(OwnsArrays):
    """A free-field or diffuse-field comparison frequency response (IEC 60268-7 8.6.3, 8.6.4).

    :ivar field: ``"free"`` (8.6.3) or ``"diffuse"`` (8.6.4).
    :ivar frequencies_hz: The one-third-octave band centres, in Hz.
    :ivar response_db: Each test person's response, one row per person, in dB
        relative to the reference band.
    :ivar reference_frequency_hz: The band the response is referred to, in Hz.
    """

    field: Literal["free", "diffuse"]
    frequencies_hz: NDArray[np.float64]
    response_db: NDArray[np.float64]
    reference_frequency_hz: float

    @property
    def persons(self) -> int:
        """The number of test persons."""
        return int(self.response_db.shape[0])

    @property
    def mean_db(self) -> NDArray[np.float64]:
        """The response averaged over the persons in each band, in dB."""
        return np.asarray(np.mean(self.response_db, axis=0), dtype=np.float64)

    @property
    def standard_deviation_db(self) -> NDArray[np.float64]:
        """The standard deviation of the persons' responses in each band, in dB.

        The sample standard deviation; zero with a single person.
        """
        if self.persons < _FEWEST_POINTS:
            return np.zeros(self.frequencies_hz.size)
        return np.asarray(np.std(self.response_db, axis=0, ddof=1), dtype=np.float64)

    @property
    def meets_panel_size(self) -> bool:
        """Whether at least eight persons were heard (8.6.3.2 d, 8.6.4.2 d)."""
        return self.persons >= _MIN_PERSONS

    @property
    def qualifies_as_reference(self) -> bool:
        """Whether the panel is large enough for a substitution reference (16 persons).

        8.6.3.3 and 8.6.4.3: a headphone measured "using a panel of at least
        16 persons, may be used as a loudness comparison reference".
        """
        return self.persons >= _MIN_REFERENCE_PERSONS

    def plot(
        self,
        ax: Axes | None = None,
        *,
        language: str = "en",
        iec_scale: bool = True,
        **kwargs: Any,
    ) -> Axes:
        """Draw the mean response as bars with the standard deviation of each band.

        8.6.3.2 e): "the resulting bar graph is presented as the free-field
        comparison frequency response of the headphone. The standard
        deviation of the results in each band should be indicated on the
        graph. The scales for the graph preferably shall be such that 50 dB
        is represented by the same length as one decade of frequency."
        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param iec_scale: Draw 50 dB the length of a decade of the bands
            (default); ``False`` lets the axes fill their box.
        :param kwargs: Forwarded to the bars' ``Axes.bar``.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.headphones import plot_field_comparison_response

        check_language(language)
        return plot_field_comparison_response(
            self, ax, language=language, iec_scale=iec_scale, **kwargs
        )


def field_comparison_response(
    frequencies_hz: ArrayLike,
    field_level_db: ArrayLike,
    source_emf_v: ArrayLike,
    *,
    field: Literal["free", "diffuse"],
    reference_frequency_hz: float = _STANDARD_REFERENCE_FREQUENCY_HZ,
) -> FieldComparisonResponse:
    r"""The free-field or diffuse-field comparison response of IEC 60268-7.

    "The quotient, as a function of frequency, of the sound pressure of the
    reference [free or diffuse] sound field by the source e.m.f. to the
    headphone which is required to produce a sound subjectively equal in
    loudness to the [...] sound field. It is normally expressed in decibels
    referred to the value at the standard reference frequency" (8.6.3.1,
    8.6.4.1). In each band :math:`k` and for each person,

    .. math::

       R_k = L_{\mathrm{field},k} - 20\lg E_k
             - (L_{\mathrm{field},\mathrm{ref}} - 20\lg E_\mathrm{ref}),

    and the persons' responses are averaged in each band, with their standard
    deviation (8.6.3.2 e). At least eight persons are heard (d); a headphone
    calibrated on at least 16 may serve as the reference of the substitution
    method (8.6.3.3).

    :param frequencies_hz: The one-third-octave band centres, in Hz,
        ascending, including the reference band.
    :param field_level_db: The level of the reference field at the reference
        point, without the person, in dB re 20 µPa: one value per band, or one
        row per person.
    :param source_emf_v: The e.m.f. that made the headphone equally loud, in
        volts (RMS), one row per person, one value per band.
    :param field: ``"free"`` (8.6.3) or ``"diffuse"`` (8.6.4).
    :param reference_frequency_hz: The band the response is referred to, in
        Hz: by default 1 000 Hz, the standard reference frequency of IEC
        60268-1:1985 Clause 3, which IEC 60268-7 names without defining and
        on whose band 8.6.3.2 c) and 8.6.4.2 c) begin and end the test
        sequence. Pass 500 Hz to refer the response to the band of the
        ear-canal response of Formula (1).
    :return: A :class:`FieldComparisonResponse`.
    :raises ValueError: If the shapes disagree, a value is out of range or
        the reference band is missing.
    """
    if field not in {"free", "diffuse"}:
        msg = "'field' must be 'free' or 'diffuse'."
        raise ValueError(msg)
    f = _frequencies(frequencies_hz)
    emf = np.atleast_2d(np.asarray(source_emf_v, dtype=np.float64))
    if emf.ndim != _MATRIX_NDIM or emf.shape[1] != f.size:
        msg = "'source_emf_v' must be (persons, bands) over 'frequencies_hz'."
        raise ValueError(msg)
    if not (np.all(np.isfinite(emf)) and np.all(emf > 0.0)):
        msg = "'source_emf_v' must be positive and finite."
        raise ValueError(msg)
    levels = _levels(field_level_db, "field_level_db")
    try:
        levels = np.broadcast_to(levels, emf.shape)
    except ValueError:
        msg = "'field_level_db' must be one value per band or one row per person."
        raise ValueError(msg) from None
    reference = _band_index(f, float(reference_frequency_hz))
    quotient = levels - _db20(emf)
    response = quotient - quotient[:, reference : reference + 1]
    return FieldComparisonResponse(
        field=field,
        frequencies_hz=f,
        response_db=read_only(np.asarray(response, dtype=np.float64)),
        reference_frequency_hz=float(f[reference]),
    )


@dataclass(frozen=True)
class EarCanalFrequencyResponse(OwnsArrays):
    """The ear canal sound pressure level frequency response (IEC 60268-7 8.6.5).

    :ivar frequencies_hz: The one-third-octave band centres, in Hz.
    :ivar earphone_levels_db: The probe microphone's band levels with the
        headphone, items c) and d), shape (persons, 2, bands), in dB.
    :ivar sound_field_levels_db: The probe microphone's band levels in the
        sound field, items b) and e), shape (persons, 2, bands), in dB.
    :ivar reference_frequency_hz: The band of Formula (1), in Hz.
    """

    frequencies_hz: NDArray[np.float64]
    earphone_levels_db: NDArray[np.float64]
    sound_field_levels_db: NDArray[np.float64]
    reference_frequency_hz: float

    def _reference(self) -> int:
        return _band_index(self.frequencies_hz, self.reference_frequency_hz)

    @property
    def persons(self) -> int:
        """The number of test persons."""
        return int(self.earphone_levels_db.shape[0])

    @property
    def response_db(self) -> NDArray[np.float64]:
        """Formula (1) for each person, one row per person, in dB."""
        earphone = np.mean(self.earphone_levels_db, axis=1)
        field = np.mean(self.sound_field_levels_db, axis=1)
        difference = earphone - field
        reference = self._reference()
        return np.asarray(
            difference - difference[:, reference : reference + 1], dtype=np.float64
        )

    @property
    def mean_db(self) -> NDArray[np.float64]:
        """Formula (1) averaged arithmetically over the persons, in dB (8.6.5.2 h)."""
        return np.asarray(np.mean(self.response_db, axis=0), dtype=np.float64)

    @property
    def standard_deviation_db(self) -> NDArray[np.float64]:
        """The standard deviation of the persons' responses, in dB (NOTE 5)."""
        if self.persons < _FEWEST_POINTS:
            return np.zeros(self.frequencies_hz.size)
        return np.asarray(np.std(self.response_db, axis=0, ddof=1), dtype=np.float64)

    @property
    def fitting_difference_db(self) -> NDArray[np.float64]:
        """The largest difference between the two fittings of each person, in dB."""
        first, second = self.earphone_levels_db[:, 0], self.earphone_levels_db[:, 1]
        return np.asarray(np.max(np.abs(first - second), axis=1), dtype=np.float64)

    @property
    def fittings_consistent(self) -> NDArray[np.bool_]:
        """For each person, whether the fittings agree within 2,5 dB in every band.

        8.6.5.2 f): "if there is a difference exceeding 2,5 dB [...] in any 1/3
        octave band, the whole procedure is repeated."
        """
        return np.asarray(
            self.fitting_difference_db
            <= _MAX_FITTING_DIFFERENCE_DB * (1.0 + _LIMIT_SLACK)
        )

    @property
    def level_match_db(self) -> NDArray[np.float64]:
        """The first fitting's level in the reference band minus the sound field's, in dB.

        8.6.5.2 c): the level is adjusted "using the 1/3 octave band of noise
        centred on 500 Hz, so that the filtered microphone output signal level
        is within 3 dB of that due to the sound field in the same frequency
        band".
        """
        reference = self._reference()
        return np.asarray(
            self.earphone_levels_db[:, 0, reference]
            - self.sound_field_levels_db[:, 0, reference],
            dtype=np.float64,
        )

    @property
    def levels_matched(self) -> NDArray[np.bool_]:
        """For each person, whether :attr:`level_match_db` is within 3 dB."""
        return np.asarray(
            np.abs(self.level_match_db) <= _LEVEL_MATCH_DB * (1.0 + _LIMIT_SLACK)
        )

    @property
    def meets_panel_size(self) -> bool:
        """Whether at least eight persons were measured (8.6.5.2 h)."""
        return self.persons >= _MIN_PERSONS

    @property
    def qualifies_as_reference(self) -> bool:
        """Whether the panel is large enough to calibrate a reference (16 persons).

        8.6.5.3: the indirect method replaces the sound field by "a
        headphone, previously calibrated by the method of 8.6.4.2, using at
        least 16 test persons"; the method meant is the direct ear-canal
        measurement of 8.6.5.2 (see ``docs/ERRATA.md``).
        """
        return self.persons >= _MIN_REFERENCE_PERSONS

    def plot(
        self,
        ax: Axes | None = None,
        *,
        language: str = "en",
        iec_scale: bool = True,
        **kwargs: Any,
    ) -> Axes:
        """Draw the persons' responses, their mean and its standard deviation.

        8.6.5.2 h): the results "may be tabulated or presented graphically,
        the scales being preferably chosen so that 50 dB and one decade of
        frequency are represented by the same length". Requires matplotlib
        (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param iec_scale: Draw 50 dB the length of a decade (default);
            ``False`` lets the axes fill their box.
        :param kwargs: Forwarded to the mean response's ``Axes.plot``.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.headphones import plot_ear_canal_frequency_response

        check_language(language)
        return plot_ear_canal_frequency_response(
            self, ax, language=language, iec_scale=iec_scale, **kwargs
        )


def ear_canal_frequency_response(
    frequencies_hz: ArrayLike,
    earphone_levels_db: ArrayLike,
    sound_field_levels_db: ArrayLike,
    *,
    reference_frequency_hz: float = _MEASURING_FREQUENCY_HZ,
) -> EarCanalFrequencyResponse:
    r"""The ear canal sound pressure level frequency response of IEC 60268-7 8.6.5.

    For each test person a probe microphone in the ear canal reads each
    one-third-octave band of pink noise twice in the sound field (items b and
    e) and twice with the headphone, refitted between the two (c and d). The
    two pairs are averaged and the response is Formula (1),
    :math:`L_\mathrm{f} = L_\mathrm{e} - L_\mathrm{s} - (L_\mathrm{e} -
    L_\mathrm{s})_{500}`, averaged over at least eight persons (h). The
    result also carries the two checks of the procedure: the fittings within
    2,5 dB in every band (f), and the 500 Hz band of the first fitting within
    3 dB of the sound field's (c).

    :param frequencies_hz: The band centres, in Hz, ascending, including the
        reference band.
    :param earphone_levels_db: The levels with the headphone, in dB, shape
        (persons, 2, bands), or (2, bands) for one person.
    :param sound_field_levels_db: The levels in the sound field, in dB, the
        same shape.
    :param reference_frequency_hz: The reference band of Formula (1), in Hz
        (500 Hz, as the formula prints it).
    :return: An :class:`EarCanalFrequencyResponse`.
    :raises ValueError: If the shapes disagree, a level is not finite or the
        reference band is missing.
    """
    f = _frequencies(frequencies_hz)
    shaped = []
    for name, values in (
        ("earphone_levels_db", earphone_levels_db),
        ("sound_field_levels_db", sound_field_levels_db),
    ):
        levels = _levels(values, name)
        if levels.ndim == _MATRIX_NDIM:
            levels = levels[None, :, :]
        if levels.ndim != _PANEL_NDIM or levels.shape[1:] != (_READINGS, f.size):
            msg = f"'{name}' must be (persons, 2, bands) over 'frequencies_hz'."
            raise ValueError(msg)
        shaped.append(levels)
    earphone, field = shaped
    if earphone.shape != field.shape:
        msg = (
            "'earphone_levels_db' and 'sound_field_levels_db' must have the same shape."
        )
        raise ValueError(msg)
    reference = _band_index(f, float(reference_frequency_hz))
    return EarCanalFrequencyResponse(
        frequencies_hz=f,
        earphone_levels_db=earphone,
        sound_field_levels_db=field,
        reference_frequency_hz=float(f[reference]),
    )


# ---------------------------------------------------------------------------
# Annex B: the microphone in the ear canal
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EarCanalMicrophoneVerification:
    """A probe microphone judged by IEC 60268-7:2010 Annex B a) to e).

    :ivar entrance_area_mm2: The microphone's cross-sectional area within the
        concha and the first 4 mm of the ear canal, in mm² (a).
    :ivar canal_section_area_mm2: Its cross-sectional area in the rest of the
        ear canal, in mm² (b).
    :ivar ear_canal_area_mm2: The cross-sectional area of the ear canal, in
        mm² (b; 45 mm² for an average adult).
    :ivar volume_mm3: The microphone's volume with its mounting parts, in mm³
        (c).
    :ivar neighbour_difference_db: The largest difference between the
        responses to neighbouring one-third-octave bands of pink noise, in dB
        (d).
    :ivar sealed_attenuation_db: The smallest drop of the output level when
        the sound entrance is sealed, over the measuring frequencies, in dB (e).
    """

    entrance_area_mm2: float
    canal_section_area_mm2: float
    ear_canal_area_mm2: float
    volume_mm3: float
    neighbour_difference_db: float
    sealed_attenuation_db: float

    @property
    def area_ratio(self) -> float:
        """The microphone's area over the ear canal's, in the rest of the canal."""
        return self.canal_section_area_mm2 / self.ear_canal_area_mm2

    @property
    def requirements(self) -> Mapping[str, bool]:
        """Each of a) to e), keyed by its item letter, and whether it holds."""
        return MappingProxyType(
            {
                "a": self.entrance_area_mm2
                <= _MAX_ENTRANCE_AREA_MM2 * (1.0 + _LIMIT_SLACK),
                # A ratio of two decimal areas that is 0,6 in decimal comes
                # out either side of it in binary; settled, it is 0,6.
                "b": float(settled(self.area_ratio)) < _MAX_CANAL_AREA_RATIO,
                "c": self.volume_mm3 < _MAX_VOLUME_MM3,
                "d": self.neighbour_difference_db
                <= _MAX_NEIGHBOUR_DIFFERENCE_DB * (1.0 + _LIMIT_SLACK),
                "e": self.sealed_attenuation_db
                >= _MIN_SEALED_ATTENUATION_DB * (1.0 - _LIMIT_SLACK),
            }
        )

    @property
    def passes(self) -> bool:
        """Whether all five requirements hold."""
        return all(self.requirements.values())

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "an EarCanalMicrophoneVerification has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw each requirement's value as a share of its limit.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the bars' ``Axes.bar``.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.headphones import plot_ear_canal_microphone

        check_language(language)
        return plot_ear_canal_microphone(self, ax, language=language, **kwargs)


def verify_ear_canal_microphone(
    *,
    entrance_area_mm2: float,
    canal_section_area_mm2: float,
    volume_mm3: float,
    pink_noise_band_levels_db: ArrayLike,
    open_levels_db: ArrayLike,
    sealed_levels_db: ArrayLike,
    ear_canal_area_mm2: float = _ADULT_EAR_CANAL_AREA_MM2,
) -> EarCanalMicrophoneVerification:
    """May this microphone measure inside the ear canal by IEC 60268-7 Annex B?

    The five measurable conditions of the normative Annex B: a) a
    cross-sectional area of 5 mm² or less within the concha and the first
    4 mm of the canal; b) in the rest of the canal, an area less than 0,6 of
    the canal's ("The average ear canal area of an adult is 45 mm²"); c) a
    volume, mounting parts included, less than 130 mm³; d) responses to
    neighbouring one-third-octave bands of pink noise that "do not differ by
    more than 3 dB"; e) an output level with the sound entrance sealed "at
    least 15 dB below that with the entrance open, at all measuring
    frequencies". Items f) and g), the suspension and the physician's
    certificate, are not numbers.

    :param entrance_area_mm2: Cross-sectional area in the concha and the
        first 4 mm of the canal, in mm².
    :param canal_section_area_mm2: Cross-sectional area in the rest of the
        canal, in mm².
    :param volume_mm3: Volume with the mounting parts, in mm³.
    :param pink_noise_band_levels_db: The microphone's output levels for
        consecutive one-third-octave bands of pink noise of equal level, in
        dB, ascending in frequency.
    :param open_levels_db: The output level with the entrance open at each
        measuring frequency, in dB.
    :param sealed_levels_db: The output level with the entrance sealed at the
        same frequencies, in dB.
    :param ear_canal_area_mm2: The canal's cross-sectional area, in mm²; the
        adult average of item b) by default.
    :return: An :class:`EarCanalMicrophoneVerification`.
    :raises ValueError: If a value is out of range or the level arrays
        disagree in length.
    """
    entrance = require_positive(entrance_area_mm2, "entrance_area_mm2")
    section = require_positive(canal_section_area_mm2, "canal_section_area_mm2")
    canal = require_positive(ear_canal_area_mm2, "ear_canal_area_mm2")
    volume = require_positive(volume_mm3, "volume_mm3")
    bands = np.atleast_1d(
        _levels(pink_noise_band_levels_db, "pink_noise_band_levels_db")
    )
    if bands.ndim != 1 or bands.size < _FEWEST_POINTS:
        msg = "'pink_noise_band_levels_db' must hold at least two bands."
        raise ValueError(msg)
    opened = np.atleast_1d(_levels(open_levels_db, "open_levels_db"))
    sealed = np.atleast_1d(_levels(sealed_levels_db, "sealed_levels_db"))
    if opened.ndim != 1 or opened.shape != sealed.shape or opened.size == 0:
        msg = "'open_levels_db' and 'sealed_levels_db' must be 1-D and of equal length."
        raise ValueError(msg)
    return EarCanalMicrophoneVerification(
        entrance_area_mm2=entrance,
        canal_section_area_mm2=section,
        ear_canal_area_mm2=canal,
        volume_mm3=volume,
        neighbour_difference_db=float(np.max(np.abs(np.diff(bands)))),
        sealed_attenuation_db=float(np.min(opened - sealed)),
    )


# ---------------------------------------------------------------------------
# 8.7: the distortion test signals
# ---------------------------------------------------------------------------


def _time_axis(fs: int, seconds: float) -> NDArray[np.float64]:
    """Sample instants of a record of ``seconds`` at ``fs``."""
    rate = require_count(fs, "fs")
    duration = require_positive(seconds, "seconds")
    n = round(rate * duration)
    if n < 1:
        msg = f"'seconds' of {duration:g} s is shorter than one sample at {rate} Hz."
        raise ValueError(msg)
    return np.arange(n, dtype=np.float64) / rate


def headphone_modulation_signal(
    fs: int, seconds: float, *, rated_source_emf_v: float
) -> NDArray[np.float64]:
    r"""The modulation distortion test signal of IEC 60268-7 8.7.3.

    "The sum of two sinusoidal signals, at 70 Hz and 600 Hz, with amplitude
    ratio 4:1. The peak voltage of the signal shall be equal to that of the
    rated input voltage": amplitudes :math:`0{,}8\sqrt{2}U` and
    :math:`0{,}2\sqrt{2}U` for a rated voltage :math:`U`, which NOTE 1 states
    as "−1,9 dB at 70 Hz and −14,0 dB at 600 Hz". Both start at their crest
    (cosine phase), so the record reaches that peak at its first sample.
    Read the products with
    :func:`~phonometry.electroacoustics.modulation_distortion` at
    ``f_low=70``, ``f_high=600``: the second order at 530 Hz and 670 Hz, the
    third at 460 Hz and 740 Hz.

    :param fs: Sample rate, in hertz.
    :param seconds: Duration, in seconds.
    :param rated_source_emf_v: The rated input voltage, the rated source
        e.m.f. of 8.3.1, in volts (RMS).
    :return: The signal, in volts.
    :raises ValueError: If an input is out of range.
    """
    t = _time_axis(fs, seconds)
    peak = math.sqrt(2.0) * require_positive(rated_source_emf_v, "rated_source_emf_v")
    low, high = _MODULATION_FREQUENCIES_HZ
    share = _MODULATION_RATIO / (_MODULATION_RATIO + 1.0)
    return np.asarray(
        peak * share * np.cos(2.0 * np.pi * low * t)
        + peak * (1.0 - share) * np.cos(2.0 * np.pi * high * t),
        dtype=np.float64,
    )


def headphone_difference_frequency_signal(
    fs: int, seconds: float, *, upper_frequency_hz: float, rated_source_emf_v: float
) -> NDArray[np.float64]:
    """The difference-frequency distortion test signal of IEC 60268-7 8.7.4.

    "Two sinusoidal signals, separated in frequency by 80 Hz, each giving half
    the rated input voltage": tones at :math:`f_2 - 80` Hz and :math:`f_2`,
    each of RMS value :math:`U/2`, in cosine phase so that the peak is that of
    the rated voltage. Read the products with
    :func:`~phonometry.electroacoustics.difference_frequency_distortion`.

    :param fs: Sample rate, in hertz.
    :param seconds: Duration, in seconds.
    :param upper_frequency_hz: The upper tone :math:`f_2`, in Hz, above 80 Hz
        and below the Nyquist frequency.
    :param rated_source_emf_v: The rated input voltage, in volts (RMS).
    :return: The signal, in volts.
    :raises ValueError: If an input is out of range.
    """
    t = _time_axis(fs, seconds)
    upper = require_positive(upper_frequency_hz, "upper_frequency_hz")
    require_scalar(fs, "fs")
    if not _DIFFERENCE_FREQUENCY_HZ < upper < 0.5 * float(fs):
        msg = (
            f"'upper_frequency_hz' must lie between {_DIFFERENCE_FREQUENCY_HZ:g} Hz "
            "and the Nyquist frequency."
        )
        raise ValueError(msg)
    amplitude = (
        math.sqrt(2.0)
        * require_positive(rated_source_emf_v, "rated_source_emf_v")
        / 2.0
    )
    lower = upper - _DIFFERENCE_FREQUENCY_HZ
    return np.asarray(
        amplitude * (np.cos(2.0 * np.pi * lower * t) + np.cos(2.0 * np.pi * upper * t)),
        dtype=np.float64,
    )
