#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Silencers, screens and barriers measured where they stand.

ISO 11820:1996, ISO 11821:1997 and ISO 10847:1997 measure three different
things in the field and none of them prints a worked example. What they do
print is tables and thresholds, and what their equations offer is identities,
so the rows here are of three kinds and each says which.

**Printed tables and thresholds.** Table 1 of ISO 11820 and Tables 1 and 3 of
ISO 10847, cell by cell; the twenty installations of Figure 1 of ISO 11820 with
the area rule clause 9 gives each; the window and the repeat rules of
ISO 11821.

**Closed form.** The Sabine area of Equations (6), (10) and (12), the two
measurement distances of Equations (15) and (16), the gas density of Equation
(29), the temperature field correction of Equations (20) and (22), the boxed
background formula of ISO 11821 5.7 at the two ends of its window, and the
divergence rates definition 3.10 of ISO 10847 states.

**Algebraic identity.** The strongest oracle any of the three offers is in
ISO 10847: the indirect method reduces exactly to the direct one when the
receiver is of the same kind in both campaigns, and moves by exactly 6 dB when
it is not. Beside it are the source-normalisation invariance of the reference
position and the level-shift invariance of the two ISO 11820 losses.

**Three rules for one correction.** The three documents correct for the
background three different ways, and the rows say so: a stepped table that
takes off 0,5 dB at a 9 dB margin, a stepped table that takes off 1 dB at the
same margin, and the energy subtraction itself.
"""

from __future__ import annotations

import math

import numpy as np

import phonometry as ph
from phonometry.environment.propagation.barrier_in_situ import (
    ISO10847_BACKGROUND_CORRECTIONS_DB,
    RECEIVER_CORRECTIONS_DB,
    ReceiverType,
)
from phonometry.noise_control.silencer_in_situ import (
    INSTALLATION_CASES,
    ISO11820_BACKGROUND_CORRECTIONS_DB,
    ISO11820_SOUND_SPEED_M_S,
    SABINE_AREA_COEFFICIENT,
)

from ..registry import Outcome, count, numeric, record, register

_IN_SITU = "In-situ measurement of silencers, screens and barriers"

#: An octave spectrum to put the identities on, in decibels.
_BANDS = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
_SOURCE = np.array([95.0, 96.0, 97.0, 95.0, 92.0, 88.0])
_RECEIVER = np.array([70.0, 68.0, 65.0, 60.0, 55.0, 51.0])


@register(
    _IN_SITU,
    "ISO 11820:1996 Table 1",
    "The stepped background correction, dB to subtract, over the eight printed rows",
)
def _chk_iso11820_table_one() -> Outcome:
    printed = {
        "3 dB": 3.0,
        "4 dB": 2.0,
        "5 dB": 2.0,
        "6 dB": 1.0,
        "7 dB": 1.0,
        "8 dB": 1.0,
        "9 dB": 0.5,
        "10 dB": 0.5,
    }
    computed = {
        f"{margin} dB": float(
            ph.noise_control.silencer_background_correction_db([float(margin)])[0]
        )
        for margin in ISO11820_BACKGROUND_CORRECTIONS_DB
    }
    return record(printed, computed, unit="dB")


@register(
    _IN_SITU,
    "ISO 11820:1996 Table 1",
    "The printed table is a rounded version of the logarithmic subtraction "
    "and departs from it by under 0,35 dB",
)
def _chk_iso11820_table_against_the_formula() -> Outcome:
    margins = np.arange(3, 11, dtype=float)
    table = ph.noise_control.silencer_background_correction_db(margins)
    exact = -10.0 * np.log10(1.0 - 10.0 ** (-0.1 * margins))
    worst = float(np.max(np.abs(table - exact)))
    return numeric(
        0.0,
        worst,
        0.35,
        unit="dB",
        expected_label="under 0,35 dB over the eight rows",
        computed_label=f"largest departure {worst:.3f} dB",
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (19)",
    "The transmission loss is unmoved by a level shift common to both sides "
    "of the silencer",
)
def _chk_iso11820_level_shift_invariance() -> Outcome:
    plain = ph.noise_control.in_situ_transmission_loss(
        _SOURCE, _RECEIVER, source_area_m2=2.0, receiver_area_m2=1.0
    )
    shifted = ph.noise_control.in_situ_transmission_loss(
        _SOURCE + 6.5, _RECEIVER + 6.5, source_area_m2=2.0, receiver_area_m2=1.0
    )
    worst = float(np.max(np.abs(plain.loss_db - shifted.loss_db)))
    return numeric(
        0.0,
        worst,
        1e-12,
        unit="dB",
        computed_label=f"max absolute difference {worst:.3f} dB over 6 bands",
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 Eqs. (20) and (22)",
    "The temperature field correction is 5 lg of the ratio of the two "
    "absolute temperatures, and vanishes when they agree",
)
def _chk_iso11820_temperature_correction() -> Outcome:
    printed = {
        "20 C both sides": 0.0,
        "20 C and 200 C": 5.0 * math.log10(293.0 / 473.0),
    }
    computed = {
        "20 C both sides": ph.noise_control.temperature_field_correction_db(
            receiver_temperature_c=20.0, source_temperature_c=20.0
        ),
        "20 C and 200 C": ph.noise_control.temperature_field_correction_db(
            receiver_temperature_c=20.0, source_temperature_c=200.0
        ),
    }
    worst = max(abs(printed[k] - computed[k]) for k in printed)
    return numeric(0.0, worst, 1e-12, unit="dB")


@register(
    _IN_SITU,
    "ISO 11820:1996 Eqs. (6), (10) and (12)",
    "A quarter of the Sabine absorption as an area, 6 ln 10 V / (c T), at "
    "the printed c = 340 m/s",
)
def _chk_iso11820_sabine_area() -> Outcome:
    volume, time = 300.0, 1.2
    expected = SABINE_AREA_COEFFICIENT * volume / (ISO11820_SOUND_SPEED_M_S * time)
    computed = float(ph.noise_control.reverberant_surface_area_m2(volume, [time])[0])
    return numeric(expected, computed, 1e-9, unit="m2", places=4)


@register(
    _IN_SITU,
    "ISO 11820:1996 Eqs. (15) and (16)",
    "The upstream distance is 1,5 equivalent diameters and the downstream "
    "one is 12 sqrt(S_d) less 10 sqrt(S_f)",
)
def _chk_iso11820_measurement_distances() -> Outcome:
    printed = {
        "upstream, S_u = 0,25 m2": 1.5 * math.sqrt(4.0 * 0.25 / math.pi),
        "downstream, S_d = 0,25 m2 and S_f = 0,09 m2": 12.0 * 0.5 - 10.0 * 0.3,
    }
    computed = {
        "upstream, S_u = 0,25 m2": ph.noise_control.measurement_distance_upstream_m(
            0.25
        ),
        "downstream, S_d = 0,25 m2 and S_f = 0,09 m2": (
            ph.noise_control.measurement_distance_downstream_m(0.25, 0.09)
        ),
    }
    worst = max(abs(printed[k] - computed[k]) for k in printed)
    return numeric(0.0, worst, 1e-9, unit="m")


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (29)",
    "The gas density with the printed R/M = 287 for air and p_amb = 100 kPa",
)
def _chk_iso11820_gas_density() -> Outcome:
    expected = 100_000.0 / (287.0 * 293.0)
    computed = ph.noise_control.gas_density_kg_m3(temperature_c=20.0)
    return numeric(expected, computed, 1e-9, unit="kg/m3", places=4)


@register(
    _IN_SITU,
    "ISO 11820:1996 Figure 1 and 9.1.3",
    "The twenty installations, sixteen for transmission and four for "
    "insertion, with the area rule each of them takes",
)
def _chk_iso11820_installation_cases() -> Outcome:
    matches = 0
    for number, case in INSTALLATION_CASES.items():
        wanted_quantity = "transmission" if number <= 16 else "insertion"  # noqa: PLR2004 - Figure 1 splits there
        if case.quantity != wanted_quantity:
            continue
        if number <= 4:  # noqa: PLR2004 - the clause groups cases 1 to 4
            ok = "measurement surface" in case.source_area_rule
        elif number <= 8:  # noqa: PLR2004 - and cases 5 to 8
            ok = "one-quarter" in case.source_area_rule
        elif number <= 16:  # noqa: PLR2004 - and cases 9 to 16
            ok = "one-half" in case.source_area_rule
        elif number <= 18:  # noqa: PLR2004 - 17 and 18 name their run
            ok = "without the silencer" in case.source_area_rule
        else:
            ok = "aperture" in case.source_area_rule and (
                "open end" in case.receiver_area_rule
            )
        matches += int(ok)
    return count(matches, len(INSTALLATION_CASES), subject="installations")


@register(
    _IN_SITU,
    "ISO 11820:1996 9.1.5",
    "The permitted conversion folds three one-third-octave levels into "
    "their octave on the energy, and is not the fold of a level difference",
)
def _chk_iso11820_octave_fold() -> Outcome:
    thirds = [30.0, 30.0, 5.0]
    permitted = float(ph.noise_control.octave_levels_from_third_octave_db(thirds)[0])
    expected = 10.0 * math.log10(sum(10.0 ** (0.1 * v) for v in thirds))
    forbidden = float(ph.noise_control.octave_insertion_loss(thirds)[0])
    agrees = abs(permitted - expected) < 1e-9 and abs(permitted - forbidden) > 1.0
    return count(
        int(agrees),
        1,
        subject="readings of 9.1.5",
        expected_label="the energy fold, distinct from the ISO 11691 one",
    )


@register(
    _IN_SITU,
    "ISO 11821:1997 5.7",
    "The background correction at the two ends of the 6 dB to 10 dB window",
)
def _chk_iso11821_background_window() -> Outcome:
    printed = {"margin 6 dB": 1.2563, "margin 10 dB": 0.4576}
    computed = {
        "margin 6 dB": 80.0
        - float(ph.noise_control.background_corrected_level_db([80.0], [74.0])[0]),
        "margin 10 dB": 80.0
        - float(ph.noise_control.background_corrected_level_db([80.0], [70.0])[0]),
    }
    worst = max(abs(printed[k] - computed[k]) for k in printed)
    return numeric(
        0.0,
        worst,
        5e-4,
        unit="dB",
        expected_label="1,2563 dB at 6 dB and 0,4576 dB at 10 dB",
        computed_label=(
            f"{computed['margin 6 dB']:.4f} dB and {computed['margin 10 dB']:.4f} dB"
        ),
    )


@register(
    _IN_SITU,
    "ISO 11821:1997 5.5.2",
    "The four microphone distances are a quarter, a half, once and twice "
    "the screen height, with a floor of 1 m",
)
def _chk_iso11821_microphone_distances() -> Outcome:
    printed = {"h/4": 2.0, "h/2": 4.0, "h": 8.0, "2h": 16.0}
    computed = dict(
        zip(printed, ph.noise_control.microphone_distances_m(8.0).tolist(), strict=True)
    )
    return record(printed, computed, unit="m")


@register(
    _IN_SITU,
    "ISO 11821:1997 3.10 and 5.2.2",
    "The directivity index is the logarithmic mean of twelve positions less "
    "the position, so a position under the mean reads positive",
)
def _chk_iso11821_directivity_index() -> Outcome:
    levels = np.full(12, 80.0)
    levels[0] = 70.0
    index = ph.noise_control.directivity_index_db(levels)
    mean = 10.0 * math.log10((11.0 * 10.0**8.0 + 10.0**7.0) / 12.0)
    expected = mean - 70.0
    return numeric(expected, float(index[0]), 1e-9, unit="dB")


@register(
    _IN_SITU,
    "ISO 11821:1997 5.6.2.1 and clause 6",
    "The impulse repeat rules and the one uncertainty number the document prints",
)
def _chk_iso11821_thresholds() -> Outcome:
    printed = {"repeats": 3.0, "repeat again": 3.0, "invalid": 5.0, "deviation": 2.0}
    computed = {
        "repeats": float(ph.noise_control.IMPULSE_REPEATS),
        "repeat again": ph.noise_control.IMPULSE_REPEAT_DEVIATION_DB,
        "invalid": ph.noise_control.IMPULSE_INVALID_DEVIATION_DB,
        "deviation": ph.noise_control.ENGINEERING_STANDARD_DEVIATION_DB,
    }
    return record(printed, computed)


@register(
    _IN_SITU,
    "ISO 10847:1997 Table 3",
    "The background correction to add, over the two printed rows",
)
def _chk_iso10847_table_three() -> Outcome:
    printed = {
        "4 dB": -2.0,
        "5 dB": -2.0,
        "6 dB": -1.0,
        "7 dB": -1.0,
        "8 dB": -1.0,
        "9 dB": -1.0,
    }
    computed = {
        f"{margin} dB": float(
            ph.environment.barrier_background_correction_db([float(margin)])[0]
        )
        for margin in ISO10847_BACKGROUND_CORRECTIONS_DB
    }
    return record(printed, computed, unit="dB")


@register(
    _IN_SITU,
    "ISO 11820:1996 Table 1 / ISO 10847:1997 Table 3",
    "The two stepped tables disagree at a 9 dB margin, so they are two "
    "tables and not one helper",
)
def _chk_two_background_tables() -> Outcome:
    silencer = float(ph.noise_control.silencer_background_correction_db([9.0])[0])
    barrier = float(ph.environment.barrier_background_correction_db([9.0])[0])
    printed = {"ISO 11820 subtracts": 0.5, "ISO 10847 adds": -1.0}
    computed = {"ISO 11820 subtracts": silencer, "ISO 10847 adds": barrier}
    return record(printed, computed, unit="dB")


@register(
    _IN_SITU,
    "ISO 10847:1997 8.2.1 and 8.2.2",
    "The indirect method returns exactly what the direct one returns when "
    "the receiver is of the same kind in both campaigns",
)
def _chk_iso10847_methods_agree() -> Outcome:
    reference_before = np.array([70.0, 72.0, 74.0, 73.0, 70.0, 66.0])
    reference_after = reference_before + 1.5
    receiver_before = np.array([60.0, 62.0, 63.0, 62.0, 59.0, 55.0])
    receiver_after = receiver_before - np.array([3.0, 5.0, 8.0, 11.0, 14.0, 16.0]) + 1.5
    direct = ph.environment.measured_insertion_loss_direct(
        reference_before, reference_after, receiver_before, receiver_after
    )
    worst = 0.0
    kinds: tuple[ReceiverType, ...] = ("hemi_free_field", "reflecting_surface")
    for kind in kinds:
        indirect = ph.environment.measured_insertion_loss_indirect(
            reference_before,
            reference_after,
            receiver_before,
            receiver_after,
            receiver_type_before=kind,
            receiver_type_after=kind,
        )
        worst = max(
            worst,
            float(
                np.max(np.abs(indirect.insertion_loss_db - direct.insertion_loss_db))
            ),
        )
    return numeric(
        0.0,
        worst,
        1e-12,
        unit="dB",
        computed_label=f"max absolute difference {worst:.3f} dB over both receiver kinds",
    )


@register(
    _IN_SITU,
    "ISO 10847:1997 8.2.2",
    "Mixing a hemi-free-field receiver with a facade one moves the answer "
    "by exactly the 6 dB of the pressure doubling",
)
def _chk_iso10847_receiver_correction() -> Outcome:
    reference_before = np.array([70.0, 72.0, 74.0])
    reference_after = reference_before
    receiver_before = np.array([60.0, 62.0, 63.0])
    receiver_after = receiver_before - 10.0
    direct = ph.environment.measured_insertion_loss_direct(
        reference_before, reference_after, receiver_before, receiver_after
    )
    mixed = ph.environment.measured_insertion_loss_indirect(
        reference_before,
        reference_after,
        receiver_before,
        receiver_after,
        receiver_type_after="reflecting_surface",
    )
    shift = float(np.max(mixed.insertion_loss_db - direct.insertion_loss_db))
    return numeric(
        RECEIVER_CORRECTIONS_DB["reflecting_surface"], shift, 1e-12, unit="dB"
    )


@register(
    _IN_SITU,
    "ISO 10847:1997 8.2.1",
    "A source that changed output between the two campaigns is normalised "
    "away by the reference position",
)
def _chk_iso10847_source_normalisation() -> Outcome:
    reference_before = np.array([70.0, 72.0, 74.0])
    receiver_before = np.array([60.0, 62.0, 63.0])
    attenuation = np.array([5.0, 8.0, 11.0])
    plain = ph.environment.measured_insertion_loss_direct(
        reference_before,
        reference_before,
        receiver_before,
        receiver_before - attenuation,
    )
    louder = ph.environment.measured_insertion_loss_direct(
        reference_before,
        reference_before + 4.0,
        receiver_before,
        receiver_before - attenuation + 4.0,
    )
    worst = float(np.max(np.abs(plain.insertion_loss_db - louder.insertion_loss_db)))
    return numeric(
        0.0,
        worst,
        1e-12,
        unit="dB",
        computed_label=f"max absolute difference {worst:.3f} dB for a 4 dB source gain",
    )


@register(
    _IN_SITU,
    "ISO 10847:1997 Table 1",
    "The wind classes, with the upwind one existing only over short "
    "distances and read as negative",
)
def _chk_iso10847_wind_classes() -> Outcome:
    readings = {
        "+3 m/s": ph.environment.wind_class(3.0),
        "0 m/s": ph.environment.wind_class(0.0),
        "-3 m/s, long": ph.environment.wind_class(-3.0),
        "-3 m/s, short": ph.environment.wind_class(-3.0, short_distance=True),
    }
    printed = {
        "+3 m/s": "downwind",
        "0 m/s": "calm",
        "-3 m/s, long": None,
        "-3 m/s, short": "upwind",
    }
    matching = sum(1 for key in printed if readings[key] == printed[key])
    return count(matching, len(printed), subject="readings of Table 1")


@register(
    _IN_SITU,
    "ISO 10847:1997 6.3.1",
    "The short-distance ratio is strict at 0,1, and the after case needs "
    "both of its two inequalities",
)
def _chk_iso10847_short_distance() -> Outcome:
    at_the_ratio, _ = ph.environment.is_short_distance(
        source_height_m=1.0,
        receiver_height_m=1.0,
        barrier_height_m=4.0,
        source_to_barrier_m=10.0,
        barrier_to_receiver_m=10.0,
    )
    _, one_half_fails = ph.environment.is_short_distance(
        source_height_m=1.0,
        receiver_height_m=1.0,
        barrier_height_m=1.0,
        source_to_barrier_m=10.0,
        barrier_to_receiver_m=100.0,
    )
    agrees = at_the_ratio is False and one_half_fails is False
    return count(
        int(agrees),
        1,
        subject="readings of 6.3.1",
        expected_label="0,1 exactly is not short, and both halves must hold",
    )


@register(
    _IN_SITU,
    "ISO 10847:1997 7.2.2 and 8.1.2 a)",
    "The reference microphone clears the barrier top by 1,5 m, or takes the "
    "10 degree rule for a source under 15 m away",
)
def _chk_iso10847_geometry() -> Outcome:
    close = 10.0 * math.tan(math.atan(4.0 / 10.0) + math.radians(10.0))
    printed = {
        "clearance": 5.5,
        "10 degree rule": close,
        "hemi free field at 5 m": 10.0,
        "hemi free field at 20 m": 30.0,
    }
    computed = {
        "clearance": ph.environment.reference_microphone_height_m(4.0),
        "10 degree rule": ph.environment.reference_microphone_height_m(
            4.0, source_to_barrier_m=10.0
        ),
        "hemi free field at 5 m": ph.environment.hemi_free_field_distance_m(5.0),
        "hemi free field at 20 m": ph.environment.hemi_free_field_distance_m(20.0),
    }
    worst = max(abs(printed[k] - computed[k]) for k in printed)
    return numeric(0.0, worst, 1e-9, unit="m")


@register(
    _IN_SITU,
    "ISO 10847:1997 3.10",
    "The far field falls 6 dB per doubling for a point source and 3 dB for "
    "an incoherent line source",
)
def _chk_iso10847_divergence() -> Outcome:
    printed = {"point": 20.0 * math.log10(2.0), "line": 10.0 * math.log10(2.0)}
    computed = {
        "point": ph.environment.POINT_SOURCE_DIVERGENCE_DB,
        "line": ph.environment.LINE_SOURCE_DIVERGENCE_DB,
    }
    worst = max(abs(printed[k] - computed[k]) for k in printed)
    return numeric(
        0.0,
        worst,
        0.021,
        unit="dB",
        expected_label="6,02 dB and 3,01 dB, printed rounded to 6 and 3",
        computed_label="6 dB and 3 dB",
    )
