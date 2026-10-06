#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound from service equipment and activities in buildings (ISO/DIS 16032:2023).

The engineering method of ISO 16032, from the draft of its second edition,
ISO/DIS 16032:2023, read in its German publication E DIN EN ISO 16032:2023-05
(prEN ISO 16032:2023, German and English text). The draft is the only text of
the revision there is; it is cited as a draft throughout.

The draft prints no worked example, so these rows stand on the numbers it does
print and on closed forms a reader can check by hand. Printed: the 2,2 dB a
4 dB background difference gives (Clause 9, folio 10, PDF page 48), Table A.1
(folio 12, PDF page 50) and Table 2 (folio 10, PDF page 48). Closed forms: a
reverberation time twice the reference, an equivalent absorption area of
16 m² normalized to the 10 m² reference, a flat spectrum and its single
numbers rounded to whole decibels, the thresholds of Clause 9 met by
decimal levels, of the position
ladder of 7.4.1, of every distance and height of 7.3 and of the corner height,
preferred wall distance and 0,2 m from obstacles of 7.2, and the additional
position of 7.9. The on-site checks are held to the limits the draft prints,
each met exactly and missed: the 0,5 dB calibration deviation of Clause 5
(folio 5, PDF page 43), the 30 s background of 7.6 (folio 8, PDF page 46),
the 2 dB of the NOTE to 7.8 (folio 9, PDF page 47), and the 10 min to 15 min,
10 dB and 5 dB of Clause 9 (folio 10, PDF page 48).

