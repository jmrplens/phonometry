#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound power in small test rooms: ISO 3743-1:2010 and ISO 3743-2:2018.

Rows of the "Intensity & sound power" section. Oracle: BS EN ISO 3743-1:2010
(the ISO text unchanged, PDF page = printed folio + 9) and ISO 3743-2:2018,
second edition (PDF page = printed folio + 6), every table and formula read on
the printed page. The two parts print their tables and a few worked numbers
(the 9.5 and 11.5 EXAMPLEs, Tables C.1 and D.1, Formula B.2's 1,06, and the
centring of B.5 on the curve of Figure B.4, which the library departs from and
the row states by how much); the determinations themselves carry no worked
example, so Eq. (14), (20), Formula (9) and (10) are pinned in closed form and
against the neighbouring standards the library already implements.
"""

from __future__ import annotations

import math
import warnings

import numpy as np

import phonometry as ph
from phonometry.noise_control.enclosure_insulation import TEST_ENVIRONMENT_REQUIREMENTS

from ..registry import Outcome, count, numeric, record, register

_DOMAIN = "Intensity & sound power"
_FREQS = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
_LW_RSS = np.array([87.0, 90.5, 92.5, 93.8, 94.0, 93.0, 90.0])
_ST = np.array(
    [
        [80.1, 83.4, 85.0, 84.2, 81.0, 76.5, 70.2],
        [79.0, 82.8, 84.6, 83.9, 80.4, 75.8, 69.5],
        [81.2, 84.0, 85.9, 85.0, 81.9, 77.1, 70.9],
        [80.5, 83.1, 85.3, 84.5, 81.3, 76.2, 70.0],
        [79.8, 83.6, 85.1, 84.0, 81.2, 76.6, 70.4],
        [80.9, 82.9, 85.6, 84.7, 81.5, 76.9, 70.6],
    ]
)
_RSS = np.array(
    [
        [78.5, 81.9, 83.7, 84.9, 84.8, 83.5, 79.8],
        [77.9, 81.2, 83.1, 84.3, 84.1, 82.9, 79.2],
        [79.3, 82.6, 84.4, 85.5, 85.4, 84.1, 80.3],
        [78.8, 82.1, 83.9, 85.0, 85.0, 83.7, 79.9],
        [78.2, 81.7, 83.5, 84.6, 84.5, 83.2, 79.5],
        [79.0, 82.4, 84.0, 85.2, 85.1, 83.9, 80.1],
    ]
)
#: More than 15 dB below both sources in every band.
_BACKGROUND = np.array([60.0, 62.0, 63.0, 62.0, 60.0, 55.0, 50.0])
_THIRDS = np.array(
    [100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0,
     1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0, 10000.0]
)  # fmt: skip


def _energy_mean(levels: np.ndarray) -> np.ndarray:
    return np.asarray(10.0 * np.log10(np.mean(10.0 ** (0.1 * levels), axis=0)))


def _hard_walled(**kwargs: object) -> ph.emission.HardWalledSoundPowerResult:
    kwargs.setdefault("background_levels", _BACKGROUND)
    return ph.emission.sound_power_hard_walled(_ST, _RSS, _LW_RSS, _FREQS, **kwargs)  # type: ignore[arg-type]


def _special_direct(**kwargs: object) -> ph.emission.SpecialRoomSoundPowerResult:
    kwargs.setdefault("background_levels", _BACKGROUND)
    return ph.emission.sound_power_special_room(
        _ST,
        _FREQS,
        volume_m3=70.0,
        nominal_reverberation_time_s=0.73,
        **kwargs,  # type: ignore[arg-type]
    )


# --- ISO 3743-1:2010 ---------------------------------------------------------
@register(
    _DOMAIN,
    "ISO 3743-1:2010 9.5 EXAMPLE",
    "Expanded uncertainty U = 2 sqrt(1,5^2 + 2^2) dB = 5 dB, sigma_omc = 2,0 dB",
)
def _chk_iso3743_1_example() -> Outcome:
    res = _hard_walled(sigma_omc_db=2.0)
    return numeric(5.0, res.expanded_uncertainty_a, 1e-12, unit="dB", places=6)


@register(
    _DOMAIN,
    "ISO 3743-1:2010 Table 3",
    "Typical upper bounds of sigma_R0 per octave band and A-weighted (the '400 to 5 000' row read as 500 Hz to 4 kHz)",
)
def _chk_iso3743_1_table3() -> Outcome:
    res = _hard_walled()
    printed = {"125 Hz": 3.0, "250 Hz": 2.0, "500 Hz": 1.5, "1 kHz": 1.5,
               "2 kHz": 1.5, "4 kHz": 1.5, "8 kHz": 2.5, "A": 1.5}  # fmt: skip
    computed = dict(zip(list(printed)[:-1], map(float, res.sigma_r0), strict=True))
    computed["A"] = res.sigma_r0_a
    return record(printed, computed, unit="dB")


@register(
    _DOMAIN,
    "ISO 3743-1:2010 Table C.1",
    "Total standard deviation of the grade 2 row, sigma_R0 = 1,5 dB, for sigma_omc = 0,5, 2 and 4 dB",
)
def _chk_iso3743_1_table_c1() -> Outcome:
    printed = {"sigma_omc 0,5": 1.6, "sigma_omc 2": 2.5, "sigma_omc 4": 4.3}
    computed = {
        name: round(_hard_walled(sigma_omc_db=omc).sigma_tot_a, 1)
        for name, omc in zip(printed, (0.5, 2.0, 4.0), strict=True)
    }
    return record(printed, computed, unit="dB")


@register(
    _DOMAIN,
    "ISO 3743-1:2010 Eq. 13 / 8.1.3",
    "K1 at the 6 dB margin is -10 lg(1 - 10^-0,6) = 1,2563 dB, 1,3 dB below it and 0 above 15 dB",
)
def _chk_iso3743_1_k1_rules() -> Outcome:
    mean_st = _energy_mean(_ST)
    background = _BACKGROUND.copy()
    background[1] = mean_st[1] - 6.0
    background[2] = mean_st[2] - 4.0
    background[3] = mean_st[3] - 15.5
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ph.emission.SoundPowerWarning)
        res = _hard_walled(
            background_levels=background, background_levels_ref=_BACKGROUND
        )
    expected = {"K1(6 dB)": 1.2563, "K1(4 dB)": 1.3, "K1(15,5 dB)": 0.0}
    computed = {
        "K1(6 dB)": round(float(res.background_correction[1]), 4),
        "K1(4 dB)": float(res.background_correction[2]),
        "K1(15,5 dB)": float(res.background_correction[3]),
    }
    return record(expected, computed, unit="dB")


@register(
    _DOMAIN,
    "ISO 3743-1:2010 Eq. 14 vs ISO 3747:2010 Eq. 11",
    "The hard-walled comparison and the in situ comparison give the same LW with the background negligible (closed form)",
)
def _chk_iso3743_1_vs_iso3747() -> Outcome:
    part1 = _hard_walled()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ph.emission.SoundPowerWarning)  # six positions
        in_situ = ph.emission.sound_power_in_situ(
            _ST, _RSS, _LW_RSS, _FREQS, background_levels=_BACKGROUND
        )
    worst = float(np.max(np.abs(part1.sound_power_level - in_situ.sound_power_level)))
    return numeric(
        0.0, worst, 1e-9, unit="dB", places=9, expected_label="0 dB difference"
    )


@register(
    _DOMAIN,
    "ISO 3743-1:2010 Eq. 20 / clause 3.4 NOTE 1",
    "A source steady over T = 10 s: LJ = LW + 10 lg(T/T0) band for band, background carried over the same T",
)
def _chk_iso3743_1_energy_identity() -> Outcome:
    t = 10.0
    background = _BACKGROUND.copy()
    background[2] = _energy_mean(_ST)[2] - 8.0
    power = _hard_walled(background_levels=background)
    energy = ph.emission.sound_energy_hard_walled(
        np.stack([_ST + 10.0 * math.log10(t)] * 5), _RSS, _LW_RSS, _FREQS,
        background_levels=background, integration_time_s=t,
    )  # fmt: skip
    worst = float(
        np.max(np.abs(energy.sound_energy_level - power.sound_power_level - 10.0))
    )
    return numeric(
        0.0, worst, 1e-9, unit="dB", places=9, expected_label="0 dB difference"
    )


@register(
    _DOMAIN,
    "ISO 3743-1:2010 Eq. 15 / Eq. 16",
    "Ne events one at a time and one measurement over Ne events agree (closed form)",
)
def _chk_iso3743_1_event_forms() -> Outcome:
    n_events = 8
    one_at_a_time = ph.emission.sound_energy_hard_walled(
        np.stack([_ST] * n_events), _RSS, _LW_RSS, _FREQS,
        background_levels=_BACKGROUND, integration_time_s=1.0,
    )  # fmt: skip
    encompassing = ph.emission.sound_energy_hard_walled(
        _ST + 10.0 * math.log10(n_events), _RSS, _LW_RSS, _FREQS, events=n_events,
        background_levels=_BACKGROUND, integration_time_s=1.0,
    )  # fmt: skip
    worst = float(
        np.max(
            np.abs(encompassing.sound_energy_level - one_at_a_time.sound_energy_level)
        )
    )
    return numeric(
        0.0, worst, 1e-9, unit="dB", places=9, expected_label="0 dB difference"
    )


@register(
    _DOMAIN,
    "ISO 3743-1:2010 Annex A",
    "C2 at 500 m and 23,0 degC from Eq. (A.2): 0,26 dB (not the 0,4 dB of C.4.2.5)",
)
def _chk_iso3743_1_annex_a() -> Outcome:
    ps = ph.emission.static_pressure_from_altitude(500.0)
    res = _hard_walled(static_pressure_kpa=ps)
    return numeric(0.26, res.c2, 0.005, unit="dB", places=4)


@register(
    _DOMAIN,
    "ISO 3743-1:2010 Table B.1 / Eq. B.1",
    "LWA of a flat 90 dB octave spectrum, 63 Hz to 8 kHz, with the printed Ck",
)
def _chk_iso3743_1_table_b1() -> Outcome:
    freqs = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
    ck = np.array([-26.2, -16.1, -8.6, -3.2, 0.0, 1.2, 1.0, -1.1])  # Table B.1
    flat = np.full((3, freqs.size), 80.0)
    res = ph.emission.sound_power_hard_walled(
        flat, flat, np.full(freqs.size, 90.0), freqs,
        background_levels=np.full(freqs.size, 50.0),
    )  # fmt: skip
    expected = 90.0 + 10.0 * math.log10(float(np.sum(10.0 ** (0.1 * ck))))
    return numeric(expected, res.sound_power_level_a, 1e-9, unit="dB", places=4)


@register(
    _DOMAIN,
    "ISO 3743-1:2010 4.2",
    "Room volume and reference box: 40 m3 and 40 boxes; 1,0 m up to 100 m3, 2,0 m above",
)
def _chk_iso3743_1_room_size() -> Outcome:
    orientations = 80.0 + np.linspace(0.0, 1.0, 8)[:, None] * np.ones((1, 7))
    cases = [
        (40.0, (1.0, 1.0, 1.0), True, True),
        (39.9, (0.5, 0.5, 0.5), False, True),
        (45.0, (1.2, 1.0, 1.0), False, False),
        (100.0, (1.1, 0.5, 0.5), True, False),
        (100.1, (1.1, 0.5, 0.5), True, True),
        (150.0, (2.1, 0.5, 0.5), True, False),
    ]
    agree = 0
    for volume, box, volume_ok, box_ok in cases:
        check = ph.emission.check_hard_walled_room(
            orientations, _FREQS, volume_m3=volume, reference_box_m=box
        )
        agree += int(check.volume_adequate is volume_ok and check.box_fits is box_ok)
    return count(agree, len(cases), subject="room and box verdicts")


@register(
    _DOMAIN,
    "ISO 3743-1:2010 Table 2",
    "Source locations from sM: 1 up to 2,5 dB, 2 up to 4,0 dB, 2 plus 2 in another room above",
)
def _chk_iso3743_1_table2() -> Outcome:
    # Deviations whose sums of squares over n - 1 are 6,25 and 16 exactly, so
    # Eq. (7) lands on the edges of the table.
    edges = {
        "sM 2,5": (np.array([3.75, -3.75, 1.25, -1.25, 0.0, 0.0]), (1, 0)),
        "sM 4,0": (np.array([6.0, -6.0, 2.0, -2.0, 0.0, 0.0]), (2, 0)),
        "sM 4,4": (np.array([6.6, -6.6, 2.2, -2.2, 0.0, 0.0]), (2, 2)),
    }
    agree = 0
    for deviations, (locations, other) in edges.values():
        plan = ph.emission.hard_walled_source_locations(
            80.0 + deviations[:, None], [1000.0]
        )
        agree += int(
            int(plan.source_locations[0]) == locations
            and int(plan.additional_room_locations[0]) == other
        )
    return count(agree, len(edges), subject="Table 2 rows")


@register(
    _DOMAIN,
    "ISO 3743-1:2010 Eq. 24 / ISO 3743-2:2018 Formula 14",
    "sigma'_R0 = sqrt(sigma'_tot^2 - sigma'_omc^2) = 2,0 dB for 2,5 dB and 1,5 dB (the minus of Part 1; Part 2 prints a plus)",
)
def _chk_iso3743_round_robin() -> Outcome:
    return numeric(
        2.0, ph.emission.reproducibility_from_round_robin(2.5, 1.5), 1e-12,
        unit="dB", places=6,
    )  # fmt: skip


@register(
    _DOMAIN,
    "ISO 3743-1:2010 4.5 vs ISO 11546-2:1995 Table C.1",
    "The 6 dB background margin the determination holds to is the one ISO 11546-2 tabulates for ISO 3743-1",
)
def _chk_iso3743_1_background_vs_iso11546() -> Outcome:
    mean_st = _energy_mean(_ST)
    at = ph.emission.sound_power_hard_walled(
        _ST, _RSS, _LW_RSS, _FREQS, background_levels=mean_st - 6.0,
        background_levels_ref=_BACKGROUND,
    )  # fmt: skip
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ph.emission.SoundPowerWarning)
        below = ph.emission.sound_power_hard_walled(
            _ST, _RSS, _LW_RSS, _FREQS, background_levels=mean_st - 5.99,
            background_levels_ref=_BACKGROUND,
        )  # fmt: skip
    threshold = (
        6.0
        if bool(np.all(at.background_requirement_met))
        and not bool(np.any(below.background_requirement_met))
        else float("nan")
    )
    tabulated = TEST_ENVIRONMENT_REQUIREMENTS["ISO 3743-1"][1]
    return record(
        {"ISO 3743-1 4.5": 6.0, "ISO 11546-2 Table C.1": 6.0},
        {"ISO 3743-1 4.5": threshold, "ISO 11546-2 Table C.1": float(tabulated or 0.0)},
        unit="dB",
    )


# --- ISO 3743-2:2018 ---------------------------------------------------------
@register(
    _DOMAIN,
    "ISO 3743-2:2018 11.5 EXAMPLE",
    "Expanded uncertainty U = 2 sqrt(2^2 + 2^2) dB = 5,7 dB, sigma_omc = 2,0 dB",
)
def _chk_iso3743_2_example() -> Outcome:
    res = _special_direct(sigma_omc_db=2.0)
    return numeric(5.7, res.expanded_uncertainty_a, 0.05, unit="dB", places=4)


@register(
    _DOMAIN,
    "ISO 3743-2:2018 Table 5",
    "Typical upper bounds of sigma_R0 per octave band and A-weighted",
)
def _chk_iso3743_2_table5() -> Outcome:
    res = _special_direct()
    printed = {"125 Hz": 5.0, "250 Hz": 3.0, "500 Hz": 2.0, "1 kHz": 2.0,
               "2 kHz": 2.0, "4 kHz": 2.0, "8 kHz": 3.0, "A": 2.0}  # fmt: skip
    computed = dict(zip(list(printed)[:-1], map(float, res.sigma_r0), strict=True))
    computed["A"] = res.sigma_r0_a
    return record(printed, computed, unit="dB")


@register(
    _DOMAIN,
    "ISO 3743-2:2018 Table D.1",
    "Total standard deviation of the grade 2 row, sigma_R0 = 2 dB, for sigma_omc = 0,5, 2,0 and 4,0 dB",
)
def _chk_iso3743_2_table_d1() -> Outcome:
    printed = {"sigma_omc 0,5": 2.1, "sigma_omc 2,0": 2.8, "sigma_omc 4,0": 4.5}
    computed = {
        name: round(_special_direct(sigma_omc_db=omc).sigma_tot_a, 1)
        for name, omc in zip(printed, (0.5, 2.0, 4.0), strict=True)
    }
    return record(printed, computed, unit="dB")


@register(
    _DOMAIN,
    "ISO 3743-2:2018 Formula 1 / Formula B.2",
    "R at 1 000 Hz for a 70 m3 room is the 1,06 of Formula (B.2)",
)
def _chk_iso3743_2_formula1() -> Outcome:
    r = float(ph.emission.reverberation_parameter([1000.0], 70.0)[0])
    return numeric(1.06, r, 0.005, places=4)


@register(
    _DOMAIN,
    "ISO 3743-2:2018 Formula B.2",
    "A room that follows the curve exactly centres on Tnom = T1000 / R(1 000 Hz) (closed form)",
)
def _chk_iso3743_2_centring() -> Outcome:
    r = ph.emission.reverberation_parameter(_THIRDS, 70.0)
    t = 0.8 * r / r[10]
    check = ph.emission.check_special_room_reverberation(t, _THIRDS, volume_m3=70.0)
    return numeric(
        0.8 / float(r[10]),
        check.nominal_reverberation_time_s,
        1e-12,
        unit="s",
        places=6,
    )


#: Figure B.4 of ISO 3743-2:2018 (PDF page 29, printed page 23): T/T1000 read
#: off the printed curve at the one-third-octave centres from 100 Hz to 10 kHz;
#: two readings made apart agree within 0,01.
_FIGURE_B4 = np.array(
    [1.398, 1.294, 1.292, 1.335, 1.298, 1.237, 1.176, 1.002, 0.967, 0.990, 1.0,
     1.0, 1.0, 1.0, 1.031, 1.018, 1.006, 0.987, 0.954, 0.919, 0.801]
)  # fmt: skip


@register(
    _DOMAIN,
    "ISO 3743-2:2018 B.5 EXAMPLE",
    "T1000 = 0,8 s on the curve of Figure B.4: the printed T/Tnom = 1,09 is the midpoint of the extreme ratios against 0,9 and 1,1 alone (within 0,015), "
    "and as Tnom = 0,73 s it puts 250 Hz above 1,1 R; the library's centring qualifies the room at 0,76 s, a departure of 0,17 dB in LW (see the errata)",
)
def _chk_iso3743_2_b5_example() -> Outcome:
    t = 0.8 * _FIGURE_B4
    q = t / ph.emission.reverberation_parameter(_THIRDS, 70.0)
    midpoint = 0.8 / (0.5 * float(q.max() + q.min()))
    printed = ph.emission.check_special_room_reverberation(
        t, _THIRDS, volume_m3=70.0, nominal_reverberation_time_s=0.73
    )
    centred = ph.emission.check_special_room_reverberation(t, _THIRDS, volume_m3=70.0)
    departure = 10.0 * math.log10(centred.nominal_reverberation_time_s / 0.73)
    facts = (
        abs(midpoint - 1.09) <= 0.015,
        not bool(printed.band_within[4]),
        centred.passes and abs(centred.nominal_reverberation_time_s - 0.76) <= 0.01,
        abs(departure - 0.17) <= 0.05,
    )
    return count(sum(facts), len(facts), subject="B.5 readings")


@register(
    _DOMAIN,
    "ISO 3743-2:2018 Clause 5",
    "The noise source should not exceed 1 % of the room: 0,7 m3 in the minimum 70 m3 room is within the recommendation, 0,71 m3 is not, and neither moves the verdict",
)
def _chk_iso3743_2_source_size() -> Outcome:
    r = ph.emission.reverberation_parameter(_THIRDS, 70.0)
    verdicts = []
    for volume in (0.7, 0.71):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ph.emission.SoundPowerWarning)
            check = ph.emission.check_special_room_reverberation(
                0.7 * r, _THIRDS, volume_m3=70.0, source_volume_m3=volume
            )
        verdicts.append((check.source_size_recommended, check.passes))
    return count(
        int(verdicts[0] == (True, True)) + int(verdicts[1] == (False, True)),
        2,
        subject="clause 5 readings",
    )


@register(
    _DOMAIN,
    "ISO 3743-2:2018 6.3",
    "Limiting curves 0,9 and 1,1 times R Tnom up to 6,3 kHz, 0,8 and 1,2 above",
)
def _chk_iso3743_2_limits() -> Outcome:
    check = ph.emission.check_special_room_reverberation(
        np.full(_THIRDS.size, 0.7),
        _THIRDS,
        volume_m3=70.0,
        nominal_reverberation_time_s=0.7,
    )
    return record(
        {"6,3 kHz low": 0.9, "6,3 kHz high": 1.1, "8 kHz low": 0.8, "8 kHz high": 1.2},
        {
            "6,3 kHz low": float(check.lower_limit[18]),
            "6,3 kHz high": float(check.upper_limit[18]),
            "8 kHz low": float(check.lower_limit[19]),
            "8 kHz high": float(check.upper_limit[19]),
        },
    )


@register(
    _DOMAIN,
    "ISO 3743-2:2018 Table 1",
    "Maximum permitted differences of the reference-source evaluation of 6.7",
)
def _chk_iso3743_2_table1() -> Outcome:
    check = ph.emission.check_special_room_suitability(_LW_RSS, _LW_RSS, _FREQS)
    printed = {"125 Hz": 5.0, "250 Hz": 3.0, "500 Hz": 3.0, "1 kHz": 3.0,
               "2 kHz": 3.0, "4 kHz": 3.0, "8 kHz": 4.0}  # fmt: skip
    return record(
        printed, dict(zip(printed, map(float, check.limit_db), strict=True)), unit="dB"
    )


@register(
    _DOMAIN,
    "ISO 3743-2:2018 6.7 / Table 1",
    "Each band is suitable at its Table 1 difference read high or low, and not 0,1 dB beyond it on either side",
)
def _chk_iso3743_2_suitability_verdicts() -> Outcome:
    limits = np.array([5.0, 3.0, 3.0, 3.0, 3.0, 3.0, 4.0])
    agree = total = 0
    for band, limit in enumerate(limits):
        for offset, within in ((limit, True), (-limit, True),
                               (limit + 0.1, False), (-limit - 0.1, False)):  # fmt: skip
            measured = _LW_RSS.copy()
            measured[band] += offset
            check = ph.emission.check_special_room_suitability(
                measured, _LW_RSS, _FREQS
            )
            agree += int(
                bool(check.band_within[band]) is within and check.passes is within
            )
            total += 1
    return count(agree, total, subject="Table 1 verdicts")


#: Table 3 of ISO 3743-2:2018 typed in from the printed page: (band, class)
#: -> the minimum number of source locations for 3, 6 and 12 microphones.
_TABLE_3 = {
    ("125", "broadband"): (1, 1, 1), ("250", "broadband"): (1, 1, 1),
    ("500", "broadband"): (1, 1, 1), ("1000", "broadband"): (1, 1, 1),
    ("125", "narrow-band"): (1, 1, 1), ("250", "narrow-band"): (2, 2, 1),
    ("500", "narrow-band"): (2, 2, 1), ("1000", "narrow-band"): (2, 1, 1),
    ("125", "discrete tone"): (3, 2, 2), ("250", "discrete tone"): (4, 3, 2),
    ("500", "discrete tone"): (4, 2, 2), ("1000", "discrete tone"): (3, 2, 1),
}  # fmt: skip
_TABLE_3_A = {
    "broadband": (1, 1, 1),
    "narrow-band": (2, 2, 1),
    "discrete tone": (4, 3, 2),
}
#: Six survey levels in each class of 9.5: sM of 1,1 dB and 2,6 dB about the
#: arithmetic mean (a range within 5 dB), and 4,4 dB about the energy mean of
#: Formula (5) (a range of 9,2 dB).
_SURVEYS = {
    "broadband": np.array([-1.0, 1.0, -1.0, 1.0, -1.0, 1.0]),
    "narrow-band": np.array([-2.4, 2.4, -2.4, 2.4, -2.4, 2.4]),
    "discrete tone": np.array([-4.6, 4.6, -4.6, 4.6, 0.0, 0.0]),
}


@register(
    _DOMAIN,
    "ISO 3743-2:2018 Table 3",
    "Minimum number of source locations for 3, 6 and 12 microphone positions, every band row and the A-weighted row",
)
def _chk_iso3743_2_table3() -> Outcome:
    agree = total = 0
    for column, mics in enumerate((3, 6, 12)):
        for (band, cls), row in _TABLE_3.items():
            plan = ph.emission.special_room_source_locations(
                70.0 + _SURVEYS[cls][:, None], [float(band)], microphone_positions=mics
            )
            agree += int(
                plan.spectral_character == (cls,)
                and int(plan.source_locations[0]) == row[column]
            )
            total += 1
        for cls, row in _TABLE_3_A.items():
            plan = ph.emission.special_room_source_locations(
                70.0 + _SURVEYS["broadband"][:, None], [1000.0],
                microphone_positions=mics, a_weighted_levels=80.0 + _SURVEYS[cls],
            )  # fmt: skip
            agree += int(plan.a_weighted_source_locations == row[column])
            total += 1
    return count(agree, total, subject="Table 3 cells")


@register(
    _DOMAIN,
    "ISO 3743-2:2018 Table 4",
    "Background corrections: 2, 2, 1, 1, 1, 0,5, 0,5 dB for 4 dB to 10 dB, 0 above",
)
def _chk_iso3743_2_table4() -> Outcome:
    margins = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
    printed = dict(
        zip(
            [f"{m:g} dB" for m in margins],
            [2.0, 2.0, 1.0, 1.0, 1.0, 0.5, 0.5, 0.0],
            strict=True,
        )
    )
    corrections = ph.emission.special_room_background_correction(
        np.full(len(margins), 80.0), 80.0 - np.array(margins)
    )
    return record(
        printed, dict(zip(printed, map(float, corrections), strict=True)), unit="dB"
    )


@register(
    _DOMAIN,
    "ISO 3743-2:2018 Formula 9",
    "Direct method LW = Lp - 10 lg(Tnom/T0) + 10 lg(V/V0) - 13 dB in a 70 m3 room, Tnom = 0,73 s (closed form)",
)
def _chk_iso3743_2_formula9() -> Outcome:
    res = _special_direct()
    expected = (
        _energy_mean(_ST) - 10.0 * math.log10(0.73) + 10.0 * math.log10(70.0) - 13.0
    )
    worst = float(np.max(np.abs(res.sound_power_level - expected)))
    return numeric(
        0.0, worst, 1e-9, unit="dB", places=9, expected_label="0 dB difference"
    )


@register(
    _DOMAIN,
    "ISO 3743-2:2018 Formula 10 vs ISO 3743-1:2010 Eq. 14",
    "The comparison methods of the two parts agree with the background negligible (closed form)",
)
def _chk_iso3743_2_formula10() -> Outcome:
    part2 = ph.emission.sound_power_special_room_comparison(
        _ST, _RSS, _LW_RSS, _FREQS, background_levels=_BACKGROUND
    )
    worst = float(
        np.max(np.abs(part2.sound_power_level - _hard_walled().sound_power_level))
    )
    return numeric(
        0.0, worst, 1e-9, unit="dB", places=9, expected_label="0 dB difference"
    )


@register(
    _DOMAIN,
    "ISO 3743-2:2018 10.3 a) / Table 4",
    "The reference levels take Table 4 before Formula (10): ST 75 dB, RSS 80 dB, LWr 90 dB and a 5 dB reference margin give Lpr 78 dB and LW 87 dB (closed form)",
)
def _chk_iso3743_2_reference_background() -> Outcome:
    res = ph.emission.sound_power_special_room_comparison(
        np.full((6, 1), 75.0),
        np.full((6, 1), 80.0),
        [90.0],
        [1000.0],
        background_levels=[50.0],
        background_levels_ref=[75.0],
    )
    return numeric(87.0, float(res.sound_power_level[0]), 1e-9, unit="dB", places=9)


@register(
    _DOMAIN,
    "ISO 3743-2:2018 Formula 2",
    "H (theta + 5 degC) within +/-10 % of its value during the reverberation measurement: +10 % passes, +12 % fails, and 80 % at 10 degC passes against 50 % at 20 degC only through the 5 degC",
)
def _chk_iso3743_2_climate() -> Outcome:
    r = ph.emission.reverberation_parameter(_THIRDS, 70.0)
    verdicts = []
    for humidity, temperature in ((55.0, 20.0), (56.0, 20.0), (80.0, 10.0)):
        check = ph.emission.check_special_room_reverberation(
            0.7 * r, _THIRDS, volume_m3=70.0,
            relative_humidity_percent=humidity, temperature_c=temperature,
            reverberation_relative_humidity_percent=50.0, reverberation_temperature_c=20.0,
        )  # fmt: skip
        verdicts.append(check.climate_stable)
    return count(
        int(verdicts[0] is True) + int(verdicts[1] is False) + int(verdicts[2] is True),
        3,
        subject="climate verdicts",
    )
