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
    the gap is registered in ``docs/ERRATA.md``.
    """
    expected = {
        "50 Hz": 10.0,
        "63 Hz": 10.0,
        "80 Hz": 8.0,
        "100 Hz": 8.0,
        "125 Hz": 7.0,
        "160 Hz and above": 6.0,
    }
    bands = (50.0, 63.0, 80.0, 100.0, 125.0, 200.0)
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
