#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Audiometric test methods, and the earmuff on its acoustic test fixture.

ISO 8253-1:2010 prints the maximum permissible ambient levels of an
audiometric test room (Tables 2 and 4), the earphone attenuations that move
them (Table 3), and one worked uncertainty budget (Table A.2, u = 4,9 dB and
U = 10 dB). ISO 8253-2:2009 prints the ambient limits for sound field
audiometry (Table 2), the microphone requirements of the diffuse-field test
(Table 1) and the off-axis increases of Table B.1. ISO 4869-3:2007 prints its
own microphone table (Table 1), the front-to-random index of the fixture
(Table A.1), the isolation it asks of the fixture (5.1.4) and a typical
uncertainty budget (Table B.1, u = 1,3 dB and U = 2,6 dB). The rows below read
each from the library.

The threshold rules of ISO 8253-1 (6.2.4.2, 6.2.4.3, 6.3.5 and 7.5) and the
cautions of 6.2.3.2 print no numeric example; their rows feed each rule a
series whose answer follows from the clause's words alone, and pin it. A
series whose answer would rest on a convention the clause does not state,
such as the tie of a mean halfway between two 5 dB steps, is left to the unit
tests, where the convention is named as the library's. 8.4 prints the average
vibrotactile levels, which are read as a table.

Oracles: BS EN ISO 8253-1:2010, printed folio n on PDF page n + 8 (6.2.3.2 on
folio 9, 8.4 on folio 13, Tables 2 to 4 on folios 17 to 19, Annex A on folios
23 to 27); ISO 8253-2:2009, printed
folio n on PDF page n + 6 (Table 1 on folio 7, Table 2 on folio 9, Table B.1
on folio 15); ISO 4869-3:2007, printed folio n on PDF page n + 4 (5.1.4 and
Table 1 on folio 4, Table A.1 on folio 9, Table B.1 on folio 11). Every value
was read on the rasterized page.

