#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Calibration of working standard microphones by comparison
(IEC 61094-5:2016, pressure; IEC 61094-8:2012, free field).

IEC 61094-5 prints the corrections for a WS3 microphone in the jig of Figure
A.4 (Table A.1) and a worked uncertainty budget at 2 kHz (Table D.1, combined
in D.3). IEC 61094-8 prints the typical expanded uncertainty of each way of
calibrating the reference microphone (Table 1) and the list of typical
uncertainty components with their subclauses (Table 2), without values. Every
number was read on the rasterized printed page: IEC 61094-5:2016 (Edition
2.0, 2016-05, English-French) Table A.1 on printed folio 15 (PDF page 17),
Annex D on folios 19 to 21 (PDF pages 21 to 23); BS EN 61094-8:2012, the
English text of EN 61094-8:2012 which is IEC 61094-8:2012 unchanged, Table 1
on folio 12 (PDF page 14) and Table 2 on folio 17 (PDF page 19).

Stdlib only, like every module of this package.
"""

from __future__ import annotations

import math

#: IEC 61094-5:2016 Table A.1, folio 15 (PDF page 17): the correction, in
#: dB, keyed by frequency in kHz as the table prints it.
IEC61094_5_TABLE_A1_DB: dict[float, float] = {
    1.0: -0.004,
    1.25: -0.006,
    1.6: -0.009,
    2.0: -0.015,
    2.5: -0.023,
    3.15: -0.036,
    4.0: -0.059,
    5.0: -0.092,
    6.3: -0.146,
    8.0: -0.235,
    10.0: -0.367,
    12.5: -0.572,
    16.0: -0.933,
    20.0: -1.443,
}

#: Table A.1 NOTE: the expanded uncertainty is one tenth of the correction.
IEC61094_5_TABLE_A1_RELATIVE_EXPANDED = 0.1

#: IEC 61094-5:2016 Table D.1, folio 20 (PDF page 22): the standard
#: uncertainty column, in dB, keyed by component.
IEC61094_5_TABLE_D1_STANDARD_DB: dict[str, float] = {
    "reference": 0.025,
    "capacitance": 0.006,
    "non_linearity": 0.017,
    "impedance": 0.003,
    "polarizing_voltage": 0.005,
    "repeatability": 0.025,
    "drift": 0.017,
    "rounding": 0.003,
}

#: Table D.1: the value each row's text states and what it is divided by,
#: for the seven rows that state one. The reference is quoted "as ± 0,05 dB
#: with a coverage factor of k = 2", and the polarising voltage is set to
#: (200,0 ± 0,2) V "giving a semi-range for this component of
#: 20 lg (200,2/200) dB with a rectangular distribution". The repeatability
#: row states no value ("Found from the standard uncertainties of a large
#: number of similar measurements."), so it is not here.
IEC61094_5_TABLE_D1_STATED: dict[str, tuple[float, float]] = {
    "reference": (0.05, 2.0),
    "capacitance": (0.01, math.sqrt(3.0)),
    "non_linearity": (0.03, math.sqrt(3.0)),
    "impedance": (0.005, math.sqrt(3.0)),
    "polarizing_voltage": (20.0 * math.log10(200.2 / 200.0), math.sqrt(3.0)),
    "drift": (0.03, math.sqrt(3.0)),
    "rounding": (0.005, math.sqrt(3.0)),
}

#: IEC 61094-5:2016 D.3, folio 21 (PDF page 23): the combined standard
#: uncertainty and the expanded one (k = 2) as printed. They are not the
#: root-sum-square of the eight components of Table D.1 (docs/ERRATA.md).
IEC61094_5_D3_PRINTED_COMBINED_DB = 0.040
IEC61094_5_D3_PRINTED_EXPANDED_DB = 0.08

#: The root-sum-square of the printed standard uncertainty column, the value
#: D.3 describes, to four decimals: 0,043 669 dB.
IEC61094_5_D3_COMBINED_DB = 0.0437

#: The same with k = 2, to three decimals: 0,087 34 dB.
IEC61094_5_D3_EXPANDED_DB = 0.087

#: The "strict calculation" D.3 mentions and does not print: each component
#: of the printed column converted to a relative uncertainty
#: 10**(u/20) - 1, combined in quadrature and converted back by
#: 20 lg(1 + r), to six decimals: 0,043 614 dB, 0,000 055 dB below the
#: combination in decibels.
IEC61094_5_D3_LINEAR_COMBINED_DB = 0.043614

#: BS EN 61094-8:2012 Table 1, folio 12 (PDF page 14): the typical expanded
#: uncertainty (k = 2) at 1 kHz and at 10 kHz, in dB, of each way of
#: calibrating the reference microphone, in the table's order.
IEC61094_8_TABLE_1_DB: dict[str, tuple[float, float]] = {
    "primary_free_field": (0.25, 0.10),
    "primary_pressure": (0.12, 0.4),
    "secondary_pressure": (0.15, 0.5),
    "secondary_free_field": (0.2, 0.5),
    "electrostatic_actuator": (0.3, 0.6),
}

#: BS EN 61094-8:2012 Table 1, folio 12 (PDF page 14): the text cells of each
#: row, the reference microphone type, the calibration method and the
#: references, in the table's order. The type is printed once for the rows it
#: spans; "This part of IEC 61094" is IEC 61094-8, and "IEC 61094-2 and
#: IEC/TS 61094-7" is two references.
IEC61094_8_TABLE_1_TEXT: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "primary_free_field": (
        "LS",
        "Primary free-field calibration",
        ("IEC 61094-3",),
    ),
    "primary_pressure": (
        "LS",
        "Primary pressure calibration with the addition of a free-field to "
        "pressure sensitivity level difference",
        ("IEC 61094-2", "IEC/TS 61094-7"),
    ),
    "secondary_pressure": (
        "LS",
        "Secondary pressure calibration with the addition of a free-field to "
        "pressure sensitivity level difference",
        ("IEC 61094-5", "IEC/TS 61094-7"),
    ),
    "secondary_free_field": (
        "LS and WS",
        "Secondary free-field calibration",
        ("IEC 61094-8",),
    ),
    "electrostatic_actuator": (
        "LS and WS",
        "Electrostatic actuator calibration with the addition of a free-field "
        "to actuator response level difference",
        ("IEC 61094-6",),
    ),
}

#: BS EN 61094-8:2012 Table 2, folio 17 (PDF page 19): the source of
#: uncertainty of each row as printed, in the table's order.
IEC61094_8_TABLE_2_SOURCES: dict[str, str] = {
    "reference": "Free-field sensitivity of the reference microphone",
    "source_stability": "Stability of sound source",
    "positioning": "Positioning accuracy (including acoustic centre uncertainty)",
    "alignment": "Alignment between source and receiver",
    "free_field": (
        "Quality of free-field environment or influence of signal processing"
    ),
    "non_plane_wave": "Influence of non-plane wave",
    "environment": "Influence of environmental conditions",
    "polarizing_voltage": "Polarizing voltage",
    "capacitance": "Microphone capacitance",
    "non_linearity": "Measurement system non-linearity",
    "rounding": "Rounding error",
    "repeatability": "Measurement repeatability",
}

#: BS EN 61094-8:2012 Table 2, folio 17 (PDF page 19): the subclause
#: references of the twelve typical components, in the table's order ("-"
#: for the rounding error).
IEC61094_8_TABLE_2_SUBCLAUSES: dict[str, tuple[str, ...]] = {
    "reference": ("8.2",),
    "source_stability": ("8.4",),
    "positioning": ("7.3", "8.4"),
    "alignment": ("7.4", "8.4"),
    "free_field": ("8.5", "8.6"),
    "non_plane_wave": ("6.3",),
    "environment": ("7.6",),
    "polarizing_voltage": ("7.2", "8.2"),
    "capacitance": ("8.7.1",),
    "non_linearity": ("8.7.2",),
    "rounding": (),
    "repeatability": ("8.3",),
}

#: IEC 61094-5 clause 4 and IEC 61094-8 clause 4: the reference environmental
#: conditions, 23,0 °C, 101,325 kPa and 50 %.
IEC61094_REFERENCE_CONDITIONS: tuple[float, float, float] = (23.0, 101.325, 50.0)

#: BS EN 61094-8:2012 B.2.2, folio 25 (PDF page 27): "in small anechoic
#: rooms, with typical internal dimensions of around 1,5 m, it is enough to
#: have a frequency resolution of 120 Hz because the primary reflections all
#: occur before 8 ms": the step in Hz and the arrival in s.
IEC61094_8_B22_SMALL_ROOM: tuple[float, float] = (120.0, 0.008)

#: B.2.2, the same page: in a large high performance free-field room "a
#: frequency resolution of approximately 30 Hz is appropriate", in Hz.
IEC61094_8_B22_LARGE_ROOM_STEP_HZ = 30.0

#: BS EN 61094-8:2012 B.6.1, folio 28 (PDF page 30): the first zero of the
#: pulse spectrum "must be approximately an order of magnitude higher than
#: the upper limit of the frequency range of interest".
IEC61094_8_B61_ZERO_RATIO = 10.0

#: BS EN 61094-1:2001 6.2.2, page 9 (PDF page 11), the English text of
#: EN 61094-1:2000 which is IEC 61094-1:2000: "The value of κr shall be taken
#: as 1,40" in the definition of the equivalent volume.
IEC61094_1_KAPPA_REFERENCE = 1.40