Table A.1 carries a printed defect, registered in ``docs/ERRATA.md``: the
one-third-octave C-weighting reads -5 dB at 25 Hz and 0 dB from 1 600 Hz to
10 000 Hz, against the -4,4 dB and -0,1 dB to -4,4 dB of IEC 61672-1, and
against the draft's own octave column at 2 000, 4 000 and 8 000 Hz. The row on
that column says which cells the library takes from the print and which from
IEC 61672-1:2013 Table 3.
"""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from reference_data import service_equipment as ref

from phonometry import building
from phonometry.filters.weighting_compliance import _WEIGHTING_TABLE3

from ..registry import Outcome, count, numeric, register

_DOMAIN = "Service-equipment sound in buildings (ISO/DIS 16032:2023)"
_DRAFT = "ISO/DIS 16032:2023"

_THIRD = np.array([row[0] for row in ref.ISO16032_TABLE_A1_THIRD])
_OCTAVE = np.array([row[0] for row in ref.ISO16032_TABLE_A1_OCTAVE])


def _flat(level: float) -> np.ndarray:
    return np.full((3, _THIRD.size), level)


@register(_DOMAIN, f"{_DRAFT} Clause 9", "Correction for a background 4 dB below")
def _chk_background_four_db() -> Outcome:
    # "A difference of 4 dB corresponds to a correction value of 2,2 dB."
    difference, printed = ref.ISO16032_BACKGROUND_LIMIT_DB
    res = building.service_equipment_background_correction([50.0], [50.0 - difference])
    return numeric(printed, float(res.correction_db[0]), 0.05, unit="dB", places=2)


@register(_DOMAIN, f"{_DRAFT} Clause 9", "Correction held at 2,2 dB below 4 dB")
def _chk_background_limited() -> Outcome:
    # Below 4 dB the correction "shall be limited to 2,2 dB": a background 1 dB
    # below, level with and 5 dB above the measured band all take 2,2 dB.
    res = building.service_equipment_background_correction(
        [50.0, 50.0, 50.0], [49.0, 50.0, 55.0]
    )
    held = int(np.count_nonzero(np.abs(res.correction_db - 2.2) <= 1e-12))
    return count(held, 3, subject="bands held at 2,2 dB")


@register(
    _DOMAIN, f"{_DRAFT} Clause 9", "Thresholds of 10 dB and 4 dB met by decimal levels"
)
def _chk_background_thresholds() -> Outcome:
    # A band 10,0 dB above its background is not corrected ("10 dB or more
    # below"), and one 4,0 dB above is corrected, not held ("less than 4 dB").
    # Read on levels given to 0,1 dB, whose differences are a hair off in
    # binary: 20,4 - 10,4 and 32,3 - 28,3.
    res = building.service_equipment_background_correction([20.4, 32.3], [10.4, 28.3])
    matching = sum(
        got == wanted
        for got, wanted in zip(res.regime, ("none", "corrected"), strict=True)
    )
    return count(matching, 2, subject="bands placed as Clause 9 reads")


@register(
    _DOMAIN,
    f"{_DRAFT} Clause 9, Formulae (7) to (9)",
    "Correction from 4 dB to 10 dB is the energy subtraction",
)
def _chk_background_formula() -> Outcome:
    # L = L1 - K with K = -10 lg(1 - 10^(-0,1 dL)) is 10 lg(10^(L1/10) -
    # 10^(L2/10)); at 10 dB or more nothing is corrected.
    l1 = np.array([50.0, 50.0, 50.0, 50.0])
    l2 = np.array([46.0, 43.0, 40.1, 40.0])
    res = building.service_equipment_background_correction(l1, l2)
    subtracted = 10.0 * np.log10(10.0 ** (0.1 * l1) - 10.0 ** (0.1 * l2))
    expected = np.where(l1 - l2 >= 10.0, l1, subtracted)
    worst = float(np.max(np.abs(res.corrected_db - expected)))
    return numeric(0.0, worst, 1e-9, unit="dB", places=6)


@register(
    _DOMAIN, f"{_DRAFT} Annex A, Table A.1", "A-weighting, one-third-octave and octave"
)
def _chk_table_a1_a() -> Outcome:
    table = building.SERVICE_EQUIPMENT_WEIGHTING
    matching = sum(
        abs(table["third"]["A"][f] - a) <= 1e-12
        for f, a, _ in ref.ISO16032_TABLE_A1_THIRD
    ) + sum(
        abs(table["octave"]["A"][f] - a) <= 1e-12
        for f, a, _ in ref.ISO16032_TABLE_A1_OCTAVE
    )
    total = len(ref.ISO16032_TABLE_A1_THIRD) + len(ref.ISO16032_TABLE_A1_OCTAVE)
    return count(matching, total, subject="A-weighting cells of Table A.1")


@register(
    _DOMAIN,
    f"{_DRAFT} Annex A, Table A.1 against IEC 61672-1:2013 Table 3",
    "C-weighting: printed cells kept, misprinted cells from IEC 61672-1",
)
def _chk_table_a1_c() -> Outcome:
    table = building.SERVICE_EQUIPMENT_WEIGHTING
    iec = {row[0]: row[2] for row in _WEIGHTING_TABLE3}
    defect = set(ref.ISO16032_TABLE_A1_C_DEFECT_HZ)
    matching = 0
    for f, _, printed in ref.ISO16032_TABLE_A1_THIRD:
        wanted = iec[f] if f in defect else printed
        matching += abs(table["third"]["C"][f] - wanted) <= 1e-12
    for f, _, printed in ref.ISO16032_TABLE_A1_OCTAVE:
        matching += abs(table["octave"]["C"][f] - printed) <= 1e-12
    total = len(ref.ISO16032_TABLE_A1_THIRD) + len(ref.ISO16032_TABLE_A1_OCTAVE)
    return count(
        matching,
        total,
        subject="C-weighting cells",
        expected_label=(
            f"{total}/{total} C-weighting cells: {total - len(defect)} as printed, "
            f"{len(defect)} from IEC 61672-1"
        ),
    )


@register(
    _DOMAIN, f"{_DRAFT} Clause 10, Table 2", "Reproducibility standard deviations"
)
def _chk_table_2() -> Outcome:
    band_table = building.SERVICE_EQUIPMENT_REPRODUCIBILITY
    matching = 0
    total = 0
    for thirds, octaves, sigma in ref.ISO16032_TABLE_2_BANDS:
        for f in thirds:
            matching += abs(band_table["third"][f] - sigma) <= 1e-12
        for f in octaves:
            matching += abs(band_table["octave"][f] - sigma) <= 1e-12
        total += len(thirds) + len(octaves)
    for weighting, sigma in ref.ISO16032_TABLE_2_WEIGHTED:
        matching += (
            abs(building.SERVICE_EQUIPMENT_WEIGHTED_REPRODUCIBILITY[weighting] - sigma)
            <= 1e-12
        )
        total += 1
    return count(matching, total, subject="cells of Table 2")


@register(
    _DOMAIN,
    f"{_DRAFT} Formula (1) and 7.5",
    "Band average of three readings, to 0,1 dB",
)
def _chk_average() -> Outcome:
    readings = np.repeat(np.array([[40.0], [43.0], [46.0]]), _THIRD.size, axis=1)
    res = building.service_equipment_level(readings, _THIRD, quantity="eq")
    exact = 10.0 * math.log10((10.0**4.0 + 10.0**4.3 + 10.0**4.6) / 3.0)
    return numeric(
        math.floor(exact * 10.0 + 0.5) / 10.0,
        float(res.average_db[0]),
        1e-9,
        unit="dB",
        places=2,
    )


@register(
    _DOMAIN,
    f"{_DRAFT} Formula (5) and 7.7",
    "Standardization by T = 2 T0 in 50 Hz to 5 000 Hz (octaves 63 Hz to 4 000 Hz) only",
)
def _chk_standardization() -> Outcome:
    # 10 lg 2 off the bands 7.7 standardizes, nothing off the others, in
    # one-third octaves and in octaves.
    worst = 0.0
    widths: tuple[tuple[Literal["third", "octave"], np.ndarray], ...] = (
        ("third", _THIRD),
        ("octave", _OCTAVE),
    )
    for band, freqs in widths:
        res = building.service_equipment_level(
            np.full((3, freqs.size), 40.0),
            freqs,
            quantity="eq",
            band=band,
            reverberation_time_s=np.full(freqs.size, 1.0),
        )
        assert res.standardized_db is not None
        low, high = (50.0, 5000.0) if band == "third" else (63.0, 4000.0)
        inside = (freqs >= low) & (freqs <= high)
        expected = np.where(inside, 40.0 - 10.0 * math.log10(2.0), 40.0)
        worst = max(worst, float(np.max(np.abs(res.standardized_db - expected))))
    return numeric(0.0, worst, 1e-9, unit="dB", places=6)


@register(
    _DOMAIN,
    f"{_DRAFT} Formula (6)",
    "Normalization of an equivalent absorption area of 16 m² to A0 = 10 m² at 1 kHz",
)
def _chk_normalization() -> Outcome:
    # T = 0,5 s in V = 50 m³ is A = 0,16 V / T = 16 m², so Formula (6),
    # L_n = L - 10 lg(A0 T / (0,16 V)), adds 10 lg(16/10) = 2,04 dB to a
    # 40 dB band: 42,04 dB, worked by hand.
    res = building.service_equipment_level(
        _flat(40.0),
        _THIRD,
        quantity="eq",
        reverberation_time_s=np.full(_THIRD.size, 0.5),
        volume_m3=50.0,
    )
    assert res.normalized_db is not None
    at_1_khz = float(res.normalized_db[_THIRD == 1000.0][0])
    return numeric(42.0412, at_1_khz, 5e-5, unit="dB", places=4)


@register(
    _DOMAIN,
    f"{_DRAFT} Formula (2) and 7.8",
    "LA,eq of a flat 40 dB spectrum over 50 Hz to 5 000 Hz",
)
def _chk_a_weighted() -> Outcome:
    res = building.service_equipment_level(_flat(40.0), _THIRD, quantity="eq")
    a = building.SERVICE_EQUIPMENT_WEIGHTING["third"]["A"]
    bands = [f for f in _THIRD if 50.0 <= f <= 5000.0]
    expected = 10.0 * math.log10(sum(10.0 ** (0.1 * (40.0 + a[f])) for f in bands))
    return numeric(expected, res.unrounded_ratings["LA,eq"], 1e-9, unit="dB", places=4)


@register(
    _DOMAIN,
    f"{_DRAFT} Formula (3) and 7.8",
    "LC,eq of a flat 40 dB spectrum over 25 Hz to 10 000 Hz",
)
def _chk_c_weighted() -> Outcome:
    res = building.service_equipment_level(_flat(40.0), _THIRD, quantity="eq")
    c = building.SERVICE_EQUIPMENT_WEIGHTING["third"]["C"]
    expected = 10.0 * math.log10(sum(10.0 ** (0.1 * (40.0 + c[f])) for f in _THIRD))
    return numeric(expected, res.unrounded_ratings["LC,eq"], 1e-9, unit="dB", places=4)


@register(_DOMAIN, f"{_DRAFT} 7.8", "Single numbers rounded to whole decibels")
def _chk_rounding() -> Outcome:
    # "rounded to integer numbers": the flat 40 dB spectrum gives
    # LA,eq = 51,000 4 dB and LC,eq = 53,550 7 dB, which read 51 and 54 dB;
    # a lone 1 000 Hz band at 44,5 dB sums to exactly 44,5 dB, and the half
    # goes up, to 45 dB.
    flat = building.service_equipment_level(_flat(40.0), _THIRD, quantity="eq")
    lone_levels = np.full(_THIRD.size, -200.0)
    lone_levels[_THIRD == 1000.0] = 44.5
    lone = building.service_equipment_level(
        np.tile(lone_levels, (3, 1)), _THIRD, quantity="eq"
    )
    got = (flat.ratings["LA,eq"], flat.ratings["LC,eq"], lone.ratings["LA,eq"])
    matching = sum(g == w for g, w in zip(got, (51, 54, 45), strict=True))
    return count(matching, 3, subject="single numbers rounded as 7.8 reads")


@register(_DOMAIN, f"{_DRAFT} 7.4.1", "Position ladder at its thresholds")
def _chk_ladder() -> Outcome:
    # Three readings 3,0 dB apart proceed (inclusive); 3,1 dB adds positions 4
    # and 5; six under 6,0 dB proceed and at 6,0 dB add 6 and 7; nine under
    # 9,0 dB proceed and at 9,0 dB the session is interrupted. Positions 6 and
    # 7 answer a difference "less than 9,0 dB" only, and a spread can only
    # widen: three or six readings already 10 dB apart interrupt at once.
    cases = (
        ([35.1, 32.1, 34.0], "proceed"),
        ([35.2, 32.1, 34.0], "add_positions"),
        ([35.0, 32.1, 36.0, 35.2, 33.0, 37.9], "proceed"),
        ([38.1, 32.1, 35.0, 37.0, 34.0, 36.0], "add_positions"),
        ([35.0, 32.0, 36.0, 35.0, 34.0, 36.0, 35.0, 40.9, 33.0], "proceed"),
        ([35.0, 32.0, 36.0, 35.0, 34.0, 36.0, 35.0, 41.0, 33.0], "interrupt"),
        ([30.0, 33.0, 40.0], "interrupt"),
        ([30.0, 33.0, 34.0, 31.0, 32.0, 40.0], "interrupt"),
    )
    matching = sum(
        building.check_position_spread(levels).action == action
        for levels, action in cases
    )
    return count(matching, len(cases), subject="stages decided as 7.4.1 reads")


@register(
    _DOMAIN,
    f"{_DRAFT} 7.2 and 7.3",
    "Distances and heights of the positions at each limit",
)
def _chk_positions() -> Outcome:
    # Each limit met exactly and missed by 0,01 m in a 5 m x 4 m x 2,6 m room:
    # 0,50 m from the walls and from the ceiling (in a room 2,4 m high) and
    # 0,30 m in a small room, 1,0 m between room positions and from the
    # corner, the preferred 1,5 m, 1,5 m from a source, room positions 0,5 m
    # to 2,0 m high (7.3), the corner 0,5 m to 1,5 m high and its preferred
    # 0,5 m from both walls (7.2). The 0,2 m from obstacles of 7.2 has a row
    # of its own.
    # Where decimal coordinates put a limit a hair under itself in binary
    # (4,0 - 3,7 m; 2,3 - 1,3 m; 2,8 - 1,3 m; 2,3 - 0,8 m) the passing case
    # uses them.
    room = (5.0, 4.0, 2.6)
    corner = (0.5, 0.5, 0.5)
    pair = ((2.5, 2.0, 1.2), (4.0, 3.2, 1.5))
    source = ((4.9, 0.2, 2.4),)

    def judged(
        verdict: str,
        rooms: tuple[tuple[float, float, float], ...] = pair,
        *,
        room_m: tuple[float, float, float] = room,
        corner_m: tuple[float, float, float] = corner,
        sources: tuple[tuple[float, float, float], ...] = source,
        small_room: bool = False,
    ) -> bool:
        check = building.check_service_equipment_positions(
            room_m, corner_m, rooms, source_positions_m=sources, small_room=small_room
        )
        return bool(getattr(check, verdict))

    low_ceiling = (5.0, 4.0, 2.4)

    near = ((2.5, 2.3, 1.2), (4.0, 3.2, 1.5))
    cases = (
        (judged("surface_ok", ((2.5, 2.0, 1.2), (4.5, 3.2, 1.5))), True),
        (judged("surface_ok", ((2.5, 2.0, 1.2), (4.51, 3.2, 1.5))), False),
        (judged("surface_ok", ((2.5, 2.0, 1.2), (4.0, 3.7, 1.5))), False),
        (
            judged("surface_ok", ((2.5, 2.0, 1.2), (4.0, 3.7, 1.5)), small_room=True),
            True,
        ),
        (
            judged("surface_ok", ((2.5, 2.0, 1.2), (4.0, 3.71, 1.5)), small_room=True),
            False,
        ),
        (
            judged(
                "surface_ok", ((2.5, 2.0, 1.2), (4.0, 3.2, 1.9)), room_m=low_ceiling
            ),
            True,
        ),
        (
            judged(
                "surface_ok", ((2.5, 2.0, 1.2), (4.0, 3.2, 1.91)), room_m=low_ceiling
            ),
            False,
        ),
        (judged("separation_ok", ((1.3, 2.0, 1.2), (2.3, 2.0, 1.2))), True),
        (judged("separation_ok", ((1.3, 2.0, 1.2), (2.29, 2.0, 1.2))), False),
        (judged("separation_ok", ((1.5, 0.5, 0.5), (4.0, 3.2, 1.5))), True),
        (judged("separation_ok", ((1.49, 0.5, 0.5), (4.0, 3.2, 1.5))), False),
        (judged("preferred_separation", ((1.3, 2.0, 1.2), (2.8, 2.0, 1.2))), True),
        (judged("preferred_separation", ((1.3, 2.0, 1.2), (2.79, 2.0, 1.2))), False),
        (judged("source_ok", near, sources=((2.5, 0.8, 1.2),)), True),
        (judged("source_ok", near, sources=((2.5, 0.81, 1.2),)), False),
        (judged("height_ok", ((2.5, 2.0, 0.5), (4.0, 3.2, 1.5))), True),
        (judged("height_ok", ((2.5, 2.0, 0.49), (4.0, 3.2, 1.5))), False),
        (judged("height_ok", ((2.5, 2.0, 2.0), (4.0, 3.2, 1.5))), True),
        (judged("height_ok", ((2.5, 2.0, 2.01), (4.0, 3.2, 1.5))), False),
        (judged("corner_height_ok"), True),
        (judged("corner_height_ok", corner_m=(0.5, 0.5, 0.49)), False),
        (judged("corner_height_ok", corner_m=(0.5, 0.5, 1.5)), True),
        (judged("corner_height_ok", corner_m=(0.5, 0.5, 1.51)), False),
        (judged("preferred_corner_wall_distance"), True),
        (judged("preferred_corner_wall_distance", corner_m=(0.5, 0.49, 0.5)), False),
        (judged("preferred_corner_wall_distance", corner_m=(0.51, 0.5, 0.5)), False),
    )
    matching = sum(got is expected for got, expected in cases)
    return count(matching, len(cases), subject="limits decided as 7.2 and 7.3 read")


@register(_DOMAIN, f"{_DRAFT} 7.9", "Additional position for a source in the room")
def _chk_additional_position() -> Outcome:
    # "For noise sources in the wall a position is chosen 1 m in front of the
    # source and 1,5 m above floor level. For a noise source in the ceiling, the
    # position shall be 1,5 m above floor level, directly below the source."
    room = (5.0, 4.0, 2.6)
    placed = (
        building.additional_microphone_position(room, (0.0, 1.7, 2.1), mounting="wall"),
        building.additional_microphone_position(room, (2.0, 4.0, 0.3), mounting="wall"),
        building.additional_microphone_position(
            room, (0.6, 3.0, 2.6), mounting="ceiling"
        ),
    )
    expected = ((1.0, 1.7, 1.5), (2.0, 3.0, 1.5), (0.6, 3.0, 1.5))
    matching = sum(
        bool(np.allclose(p, e, rtol=0.0, atol=1e-12))
        for p, e in zip(placed, expected, strict=True)
    )
    return count(matching, len(expected), subject="positions placed as 7.9 reads")


@register(
    _DOMAIN, f"{_DRAFT} 7.2", "Corner microphone at least 0,2 m from any obstacle"
)
def _chk_obstacle() -> Outcome:
    # "The microphone position shall be at least 0,2 m away from any obstacle"
    # (folio 7, PDF page 45): the limit met exactly passes, 0,19 m fails, and
    # 0,7 - 0,5 m, a hair under 0,2 in binary, is still 0,2 m.
    limit = ref.ISO16032_OBSTACLE_DISTANCE_M
    cases = ((limit, True), (0.7 - 0.5, True), (limit - 0.01, False))
    matching = sum(
        building.check_service_equipment_positions(
            (5.0, 4.0, 2.6),
            (0.5, 0.5, 0.5),
            [(2.5, 2.0, 1.2), (4.0, 3.2, 1.5)],
            corner_obstacle_distance_m=distance,
        ).corner_obstacle_ok
        is expected
        for distance, expected in cases
    )
    return count(matching, len(cases), subject="obstacle distances judged as 7.2 reads")


@register(_DOMAIN, f"{_DRAFT} Clause 5", "Calibration deviating by more than 0,5 dB")
def _chk_calibration() -> Outcome:
    # "If the calibration measurement deviates from previous calibrations by
    # more than 0,5 dB, do not use this equipment" (folio 5, PDF page 43).
    # 93,8 and 94,3 dB are exactly 0,5 dB apart and pass, and so do 127,8
    # and 128,3 dB, 0,500 000 000 000 014 2 apart in binary; 94,4 dB is
    # 0,6 dB from 93,8 dB and fails. An end 0,2 dB from the beginning but
    # 0,6 dB from an earlier calibration deviates from "previous
    # calibrations" and fails.
    limit = ref.ISO16032_CALIBRATION_DEVIATION_DB
    cases = (
        (building.verify_calibration_deviation([93.8, 93.8 + limit]), True),
        (building.verify_calibration_deviation([127.8, 128.3]), True),
        (building.verify_calibration_deviation([93.8, 94.4]), False),
        (
            building.verify_calibration_deviation(
                [94.0, 94.2], previous_levels_db=[93.6]
            ),
            False,
        ),
    )
    matching = sum(check.passes is expected for check, expected in cases)
    return count(matching, len(cases), subject="calibrations judged as Clause 5 reads")


@register(_DOMAIN, f"{_DRAFT} 7.6", "Background measured over approximately 30 s")
def _chk_background_duration() -> Outcome:
    # "over a period of approximately 30 s" (folio 8, PDF page 46). The 30 s
    # is printed and "approximately" is not given a number, so the tolerance
    # is the operator's: 29 s and 31 s are reported as 1 s departures either
    # way, met by a 1 s tolerance and not by none; 28,9 s and 31,1 s miss the
    # 1 s on each side; and 30,3 s, 0,300 000 000 000 000 7 s over in binary,
    # meets a 0,3 s tolerance.
    nominal = ref.ISO16032_BACKGROUND_DURATION_S

    def held(durations: list[float], tolerance: float) -> bool:
        return building.check_background_duration(
            durations, tolerance_s=tolerance
        ).passes

    departed = building.check_background_duration(
        [nominal - 1.0, nominal + 1.0], tolerance_s=1.0
    )
    cases = (
        held([nominal, nominal], 0.0),
        not held([nominal - 1.0], 0.0),
        not held([nominal + 1.0], 0.0),
        departed.passes,
        bool(np.allclose(departed.departures_s, [-1.0, 1.0], rtol=0.0, atol=1e-12)),
        not held([nominal - 1.1], 1.0),
        not held([nominal + 1.1], 1.0),
        held([30.3], 0.3),
    )
    return count(
        sum(cases), len(cases), subject="durations held to 30 s within a tolerance"
    )


@register(
    _DOMAIN,
    f"{_DRAFT} Clause 9, NOTE",
    "Varying background: maximum over 10 min to 15 min, 10 dB or more below",
)
def _chk_varying_background() -> Outcome:
    # "the maximum sound pressure levels of the background noise could be
    # determined over a period of 10 min to 15 min in the corner microphone
    # position. If the maximum level is 10 dB or more below the service
    # equipment sound pressure level the result can be regarded valid without
    # correction" (folio 10, PDF page 48). Both ends of the period are in,
    # 599 s and 901 s are out; 30,4 dB over 20,4 dB is exactly the 10 dB,
    # 40,3 dB over 30,3 dB is the 10 dB a hair under it in binary, and 9,9 dB
    # is not.
    low, high, margin = ref.ISO16032_VARYING_BACKGROUND

    def valid(background: float, equipment: float, seconds: float) -> bool:
        return building.check_varying_background(
            [background], [equipment], observation_time_s=seconds
        ).passes

    cases = (
        (valid(30.0, 30.0 + margin, low), True),
        (valid(30.0, 30.0 + margin, high), True),
        (valid(30.0, 45.0, low - 1.0), False),
        (valid(30.0, 45.0, high + 1.0), False),
        (valid(20.4, 30.4, 720.0), True),
        (valid(30.3, 40.3, 720.0), True),
        (valid(30.6, 40.5, 720.0), False),
    )
    matching = sum(got is expected for got, expected in cases)
    return count(matching, len(cases), subject="cases judged as the NOTE reads")


@register(
    _DOMAIN,
    f"{_DRAFT} Clause 9",
    "Maximum less than 5 dB above the equivalent level in each period",
)
def _chk_disturbance() -> Outcome:
    # "for many stable sources this difference should be less than 5 dB to
    # indicate that the measurement has not been disturbed" (folio 10, PDF
    # page 48): 4,9 dB is undisturbed; 45,3 - 40,3 dB is exactly 5 dB and
    # 35,01 - 30,01 dB is 5 dB a hair under it in binary, and neither is less
    # than 5 dB.
    limit = ref.ISO16032_MAX_TO_EQUIVALENT_DB
    expected = (True, False, False, False)
    check = building.check_measurement_disturbance(
        [40.0 + limit - 0.1, 45.3, 40.0 + limit, 35.01], [40.0, 40.3, 40.0, 30.01]
    )
    matching = sum(
        bool(got) is want for got, want in zip(check.undisturbed, expected, strict=True)
    )
    return count(matching, len(expected), subject="periods judged as Clause 9 reads")


@register(
    _DOMAIN,
    f"{_DRAFT} 7.8, NOTE",
    "Calculated single numbers within 2 dB of the instrument",
)
def _chk_instrument_agreement() -> Outcome:
    # "If the difference is more than 2 dB, the calculations should be
    # checked" (folio 9, PDF page 47): the flat 40 dB spectrum gives
    # LA,eq = 51 dB and LC,eq = 54 dB. The difference counts either way: an
    # instrument 2 dB under the calculation (LA 49,0 dB) or 2 dB over it
    # (LC 56,0 dB) agrees, and one 2,1 dB under it (LA 48,9 dB) or over it
    # (LC 56,1 dB) does not.
    limit = ref.ISO16032_INSTRUMENT_AGREEMENT_DB
    res = building.service_equipment_level(_flat(40.0), _THIRD, quantity="eq")
    la, lc = res.ratings["LA,eq"], res.ratings["LC,eq"]
    lc_off = building.check_instrument_agreement(
        res, {"LA,eq": la - limit, "LC,eq": lc + limit + 0.1}
    )
    la_off = building.check_instrument_agreement(
        res, {"LA,eq": la - limit - 0.1, "LC,eq": lc + limit}
    )
    cases = (
        la == 51,
        lc == 54,
        lc_off.disagreeing == ("LC,eq",),
        la_off.disagreeing == ("LA,eq",),
    )
    return count(sum(cases), len(cases), subject="comparisons judged as 7.8 reads")
