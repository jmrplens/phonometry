#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The substitution measurement of ISO 7235 and ISO 11691.

Neither standard prints a worked example, so there is no column of
intermediates to reproduce here. What both print instead is tables and closed
form, and those are the oracle: ISO 11691 Table 1 and Equations (1) and (2),
and ISO 7235 Equation (1), the reverberation correction of 6.3, Table 6,
Table 7 and the coverage factor of 7.9.

Oracles: BS EN ISO 11691:2009 (printed folios 1 to 5, PDF pages 7 to 11),
which endorses ISO 11691:1995 without modification, and BS EN ISO 7235:2009
(printed folios 2, 23 and 31, PDF pages 12, 33 and 41), which endorses
ISO 7235:2003 without modification.

One printed defect sits in this oracle and is recorded in ``docs/ERRATA.md``:
Table 6 of ISO 7235 names the bands 50, 63, 80, 100 and 125 Hz and then
``> 160`` Hz, so the 160 Hz one-third octave belongs to no row and is given
no limit at all. Every other row names a single band, and the row is read
here as "160 Hz and above".
"""

from __future__ import annotations

import math

import numpy as np

import phonometry as ph

from ..registry import Outcome, mask, numeric, record, register

_ISO7235 = "Ducted silencer measurement (ISO 7235, ISO 11691)"

#: The two test series of a substitution measurement, in dB, over six
#: one-third-octave bands: the same rig with an empty duct and with a
#: parallel-baffle silencer in its place.
_SUBSTITUTION = (88.0, 90.0, 91.0, 92.0, 92.0, 91.0)
_WITH_OBJECT = (84.0, 83.0, 79.0, 72.0, 66.0, 63.0)


@register(_ISO7235, "ISO 11691:1995", "Insertion loss by substitution (Eq. (1))")
def _chk_substitution_insertion_loss() -> Outcome:
    """The subtraction, band by band.

    Equation (1) of ISO 11691 is ``D = L_p1 - L_p2`` with the substitution
    duct first; Equation (1) of ISO 7235 is ``D_i = L_WII - L_WI`` with the
    substitution duct second. The two numberings are opposite and the
    arithmetic is the same, which is what this row pins: the level without
    the silencer minus the level with it, and nothing else.
    """
    found = ph.noise_control.substitution_insertion_loss(_SUBSTITUTION, _WITH_OBJECT)
    expected = {
        f"{band} Hz": float(without - with_object)
        for band, without, with_object in zip(
            (50, 63, 80, 100, 125, 160), _SUBSTITUTION, _WITH_OBJECT, strict=True
        )
    }
    computed = dict(zip(expected, (float(v) for v in found), strict=True))
    return record(expected, computed, unit="dB")


@register(
    _ISO7235,
    "ISO 7235:2003",
    "Reverberation-time correction of the insertion loss (6.3)",
)
def _chk_reverberation_correction() -> Outcome:
    """A receiving room twice as live holds the second level up by 10 lg 2.

    Clause 6.3 writes ``D_i = L_p1 - L_p2 + 10 lg(T_2 / T_1)``, with ``T_2``
    the reverberation time measured with the test object installed. Doubling
    it has to add exactly 3,0103 dB to the insertion loss and nothing else,
    so the correction is checked against the logarithm rather than against a
    rounded decibel.
    """
    plain = ph.noise_control.substitution_insertion_loss(90.0, 65.0)
    corrected = ph.noise_control.substitution_insertion_loss(
        90.0, 65.0, reverberation_times=(1.0, 2.0)
    )
    return numeric(
        10.0 * math.log10(2.0),
        float(corrected[0] - plain[0]),
        1e-12,
        unit="dB",
        places=6,
        expected_label="10 lg 2 = 3,010300 dB",
    )


@register(_ISO7235, "ISO 11691:1995", "Octave from three one-third octaves (Eq. (2))")
def _chk_octave_insertion_loss() -> Outcome:
    """Equation (2) averages the transmission, not the decibels.

    Three one-third octaves of 30, 30 and 5 dB average to 21,67 dB read as
    decibels and to 9,74 dB read as Equation (2) asks. The difference is the
    whole point of the equation being written out: the leaky band carries
    nearly all of the transmitted energy, so it decides the octave.
    """
    found = ph.noise_control.octave_insertion_loss((30.0, 30.0, 5.0))
    energy = (10.0 ** (-3.0) + 10.0 ** (-3.0) + 10.0 ** (-0.5)) / 3.0
    return numeric(
        -10.0 * math.log10(energy),
        float(found[0]),
        1e-12,
        unit="dB",
        places=6,
        expected_label="-10 lg[(10^-3 + 10^-3 + 10^-0,5)/3] = 9,744 dB",
    )


@register(_ISO7235, "ISO 11691:1995", "Bounds of the octave insertion loss (Eq. (2))")
def _chk_octave_bounds() -> Outcome:
    """Equation (2) cannot leave the band it is bracketed by.

    Whatever the three one-third octaves are, the octave lies between the
    smallest of them and that value plus 10 lg 3 = 4,771 dB: the mean of the
    three transmitted energies is at least a third of the largest and at most
    the largest itself. The example is the same 30, 30 and 5 dB triple, whose
    9,744 dB sits 4,744 dB above its worst band with 0,027 dB of headroom to
    the upper edge.
    """
    thirds = (30.0, 30.0, 5.0)
    found = float(ph.noise_control.octave_insertion_loss(thirds)[0])
    worst = min(thirds)
    return mask(
        expected=f"between {worst:.3f} dB and {worst + 10.0 * math.log10(3.0):.3f} dB",
        computed=f"{found:.3f} dB",
        deviation=found,
        lower=worst,
        upper=worst + 10.0 * math.log10(3.0),
        unit="dB",
    )


@register(_ISO7235, "ISO 11691:1995", "Reproducibility of the survey method (Table 1)")
def _chk_survey_reproducibility() -> Outcome:
    """Table 1, both rows.

    Two decibels from 50 Hz to the 1,25 kHz one-third octave and three from
    1,6 kHz to 10 kHz. ISO 11691 offers no interlaboratory result of its own
    and says only that this is what makes it a survey standard.
    """
    bands = (50.0, 1250.0, 1600.0, 10000.0)
    expected = {"50 Hz": 2.0, "1250 Hz": 2.0, "1600 Hz": 3.0, "10000 Hz": 3.0}
    computed = {
        f"{band:.0f} Hz": ph.noise_control.survey_reproducibility(band)
        for band in bands
    }
    return record(expected, computed, unit="dB")


@register(_ISO7235, "ISO 7235:2003", "Microphone position spread limits (Table 6)")
def _chk_spread_limits() -> Outcome:
    """Table 6, every printed row.

    The limit falls from 10 dB at 50 and 63 Hz to 6 dB from 160 Hz upwards.
    The printed last row reads ``> 160``, which leaves the 160 Hz one-third
    octave itself with no limit; it is read here as belonging to that row and
    the gap is registered in ``docs/ERRATA.md``. The row also pins where the
    step sits, at 130 Hz, so that a boundary moved anywhere into the gap the
    printed table leaves between 125 and 160 changes an answer here.
    """
    expected = {
        "50 Hz": 10.0,
        "63 Hz": 10.0,
        "80 Hz": 8.0,
        "100 Hz": 8.0,
        "125 Hz": 7.0,
        "just above 125 Hz": 6.0,
        "160 Hz and above": 6.0,
    }
    bands = (50.0, 63.0, 80.0, 100.0, 125.0, 130.0, 200.0)
    computed = dict(
        zip(
            expected,
            (ph.noise_control.microphone_spread_limit(band) for band in bands),
            strict=True,
        )
    )
    return record(expected, computed, unit="dB")


@register(_ISO7235, "ISO 7235:2003", "Three microphone positions, or five (6.2.1)")
def _chk_positions_required() -> Outcome:
    """The rule Table 6 serves, at the band where it binds.

    Three positions spread over 9 dB are too far apart at 125 Hz, where the
    limit is 7 dB, and close enough at 50 Hz, where it is 10. The same three
    levels therefore need five positions in one band and three in another,
    which is the whole content of the rule.
    """
    levels = (70.0, 74.0, 79.0)
    expected = {"at 50 Hz": 3.0, "at 125 Hz": 5.0, "at 1000 Hz": 5.0}
    computed = {
        "at 50 Hz": float(ph.noise_control.microphone_positions_required(levels, 50.0)),
        "at 125 Hz": float(
            ph.noise_control.microphone_positions_required(levels, 125.0)
        ),
        "at 1000 Hz": float(
            ph.noise_control.microphone_positions_required(levels, 1000.0)
        ),
    }
    return record(expected, computed)


@register(
    _ISO7235, "ISO 7235:2003", "Reproducibility of the three quantities (Table 7)"
)
def _chk_reproducibility_table() -> Outcome:
    """Table 7, all three columns at all four band ranges.

    The insertion-loss column is the only one measured, on 1 m long
    parallel-baffle silencers, and it is the only one that moves with
    frequency in a way that looks like data: best in the middle at 1 dB and
    worst at the top at 3. The transmission-loss column is a flat 3 dB, and
    the sound-intensity column runs the other way, which is what an estimate
    based on experience looks like.
    """
    bands = (50.0, 250.0, 1000.0, 4000.0)
    columns = ("insertion_loss", "transmission_loss", "intensity")
    expected = {
        "insertion_loss 50 Hz": 1.5,
        "insertion_loss 250 Hz": 1.0,
        "insertion_loss 1000 Hz": 2.0,
        "insertion_loss 4000 Hz": 3.0,
        "transmission_loss 50 Hz": 3.0,
        "transmission_loss 250 Hz": 3.0,
        "transmission_loss 1000 Hz": 3.0,
        "transmission_loss 4000 Hz": 3.0,
        "intensity 50 Hz": 3.0,
        "intensity 250 Hz": 1.5,
        "intensity 1000 Hz": 1.0,
        "intensity 4000 Hz": 1.0,
    }
    computed = {
        f"{column} {band:.0f} Hz": ph.noise_control.measurement_reproducibility(
            band, quantity=column
        )
        for column in columns
        for band in bands
    }
    return record(expected, computed, unit="dB")


@register(_ISO7235, "ISO 7235:2003", "Expanded measurement uncertainty (7.9)")
def _chk_expanded_uncertainty() -> Outcome:
    """Twice the standard deviation of Table 7, for 95 % coverage.

    A measured insertion loss is within 2 dB of the truth at 250 Hz and
    within 6 dB at 4 kHz, which is the same as saying the top of the range is
    three times as uncertain as the middle.
    """
    expected = {"250 Hz": 2.0, "4000 Hz": 6.0}
    computed = {
        f"{band:.0f} Hz": ph.noise_control.measurement_expanded_uncertainty(band)
        for band in (250.0, 4000.0)
    }
    return record(expected, computed, unit="dB")


@register(_ISO7235, "ISO 11691:1995", "Test duct against the silencer (4.5)")
def _chk_area_ratio() -> Outcome:
    """The 0,6 to 1,7 the survey method holds the ducts to.

    Inside the range the two joints reflect little enough that the test ducts
    stand in for the installation, and transition elements may be fitted;
    outside it the arrangement is no longer the one the method was written
    for.
    """
    expected = {"lower": 0.6, "upper": 1.7}
    low, high = ph.noise_control.SURVEY_AREA_RATIO_RANGE
    computed = {
        "lower": ph.noise_control.substitution_area_ratio(0.1 * low, 0.1),
        "upper": ph.noise_control.substitution_area_ratio(0.1 * high, 0.1),
    }
    return record(expected, computed)


#: A 350 mm circular test duct, as its cross-sectional area in m², and the
#: octave centres a laboratory would report it over.
_DUCT_AREA = 0.0962
_BANDS = (63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0)


@register(
    _ISO7235, "ISO 7235:2003", "Open-end transmission loss and reflection (B.3), (B.4)"
)
def _chk_open_end_identity() -> Outcome:
    """The two Annex B equations are the same physics said twice.

    Neither is printed with a worked value, but they cannot disagree: what
    the duct mouth does not transmit it reflects, so
    ``D_td = -10 lg(1 - r^2)`` at every frequency, area and solid angle. The
    row evaluates both at six octave centres on a 350 mm duct, once for each
    of the five configurations of Table B.1, and reports the largest
    disagreement across all thirty pairs.
    """
    worst = 0.0
    for angle in ph.noise_control.RADIATION_SOLID_ANGLES.values():
        loss = ph.noise_control.open_end_transmission_loss(
            _BANDS, _DUCT_AREA, solid_angle=angle
        )
        reflected = ph.noise_control.open_end_reflection_coefficient(
            _BANDS, _DUCT_AREA, solid_angle=angle
        )
        closed = -10.0 * np.log10(1.0 - reflected**2)
        worst = max(worst, float(np.max(np.abs(loss - closed))))
    return numeric(
        0.0,
        worst,
        1e-12,
        unit="dB",
        places=12,
        expected_label="D_td = -10 lg(1 - r^2) at all 30 pairs",
        computed_label=f"largest disagreement {worst:.3e} dB",
    )


@register(
    _ISO7235, "ISO 7235:2003", "Solid angle of radiation at the duct end (Table B.1)"
)
def _chk_solid_angles() -> Outcome:
    """Table B.1, all five configurations of Figure B.2.

    The same five values are printed as Table 1 of ISO 5135:1999, entry for
    entry: a duct flush in a wall radiates into a half space, one at the
    junction of a wall and the floor into a quarter, and one standing free in
    the room into the whole of it.
    """
    expected = {
        "A (flush in a wall)": 2.0 * math.pi,
        "B (wall and floor)": math.pi,
        "C (free in the room)": 4.0 * math.pi,
        "D (on the floor)": 2.0 * math.pi,
        "E (mid-room duct)": 4.0 * math.pi,
    }
    computed = dict(
        zip(
            expected,
            ph.noise_control.RADIATION_SOLID_ANGLES.values(),
            strict=True,
        )
    )
    return record(expected, computed, unit="sr")


@register(_ISO7235, "ISO 7235:2003", "Rectangular cut-on frequency (Eq. (5))")
def _chk_rectangular_cut_on() -> Outcome:
    """Equation (5) is exact, and the library's own eigenvalues say so.

    The first higher-order mode of a rigid rectangular duct is a half
    wavelength across the larger dimension, so ``f = c / 2H``, which is the
    ``0,5 c / H`` NOTE 2 prints. The independent route through Norton &
    Karczub's eigenvalues has to give the same number to the last bit.
    """
    exact = ph.noise_control.rectangular_duct_cut_on(
        0.5, 0.2, speed_of_sound=343.0, count=1
    )
    found = ph.noise_control.modal_filter_cut_on(larger_dimension=0.5)
    return numeric(
        float(exact.cut_on_no_flow[0]),
        found,
        1e-9,
        unit="Hz",
        places=6,
        expected_label="343,000000 Hz from the (1, 0) eigenvalue",
    )


@register(_ISO7235, "ISO 7235:2003", "Circular cut-on frequency (Eq. (4))")
def _chk_circular_cut_on() -> Outcome:
    """Equation (4) is the same mode with a rounded constant.

    The exact coefficient is the first zero of the derivative of the Bessel
    function of order one divided by pi, 1,8412 / pi = 0,58607. The standard
    prints 0,59, which is 0,67 % high: on the 0,4 m duct of the sound source
    of ISO 11691 that is 505,9 Hz against 502,6 Hz, a difference of 3,4 Hz on
    a frequency the modal filter requirement steps at. The row pins the
    ratio, which is the part that does not depend on the duct.
    """
    exact = ph.noise_control.circular_duct_cut_on(0.4, speed_of_sound=343.0, count=1)
    found = ph.noise_control.modal_filter_cut_on(diameter=0.4)
    return numeric(
        0.59 / (1.8412 / math.pi),
        found / float(exact.cut_on_no_flow[0]),
        1e-9,
        places=6,
        expected_label="0,59 / (1,8412 / pi) = 1,006701",
    )


@register(
    _ISO7235, "ISO 7235:2003", "Transmission loss of an air-terminal unit (Eq. (6))"
)
def _chk_measured_transmission_loss() -> Outcome:
    """Equation (6) and the limit that makes it meaningful.

    ``D_t = D_i + D_td`` puts back what the open end of the duct was keeping
    in anyway, so the gap between the two quantities has to be Equation (B.3)
    exactly. The expected side here is that equation written out again away
    from the library: on a 350 mm duct flush with a wall it is 11,2 dB at
    63 Hz and 0,05 dB at 2 kHz, which is why an air-terminal unit's
    transmission loss and its insertion loss are the same number at the top
    of the range and are not at the bottom.
    """
    insertion = np.array([4.0, 7.0, 12.0, 20.0, 26.0, 28.0])
    open_end = ph.noise_control.open_end_transmission_loss(_BANDS, _DUCT_AREA)
    found = ph.noise_control.measured_transmission_loss(insertion, open_end)

    def printed(band: float) -> float:
        """Equation (B.3) written out again, away from the library."""
        mouth = 4.0 * math.pi * band * math.sqrt(_DUCT_AREA) / 343.0
        return 10.0 * math.log10(1.0 + 2.0 * math.pi / mouth**2)

    expected = {
        f"{band:.0f} Hz gap": round(printed(band), 6) for band in (63.0, 2000.0)
    }
    computed = {
        "63 Hz gap": round(float(found[0] - insertion[0]), 6),
        "2000 Hz gap": round(float(found[-1] - insertion[-1]), 6),
    }
    return record(expected, computed, unit="dB")


@register(_ISO7235, "ISO 7235:2003", "Normal air density (Eqs. (10), (21), (22))")
def _chk_normal_air_density() -> Outcome:
    """The gas law with the standard's own two constants.

    ISO 7235 prints ``R = 287 N.m/(kg.K)`` and writes the absolute
    temperature as ``theta + 273 degC``. Neither is the accurate figure
    (287,05 and 273,15): the offset alone puts a density 0,051 % high at
    20 °C and the gas constant adds 0,017 % to that. The row pins the printed
    arithmetic, which is what reproduces a result computed to the standard.
    The error does not cancel where the density is used, it scales: the same
    value is in the dynamic pressure of both test series, so the pressure
    loss coefficient of Equation (18) comes out 0,069 % low rather than
    displaced, which is far under the uncertainty of the test.
    """
    found = ph.noise_control.normal_air_density(200.0, 101325.0, 20.0)
    printed = (101325.0 + 200.0) / (287.0 * (20.0 + 273.0))
    return numeric(
        printed,
        found,
        1e-12,
        unit="kg/m3",
        places=6,
        expected_label="(101 325 + 200) / (287 x 293) = 1,207323 kg/m³",
    )


@register(
    _ISO7235, "ISO 7235:2003", "Total pressure loss across unequal ducts (Eq. (12))"
)
def _chk_total_pressure_loss() -> Outcome:
    """The bracket that keeps an area change out of the answer.

    An object that widens the duct turns velocity head back into static
    pressure, and a static-pressure difference alone would credit it with a
    recovery that is only bookkeeping. Equation (12) adds
    ``p_d1 [1 - (S_1/S_2)^2]`` back. The row checks the three cases the
    bracket has: equal ducts, where it vanishes as the NOTE to Equation (14)
    says it usually does; twice the outlet area, where it returns three
    quarters of the inlet velocity head; and half of it, where it takes three
    whole heads away.
    """
    head = ph.noise_control.dynamic_pressure(1.0, 0.0962, 1.2)
    expected = {
        "S_2 = S_1": 45.0,
        "S_2 = 2 S_1": 45.0 + 0.75 * head,
        "S_2 = S_1 / 2": 45.0 - 3.0 * head,
    }
    computed = {
        "S_2 = S_1": ph.noise_control.total_pressure_loss(45.0, head, 0.0962, 0.0962),
        "S_2 = 2 S_1": ph.noise_control.total_pressure_loss(
            45.0, head, 0.0962, 2.0 * 0.0962
        ),
        "S_2 = S_1 / 2": ph.noise_control.total_pressure_loss(
            45.0, head, 0.0962, 0.5 * 0.0962
        ),
    }
    return record(expected, computed, unit="Pa")


@register(
    _ISO7235, "ISO 7235:2003", "Pressure loss coefficient is flow invariant (Eq. (14))"
)
def _chk_pressure_loss_coefficient() -> Outcome:
    """The coefficient belongs to the object, not to the test point.

    A total pressure loss grows as the square of the velocity, and so does
    the velocity head Equation (14) divides it by, so the ratio is the same
    number at every flow rate the loss scales that way at. That is what makes
    the coefficient reportable at all, and it is the algebra this row pins: a
    loss four times larger at twice the flow gives one value. Real flow is
    only approximately similar, because twice the rate is twice the Reynolds
    number, which is why 6.5.2 measures at five rates and averages rather
    than trusting one.
    """
    slow = ph.noise_control.pressure_loss_coefficient(
        45.0, ph.noise_control.dynamic_pressure(1.0, 0.1, 1.2)
    )
    fast = ph.noise_control.pressure_loss_coefficient(
        4.0 * 45.0, ph.noise_control.dynamic_pressure(2.0, 0.1, 1.2)
    )
    return numeric(
        slow,
        fast,
        1e-12,
        places=6,
        expected_label=f"zeta = {slow:.6f} at 1 m³/s",
        computed_label=f"{fast:.6f} at 2 m³/s",
    )


@register(_ISO7235, "ISO 7235:2003", "Averaged pressure loss coefficient (Eq. (18))")
def _chk_average_pressure_loss_coefficient() -> Outcome:
    """The computational route of 6.5.2.2.3, which is a substitution too.

    Equation (18) averages the coefficients rather than the pressures, so the
    two series need share neither their flow rates nor their point count.
    The row runs a test object at 2,5 velocity heads against a substitution
    duct at 0,4, over five points and six points at different flow rates, and
    the difference has to come back as exactly 2,1.
    """
    first = np.array([20.0, 40.0, 60.0, 80.0, 100.0])
    second = np.array([25.0, 50.0, 75.0, 100.0, 125.0, 150.0])
    found = ph.noise_control.average_pressure_loss_coefficient(
        2.5 * first, first, 0.4 * second, second
    )
    return numeric(
        2.1,
        found,
        1e-12,
        places=6,
        expected_label="2,5 - 0,4 = 2,100000",
    )


@register(_ISO7235, "ISO 7235:2003", "Upstream straight length (6.5.2.2.1)")
def _chk_upstream_length() -> Outcome:
    """Five equivalent diameters or two metres, whichever is greater.

    The two rules cross at the duct whose five diameters are exactly two
    metres, which is an equivalent diameter of 0,4 m and an area of
    0,1257 m². Below it the floor binds and above it the diameters do, and
    the row checks a duct on each side of the crossing as well as the
    crossing itself.
    """
    crossing = math.pi * (2.0 / 5.0) ** 2 / 4.0
    expected = {
        "S = 0,0962 m² (350 mm)": 2.0,
        "S = 0,1257 m² (400 mm)": 2.0,
        "S = 0,5 m²": 5.0 * math.sqrt(4.0 * 0.5 / math.pi),
    }
    computed = {
        "S = 0,0962 m² (350 mm)": ph.noise_control.upstream_straight_length(0.0962),
        "S = 0,1257 m² (400 mm)": ph.noise_control.upstream_straight_length(crossing),
        "S = 0,5 m²": ph.noise_control.upstream_straight_length(0.5),
    }
    return record(expected, computed, unit="m")


@register(
    _ISO7235,
    "ISO 5135:1999",
    "End reflection loss is ISO 7235 (B.3) written out (Eq. (2))",
)
def _chk_iso5135_end_reflection() -> Outcome:
    """Two standards, two printings, one formula.

    ISO 5135 Equation (2) reads
    ``Delta L_r = 10 lg[1 + (c / 4 pi f)^2 (Omega / S)]`` and ISO 7235
    Equation (B.3) reads ``D_td = 10 lg[1 + Omega / (4 pi f sqrt(S) / c)^2]``.
    Expanding either gives ``10 lg[1 + Omega c^2 / (16 pi^2 f^2 S)]``, so the
    end reflection loss of one and the open-end transmission loss of the
    other are one quantity under two names. The expected side here is the
    ISO 5135 printing evaluated on its own, over six octave centres and all
    five configurations of Table 1.
    """
    worst = 0.0
    for angle in ph.noise_control.RADIATION_SOLID_ANGLES.values():
        iso5135 = 10.0 * np.log10(
            1.0
            + (343.0 / (4.0 * math.pi * np.asarray(_BANDS))) ** 2 * (angle / _DUCT_AREA)
        )
        iso7235 = ph.noise_control.open_end_transmission_loss(
            _BANDS, _DUCT_AREA, solid_angle=angle
        )
        worst = max(worst, float(np.max(np.abs(iso5135 - iso7235))))
    return numeric(
        0.0,
        worst,
        1e-12,
        unit="dB",
        places=12,
        expected_label="ISO 5135 (2) = ISO 7235 (B.3) at all 30 pairs",
        computed_label=f"largest disagreement {worst:.3e} dB",
    )


@register(_ISO7235, "ISO 5135:1999", "Sound power level in the duct (Eq. (1))")
def _chk_duct_sound_power() -> Outcome:
    """What the room measured, plus what the duct mouth kept in.

    ``L_Wduct = L_W + Delta L_r``. On the 350 mm duct of the other rows,
    flush with a wall, that is 11,2 dB at 63 Hz and 0,05 dB at 2 kHz, so an
    air-terminal device measured in a reverberation room is understated in
    the duct by eleven decibels at the bottom of the range and by nothing at
    the top.
    """
    room = np.full(len(_BANDS), 60.0)
    reflection = ph.noise_control.open_end_transmission_loss(_BANDS, _DUCT_AREA)
    found = ph.noise_control.duct_sound_power_level(room, reflection)
    expected = {
        f"{band:.0f} Hz": round(60.0 + float(value), 6)
        for band, value in zip(_BANDS, reflection, strict=True)
    }
    computed = {
        f"{band:.0f} Hz": round(float(value), 6)
        for band, value in zip(_BANDS, found, strict=True)
    }
    return record(expected, computed, unit="dB")


@register(_ISO7235, "ISO 5135:1999", "Least-squares operating line (5.5.2)")
def _chk_operating_line() -> Outcome:
    """The fit, on data whose answer is known before it is fitted.

    A device whose level follows a clean twenty decibels per decade of flow
    rate has to come back with that slope, no deviation from the line at any
    point, and the level it was built around at the duty it was built around.
    The row also pins the range 5.5.2 allows the line to be read over, half
    the smallest duty measured to twice the largest.
    """
    duty = np.array([0.05, 0.1, 0.2, 0.4, 0.8])
    levels = 50.0 + 20.0 * np.log10(duty / 0.2)
    line = ph.noise_control.fit_operating_line(duty, levels)
    expected = {
        "slope [dB/decade]": 20.0,
        "level at 0,2 m³/s [dB]": 50.0,
        "worst deviation [dB]": 0.0,
        "lowest readable duty [m³/s]": 0.025,
        "highest readable duty [m³/s]": 1.6,
    }
    computed = {
        "slope [dB/decade]": round(line.slope, 6),
        "level at 0,2 m³/s [dB]": round(line.level_at(0.2), 6),
        "worst deviation [dB]": round(line.maximum_deviation, 6),
        "lowest readable duty [m³/s]": round(line.valid_range[0], 6),
        "highest readable duty [m³/s]": round(line.valid_range[1], 6),
    }
    return record(expected, computed)