Two printed inconsistencies of these oracles are recorded in
``docs/ERRATA.md`` and pinned here: ISO 8253-2 announces Table B.1 from 200 Hz
and prints its rows from 125 Hz, and ISO 4869-3 Table 1 writes "> 5" where
5.2.2 asks for "at least 5 dB".
"""

from __future__ import annotations

import math

import numpy as np
import reference_data as ref

from phonometry import hearing

from ..registry import Outcome, count, record, register

_ISO8253 = "Audiometric test methods (ISO 8253)"
_ISO4869_3 = "Earmuff insertion loss on a test fixture (ISO 4869-3)"


def _cells(library: np.ndarray, printed: tuple[float, ...]) -> tuple[int, int]:
    """``(matching, total)`` of the cells a table prints, NaN for a dash.

    :param library: The library's column.
    :param printed: The printed column, NaN where the table prints a dash.
    :return: The count of cells that agree exactly, and of cells compared.
    """
    got = np.asarray(library, dtype=np.float64)
    want = np.asarray(printed, dtype=np.float64)
    if got.shape != want.shape:
        return 0, want.size
    same = np.isclose(got, want, rtol=0.0, atol=1e-12) | (
        np.isnan(got) & np.isnan(want)
    )
    return int(np.sum(same)), want.size


def _table(
    library: dict[float, np.ndarray] | dict[str, np.ndarray],
    printed: dict[float, tuple[float, ...]] | dict[str, tuple[float, ...]],
    subject: str,
) -> Outcome:
    """A count over every cell of a printed table.

    :param library: The library's table, keyed as the page keys it.
    :param printed: The transcription.
    :param subject: What is counted, for the report.
    :return: The outcome.
    """
    matching = total = 0
    for key, column in printed.items():
        got, n = _cells(library[key], column)  # type: ignore[index]
        matching += got
        total += n
    return count(matching, total, subject=subject)


@register(
    _ISO8253,
    "ISO 8253-1:2010 Table 2",
    "Maximum permissible ambient levels for air conduction, three test ranges",
)
def _chk_table_2() -> Outcome:
    """25 bands from 31,5 Hz to 8 kHz for 125 Hz, 250 Hz and 500 Hz."""
    return _table(
        dict(hearing.AIR_CONDUCTION_AMBIENT_LIMITS_DB),
        ref.ISO8253_1_TABLE_2,
        "cells of Table 2",
    )


@register(
    _ISO8253,
    "ISO 8253-1:2010 Table 3",
    "Average sound attenuation of the supra-aural, ER-3A and HDA 200 earphones",
)
def _chk_table_3() -> Outcome:
    """72 printed cells and the three dashes of the HDA 200 below 63 Hz."""
    return _table(
        dict(hearing.EARPHONE_ATTENUATION_DB), ref.ISO8253_1_TABLE_3, "cells of Table 3"
    )


@register(
    _ISO8253,
    "ISO 8253-1:2010 Table 4",
    "Maximum permissible ambient levels for bone conduction, two test ranges",
)
def _chk_table_4() -> Outcome:
    """25 bands from 31,5 Hz to 8 kHz for 125 Hz and 250 Hz."""
    return _table(
        dict(hearing.BONE_CONDUCTION_AMBIENT_LIMITS_DB),
        ref.ISO8253_1_TABLE_4,
        "cells of Table 4",
    )


@register(
    _ISO8253,
    "ISO 8253-1:2010 11.1",
    "The limit at 1 kHz with each adjustment of 11.1 and the NOTE to Table 2",
)
def _chk_adjustments() -> Outcome:
    """23 dB; + (37 - 15) dB for the ER-3A; + 8 dB for +5 dB; + 10 dB of HL."""
    k = ref.ISO8253_1_BANDS_HZ.index(1000.0)
    base = ref.ISO8253_1_TABLE_2[125.0][k]
    extra = ref.ISO8253_1_TABLE_3["ER-3A"][k] - ref.ISO8253_1_TABLE_3["supra-aural"][k]
    expected = {
        "supra-aural": base,
        "ER-3A": base + extra,
        "shift +5 dB": base + ref.ISO8253_1_RELAXED_ALLOWANCE_DB,
        "lowest HL 10 dB": base + 10.0,
    }
    computed = {
        "supra-aural": hearing.ambient_noise_limits()[k],
        "ER-3A": hearing.ambient_noise_limits(earphone="ER-3A")[k],
        "shift +5 dB": hearing.ambient_noise_limits(allowed_threshold_shift_db=5.0)[k],
        "lowest HL 10 dB": hearing.ambient_noise_limits(lowest_hearing_level_db=10.0)[
            k
        ],
    }
    return record(expected, computed, unit="dB")


@register(
    _ISO8253,
    "ISO 8253-1:2010 A.3.3",
    "Audiometer standard uncertainty, air conduction up to 4 kHz, 5 dB steps",
)
def _chk_a33() -> Outcome:
    """sqrt((3/sqrt 3)^2 + (2,5/sqrt 3)^2) dB, which A.3.3 prints as 2,3 dB."""
    budget = hearing.audiometric_uncertainty(1000.0)
    return record(
        {"u(delta_eq)": ref.ISO8253_1_A33_EQUIPMENT_DB},
        {"u(delta_eq)": round(budget.equipment_db, 1)},
        unit="dB",
    )


@register(
    _ISO8253,
    "ISO 8253-1:2010 A.3.4",
    "Transducer standard uncertainty up to and above 4 kHz",
)
def _chk_a34() -> Outcome:
    """sqrt(1,5^2 + 2,5^2) = 2,9 dB and sqrt(2,5^2 + 3^2) = 3,9 dB."""
    low, high = ref.ISO8253_1_A34_TRANSDUCER_DB
    return record(
        {"up to 4 kHz": low, "above 4 kHz": high},
        {
            "up to 4 kHz": round(
                hearing.audiometric_uncertainty(4000.0).transducer_db, 1
            ),
            "above 4 kHz": round(
                hearing.audiometric_uncertainty(8000.0).transducer_db, 1
            ),
        },
        unit="dB",
    )


@register(
    _ISO8253,
    "ISO 8253-1:2010 Table A.2",
    "The four components, combined and expanded uncertainty, air conduction "
    "below 4 kHz, no masking",
)
def _chk_table_a2() -> Outcome:
    """2,5, 2,3, 2,9 and 2,0 dB; u = 4,9 dB and U = 10 dB, rounded to the
    nearest full decibel (A.6).
    """
    budget = hearing.audiometric_uncertainty(1000.0)
    names = ("u1 L'_HT", "u2 delta_eq", "u3 delta_tr", "u4 delta_n")
    expected = dict(zip(names, ref.ISO8253_1_TABLE_A2_COMPONENTS_DB, strict=True))
    computed = {
        name: round(value, 1)
        for name, value in zip(names, budget.components_db[:4], strict=True)
    }
    expected |= {
        "u": ref.ISO8253_1_TABLE_A2_U_DB,
        "U": ref.ISO8253_1_TABLE_A2_EXPANDED_DB,
    }
    computed |= {
        "u": round(budget.combined_db, 1),
        "U": float(round(budget.expanded_db)),
    }
    return record(expected, computed, unit="dB")


@register(
    _ISO8253,
    "ISO 8253-1:2010 6.2.4.2",
    "Ascending method: three responses at one level out of five ascents",
)
def _chk_ascending() -> Outcome:
    """Ascents ending at 35, 30, 30, 35 and 30 dB: 30 dB, answered 3 times of 5."""
    result = hearing.ascending_method_threshold([35.0, 30.0, 30.0, 35.0, 30.0])
    return record({"threshold": 30.0}, {"threshold": result.threshold_db}, unit="dB")


@register(
    _ISO8253,
    "ISO 8253-1:2010 6.2.4.3",
    "Bracketing method: mean of the two averages to the nearest 5 dB step",
)
def _chk_bracketing() -> Outcome:
    """Ascents 30, 30, 35 dB and descents 35, 35, 35 dB: averages 31,67 dB and
    35 dB, mean 33,33 dB, whose nearest 5 dB step is 35 dB. The mean is clear
    of a tie, so the answer needs no rule the clause does not give.
    """
    result = hearing.bracketing_method_threshold([30, 30, 35], [35, 35, 35])
    return record(
        {"mean": 33.333, "threshold": 35.0},
        {"mean": round(result.mean_db, 3), "threshold": result.threshold_db},
        unit="dB",
    )


@register(
    _ISO8253,
    "ISO 8253-1:2010 6.3.5",
    "Automatic recording: first reversal and small excursions dropped, rounded up",
)
def _chk_automatic() -> Outcome:
    """Peaks 31, 30,5, 30 dB and valleys 20 dB: 25,25 dB, rounded up to 26 dB.

    The first reversal is dropped, and so are the three that bound the two
    excursions of 1 dB near the end. A mean a quarter of a decibel above a
    whole one tells "rounded up" from rounding to the nearest, which would
    give 25 dB.
    """
    result = hearing.automatic_audiometry_threshold(
        [30, 20, 31, 20, 30.5, 20, 30, 20, 31, 30, 31, 20]
    )
    return record(
        {"peaks": 30.5, "valleys": 20.0, "mean": 25.25, "threshold": 26.0},
        {
            "peaks": round(float(np.mean(result.peaks_db)), 9),
            "valleys": round(float(np.mean(result.valleys_db)), 9),
            "mean": round(result.mean_db, 9),
            "threshold": result.threshold_db,
        },
        unit="dB",
    )


@register(
    _ISO8253,
    "ISO 8253-1:2010 7.5",
    "Sweep-frequency audiometry: three nearest peaks and valleys, rounded",
)
def _chk_sweep() -> Outcome:
    """Peaks at 30,6 dB and valleys at 20 dB about 1 kHz: 25,3 dB, then 25 dB."""
    freqs = np.geomspace(250.0, 8000.0, 24)
    levels = np.where(np.arange(24) % 2 == 0, 30.6, 20.0)
    result = hearing.sweep_audiometry_threshold(freqs, levels, frequencies=[1000.0])
    return record(
        {"mean": 25.3, "threshold": 25.0},
        {
            "mean": round(float(result.mean_db[0]), 9),
            "threshold": result.threshold_db[0],
        },
        unit="dB",
    )


@register(
    _ISO8253,
    "ISO 8253-1:2010 6.2.3.2, Step 3",
    "Repeat at 1 kHz: 5 dB or less agrees, 10 dB or more retests further",
)
def _chk_retest() -> Outcome:
    """25 dB against 30 and 20 dB agrees; against 35 and 15 dB it retests."""
    agree, retest = (
        ref.ISO8253_1_RETEST_AGREEMENT_DB,
        ref.ISO8253_1_RETEST_DISAGREEMENT_DB,
    )
    cases = [
        (hearing.check_retest_agreement(25.0, 25.0 + agree), True, False),
        (hearing.check_retest_agreement(25.0, 25.0 - agree), True, False),
        (hearing.check_retest_agreement(25.0, 25.0 + retest), False, True),
        (hearing.check_retest_agreement(25.0, 25.0 - retest), False, True),
    ]
    matching = sum(
        int(check.passes == passes and check.retest_further_frequencies == back)
        for check, passes, back in cases
    )
    return count(matching, len(cases), subject="repeats judged as Step 3 words it")


@register(
    _ISO8253,
    "ISO 8253-1:2010 6.2.3.2",
    "Cross-hearing: a hearing level of 40 dB or more calls for caution",
)
def _chk_cross_hearing() -> Outcome:
    """35 dB is below it; 40 dB and 45 dB are 40 dB or more."""
    at = ref.ISO8253_1_CROSS_HEARING_DB
    levels = [at - 5.0, at, at + 5.0]
    flags = hearing.audiogram_cautions(
        [500.0, 1000.0, 2000.0], air_conduction_db=levels
    ).cross_hearing
    matching = sum(
        int(bool(flag) == (level >= at))
        for flag, level in zip(flags, levels, strict=True)
    )
    return count(matching, len(levels), subject="levels judged as 6.2.3.2 words it")


@register(
    _ISO8253,
    "ISO 8253-1:2010 8.4",
    "Average vibrotactile threshold, mastoid and forehead placement",
)
def _chk_vibrotactile() -> Outcome:
    """40, 60 and 70 dB at 250 Hz, 500 Hz and 1 kHz; about 10 dB lower forehead.

    Both placements are read through ``audiogram_cautions``, which is where the
    levels are applied.
    """
    printed = ref.ISO8253_1_VIBROTACTILE_DB
    freqs = list(printed)
    offset = ref.ISO8253_1_FOREHEAD_OFFSET_DB
    expected: dict[str, float] = {}
    computed: dict[str, float] = {}
    for placement, lower in (("mastoid", 0.0), ("forehead", offset)):
        levels = hearing.audiogram_cautions(
            freqs, bone_conduction_db=[0.0] * len(freqs), vibrator_placement=placement
        ).vibrotactile_levels_db
        for f, level in zip(freqs, levels, strict=True):
            expected[f"{f:g} Hz {placement}"] = printed[f] - lower
            computed[f"{f:g} Hz {placement}"] = float(level)
    return record(expected, computed, unit="dB")


@register(
    _ISO8253,
    "ISO 8253-2:2009 Table 2",
    "Maximum permissible ambient levels for sound field audiometry, to 12,5 kHz",
)
def _chk_sound_field_table_2() -> Outcome:
    """27 bands from 31,5 Hz to 12,5 kHz for 125 Hz and 250 Hz."""
    return _table(
        dict(hearing.SOUND_FIELD_AMBIENT_LIMITS_DB),
        ref.ISO8253_2_TABLE_2,
        "cells of Table 2",
    )


@register(
    _ISO8253,
    "ISO 8253-2:2009 Table 2, footnote a",
    "Derived from ISO 8253-1 for binaural listening; the cells equal Table 4 "
    "less 3 dB, an offset the library reads off the two tables",
)
def _chk_binaural_derivation() -> Outcome:
    """Every shared cell, 31,5 Hz to 8 kHz, is the bone-conduction limit less 3 dB.

    Footnote a says only that the limits are derived from ISO 8253-1 for
    binaural listening; the 3 dB is what the two printed tables show when laid
    side by side, not a figure the footnote prints.
    """
    shared = len(ref.ISO8253_1_BANDS_HZ)
    derived = {
        key: tuple(v - ref.ISO8253_2_BINAURAL_OFFSET_DB for v in column)
        for key, column in ref.ISO8253_1_TABLE_4.items()
    }
    library = {
        key: np.asarray(column)[:shared]
        for key, column in hearing.SOUND_FIELD_AMBIENT_LIMITS_DB.items()
    }
    return _table(library, derived, "cells equal to Table 4 less 3 dB")


@register(
    _ISO8253,
    "ISO 8253-2:2009 Table B.1",
    "Increase at the nearer ear at 45 and 90 degrees, 125 Hz to 12,5 kHz",
)
def _chk_table_b1() -> Outcome:
    """24 rows, the first two below the 200 Hz the text announces (an erratum)."""
    matching, total = 0, 0
    if hearing.INCIDENCE_CORRECTION_FREQUENCIES_HZ == ref.ISO8253_2_TABLE_B1_HZ:
        for angle, column in ref.ISO8253_2_TABLE_B1.items():
            got, n = _cells(
                hearing.incidence_correction(
                    ref.ISO8253_2_TABLE_B1_HZ, incidence_angle_deg=angle
                ),
                column,
            )
            matching += got
            total += n
    else:
        total = 2 * len(ref.ISO8253_2_TABLE_B1_HZ)
    return count(matching, total, subject="cells of Table B.1")


@register(
    _ISO8253,
    "ISO 8253-2:2009 Table 1",
    "Allowable field variation by the microphone's front-to-random index",
)
def _chk_diffuse_table_1() -> Outcome:
    """5 dB and more allow 5 dB, 4,5 dB allows 4,5 dB, 4 dB allows 4 dB."""
    expected = {
        f"index {index:g} dB": allowed for index, allowed in ref.ISO8253_2_TABLE_1
    }
    six = dict.fromkeys(("front", "back", "left", "right", "up", "down"), [0.0])
    computed = {
        f"index {index:g} dB": float(
            hearing.check_diffuse_sound_field(
                six,
                [0.0],
                directional_levels_db=[[0.0], [1.0]],
                front_to_random_index_db=index,
                frequencies=[1000.0],
            ).allowable_variation_db[0]
        )
        for index, _allowed in ref.ISO8253_2_TABLE_1
    }
    return record(expected, computed, unit="dB")


@register(
    _ISO8253,
    "ISO 8253-2:2009 5.2 c) and 5.4 c)",
    "Axial level difference the inverse distance law gives at 1 m (closed "
    "form; the standard prints no value)",
)
def _chk_inverse_distance() -> Outcome:
    """20 lg(1,15/0,85) = 2,626 dB at 0,15 m, 20 lg(1,1/0,9) = 1,743 dB at 0,10 m.

    5.2 c) and 5.4 c) name the law and print no number, so the expected side
    is the two values worked out by hand from it, to 0,001 dB.
    """
    four = dict.fromkeys(("left", "right", "up", "down"), [0.0])
    common = {
        "front_levels_db": [0.0],
        "back_levels_db": [0.0],
        "frequencies": [1000.0],
    }
    free = hearing.check_free_sound_field(
        four, [0.0], loudspeaker_distance_m=1.0, **common
    )
    quasi = hearing.check_quasi_free_sound_field(
        four, [0.0], loudspeaker_distance_m=1.0, **common
    )
    return record(
        {"free": 2.626, "quasi-free": 1.743},
        {
            "free": round(free.inverse_distance_difference_db, 3),
            "quasi-free": round(quasi.inverse_distance_difference_db, 3),
        },
        unit="dB",
    )


@register(
    _ISO4869_3,
    "ISO 4869-3:2007 Table B.1 and B.4",
    "Combined and expanded uncertainty of the typical budget",
)
def _chk_4869_3_budget() -> Outcome:
    """u = sqrt(0,25 + 1 + 0,09 + 0,25 + 0,04) = 1,3 dB, U = 2u = 2,6 dB."""
    budget = hearing.EARMUFF_INSERTION_LOSS_UNCERTAINTY
    return record(
        {"u": ref.ISO4869_3_TABLE_B1_U_DB, "U": ref.ISO4869_3_B4_EXPANDED_DB},
        {"u": round(budget.combined_db, 1), "U": round(budget.expanded_db, 1)},
        unit="dB",
    )


@register(
    _ISO4869_3,
    "ISO 4869-3:2007 5.2.2, Table 1",
    "Allowable field variation, read with the text for an index of 5 dB",
)
def _chk_4869_3_table_1() -> Outcome:
    """5 dB allows 5 dB (the text's 'at least 5 dB'), 4,5 dB allows 4 dB."""
    six = dict.fromkeys(("front", "back", "left", "right", "up", "down"), [0.0])
    computed = {
        f"index {index:g} dB": float(
            hearing.check_random_incidence_field(
                six,
                [0.0],
                directional_levels_db=[[0.0], [1.0]],
                front_to_random_index_db=index,
                frequencies=[1000.0],
            ).allowable_variation_db[0]
        )
        for index in (5.0, 4.5, 4.0)
    }
    return record(
        {"index 5 dB": 5.0, "index 4.5 dB": 4.0, "index 4 dB": 4.0},
        computed,
        unit="dB",
    )


@register(
    _ISO4869_3,
    "ISO 4869-3:2007 Table A.1",
    "Front-to-random index of the fixture, and the bands it may test itself",
)
def _chk_4869_3_table_a1() -> Outcome:
    """13 cells; at least 4 dB at 1,25 kHz to 3,15 kHz, 6,3 kHz and 8 kHz."""
    library = hearing.ATF_FRONT_TO_RANDOM_INDEX_DB
    matching = sum(
        1
        for f, index in ref.ISO4869_3_TABLE_A1.items()
        if f in library and math.isclose(library[f], index, abs_tol=1e-12)
    )
    suitable = [f for f, index in library.items() if index >= 4.0]
    fits = suitable == [1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 6300.0, 8000.0]
    total = len(ref.ISO4869_3_TABLE_A1) + 1
    return count(
        matching + int(fits), total, subject="cells of Table A.1 and its suitable bands"
    )


@register(
    _ISO4869_3,
    "ISO 4869-3:2007 5.1.4",
    "Least acoustic isolation of the fixture in each band, 63 Hz to 8 kHz",
)
def _chk_4869_3_isolation() -> Outcome:
    """50 dB to 250 Hz, 65 dB from 315 Hz to 4 kHz, 55 dB above."""
    freqs = np.asarray(hearing.EARMUFF_TEST_BANDS_HZ)
    required = hearing.verify_fixture_isolation(
        np.full(freqs.size, 100.0), np.zeros(freqs.size)
    ).required_db
    matching = 0
    for first, last, least in ref.ISO4869_3_ISOLATION:
        band = (freqs >= first) & (freqs <= last)
        matching += int(np.sum(np.isclose(required[band], least)))
    return count(matching, freqs.size, subject="bands of 5.1.4")
