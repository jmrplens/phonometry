#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Suspended ceilings in a reverberation room: EN 16487:2014.

EN 16487 is a test code, not a calculation method: it fixes the arrangement
EN ISO 354 leaves open, so that two laboratories measuring the same ceiling
measure the same thing. It prints no worked example, and nothing in it can be
recomputed from an input it also prints. Its own oracles are therefore the
numbers it fixes, on three printed pages of BS EN 16487:2014:

* **Table 1**, printed folio 14 (PDF page 16): the reproducibility of the 2010
  round robin of Annex A, as an expanded uncertainty, with the ISO 5725-6
  coverage factor of 2,8 named in the NOTE beneath it. The same table, the same
  two footnotes and the same coverage factor are printed in the official
  Spanish adoption, UNE-EN 16487:2015, Tabla 1 on printed folio 16, which is
  where the transcription below was checked a second time;
* **4.2.1**, printed folio 12 (PDF page 14): the air-absorption correction
  ``4V(m2 - m1)/S``, and the 0,05 it may not exceed at any frequency;
* **4.1.1.1.1** and **4.1.1.2.3.1**, printed folios 6 and 9: the 10,80 m2
  specimen and the 200 mm overall depth the CE marking data rests on.

The rest of this module is the chain 4.2.1 hangs off, anchored where it can be
anchored on a printed page rather than on our own arithmetic:

* the attenuation coefficient ``alpha`` comes from **ISO 9613-1:1993 Table 1**,
  printed folio 9 (PDF page 12), sub-table (i) at 20 degC and sub-table (j) at
  25 degC;
* the conversion ``m = alpha / (10 lg(e))`` of **EN ISO 354:2003 8.1.2.1**,
  printed folio 10 (PDF page 20), is anchored on the 4,343 that T. E. Vigran,
  Building Acoustics, Taylor & Francis, 2008, prints for it in Equation (4.41)
  on printed page 122, and its factor of four on the 20 m2 of air absorption
  the worked example on the next page arrives at;
* the resulting ``m`` is checked against a second printed table of it, Table
  4.2 of T. J. Cox and P. D'Antonio, Acoustic Absorbers and Diffusers, third
  edition, CRC Press, 2017, printed page 104.

Three real suspended-ceiling test reports supply arrangements and climates
nobody in this project chose: a UKAS certificate (Sound Research Laboratories,
No. 13441, 4 March 2020), a COFRAC report that names this test code on its face
as prEN 16487 (CSTB, No. AC14-26051052/10, 14 May 2014), and an SP Sweden
report from eleven years before the test code existed (P302808, Enclosure 24,
14 July 2003). Their printed values are cited here; none of the documents is
reproduced. A fourth arrangement is the E-400 mounting of G. van Hout, The
Acoustic Performance of Suspended Ceiling Systems, master of engineering
thesis, University of Canterbury, 2016, which prints the 400 mm cavity and the
3 600 mm by 3 000 mm, 10,8 m2 specimen on printed page 27 (PDF page 45).
"""

from __future__ import annotations

import math
import warnings

import numpy as np
from reference_data import suspended_ceilings as oracle

import phonometry as ph
from phonometry.materials.absorbers.suspended_ceilings import (
    AIR_CORRECTION_LIMIT,
    EN16487_COVERAGE_FACTOR,
    MIN_RELATIVE_HUMIDITY_PERCENT,
    TARGET_SPECIMEN_AREA_M2,
    TYPE_E_DEPTH_MM,
    WEIGHTED_UNCERTAINTY,
    SuspendedCeilingWarning,
)

from ..registry import Outcome, count, numeric, record, register

_CEILINGS = "Suspended ceilings in a reverberation room (EN 16487)"

#: EN 16487:2014, 4.2.1, printed folio 12: the correction "does not exceed
#: 0,05 at any frequency". Written out here rather than read from the library,
#: so that the two rows below judge the library's own limit against the page.
_PRINTED_CAP = 0.05

# The printed tables and the three laboratory reports are in
# ``tests/reference_data/suspended_ceilings.py``, each with its document, its
# edition and the page it was read on, and the test suite reads them there too.


def _half_last_digit(printed: float) -> float:
    """Half of the last digit a three-significant-figure table prints.

    ISO 9613-1 Table 1 prints every cell to three significant figures, so the
    published value carries a half-digit of its own; that half-digit, and not a
    tolerance of our choosing, is what a computed value has to land inside.
    """
    return 10.0 ** (math.floor(math.log10(abs(printed))) - 2) / 2.0


def _half_printed_decimal(printed: float) -> float:
    """Half of the last decimal place a value is printed to.

    Cox and D'Antonio print Table 4.2 to a different number of decimals in
    nearly every cell (``0.6`` beside ``38.76``), so each cell is judged at its
    own printed precision rather than the coarsest one in the table.
    """
    text = f"{printed!r}"
    decimals = len(text.partition(".")[2])
    return 0.5 * 10.0**-decimals


def _library_correction(
    *,
    volume_m3: float,
    specimen_area_m2: float,
    empty: tuple[float, float],
    with_specimen: tuple[float, float],
    bands_hz: tuple[float, ...],
) -> tuple[np.ndarray, bool]:
    """``4V(m2 - m1)/S`` through the library, and whether 4.2.1 was warned of.

    :param volume_m3: ``V``, from a laboratory report.
    :param specimen_area_m2: ``S``, likewise.
    :param empty: The empty-room climate, as the (temperature, humidity) key of
        a printed ISO 9613-1 sub-table and column.
    :param with_specimen: The same for the measurement with the specimen.
    :param bands_hz: The bands to evaluate, all of which both columns print.
    :return: The correction per band and whether the clause's cap was reported
        as exceeded, which is the verdict the rows check.
    """
    table = oracle.ISO9613_1_TABLE_1_DB_PER_KM
    alpha_1 = tuple(table[empty][band] for band in bands_hz)
    alpha_2 = tuple(table[with_specimen][band] for band in bands_hz)
    # dB/km to dB/m, then the library's own EN ISO 354 8.1.2.1 conversion.
    m_1 = ph.materials.attenuation_from_alpha(np.asarray(alpha_1) / 1000.0)
    m_2 = ph.materials.attenuation_from_alpha(np.asarray(alpha_2) / 1000.0)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        correction = ph.materials.air_absorption_correction(
            volume_m3=volume_m3,
            specimen_area_m2=specimen_area_m2,
            attenuation_with=m_2,
            attenuation_empty=m_1,
        )
    warned = any(
        issubclass(entry.category, SuspendedCeilingWarning) for entry in caught
    )
    return correction, warned


@register(
    _CEILINGS,
    "EN 16487:2014 Table 1 (BS EN 16487:2014, printed folio 14, PDF page 16)",
    "Reproducibility uncertainty of the absorption coefficient, the six "
    "printed octave bands and the weighted rating",
)
def _chk_table_one() -> Outcome:
    """The seven figures of Table 1, plane absorber, type E, 200 mm.

    The 125 Hz row carries footnote a (the band is not part of the weighted
    rating) and the last row footnote b (the weighted figure is computed with
    no rounding anywhere in the EN ISO 11654 chain). Both are transcribed in
    the library's docstrings rather than here, because neither changes a value.
    """
    printed = {
        **oracle.EN16487_TABLE_1_UNCERTAINTY,
        "alpha_w": oracle.EN16487_TABLE_1_WEIGHTED_UNCERTAINTY,
    }
    bands = ph.materials.reproducibility_uncertainty().tolist()
    computed = dict(zip(printed, [*bands, WEIGHTED_UNCERTAINTY], strict=True))
    return record(printed, computed)


@register(
    _CEILINGS,
    "EN 16487:2014 Table 1 NOTE (printed folio 14) against ISO 12999-2:2020 "
    "Table 3 (printed folio 6)",
    "The coverage factor is the 2,8 of ISO 5725-6 for this test code and the "
    "2,0 of Table 3 at 95 % for the general method",
)
def _chk_coverage_factors() -> Outcome:
    """Two printed coverage factors that the library must not confuse.

    EN 16487 prints no reproducibility standard deviation anywhere, so the 2,8
    of its NOTE cannot be checked by dividing the table by it and multiplying
    back; that is an identity, and it passes for any pair of numbers. What can
    be checked is that the two coverage factors this library holds are the two
    that are printed, in the two documents that print them, and that neither
    has been used for the other's table.
    """
    printed = {
        "EN 16487 NOTE": oracle.EN16487_TABLE_1_COVERAGE_FACTOR,
        "ISO 12999-2 Table 3 at 95 %": oracle.ISO12999_2_TABLE_3_COVERAGE_FACTOR_95,
    }
    computed = {
        "EN 16487 NOTE": EN16487_COVERAGE_FACTOR,
        "ISO 12999-2 Table 3 at 95 %": ph.materials.absorption_coverage_factor(0.95),
    }
    return record(printed, computed)


@register(
    _CEILINGS,
    "ISO 9613-1:1993 Table 1, sub-tables (i) and (j) (printed folio 9, PDF page 12)",
    "Pure-tone attenuation in dB/km at the four climates the air-absorption "
    "correction of 4.2.1 is exercised at below",
)
def _chk_iso9613_table1_climates() -> Outcome:
    """Twenty printed cells, each within half of its last printed digit.

    These are the inputs of the two 4.2.1 cases, so the cases stand on a
    printed table rather than on the library's own atmospheric model. Table 1
    is tabulated at the exact one-third-octave midbands of Note 5, which is why
    ``exact_midband`` is set: at the nominal 4 kHz the model gives 29,67 dB/km
    against the printed 2,94 x 10.
    """
    matching = 0
    total = 0
    worst = 0.0
    for (temperature_c, humidity), row in oracle.ISO9613_1_TABLE_1_DB_PER_KM.items():
        bands = list(row)
        computed = (
            ph.environment.air_attenuation(
                bands,
                temperature_c=temperature_c,
                relative_humidity_percent=humidity,
                atmospheric_pressure_kpa=101.325,
                exact_midband=True,
            )
            * 1000.0
        )
        for band, got in zip(bands, computed.tolist(), strict=True):
            printed = row[band]
            limit = _half_last_digit(printed)
            total += 1
            matching += int(abs(got - printed) <= limit)
            worst = max(worst, abs(got - printed) / limit)
    return count(
        matching,
        total,
        subject="printed cells inside half of their last printed digit",
        expected_label=f"20/20 (worst cell {worst:.0%} of its half-digit)",
    )


@register(
    _CEILINGS,
    "Vigran (2008) Eq. (4.41), printed page 122, PDF page 143",
    "The EN ISO 354:2003 8.1.2.1 conversion between alpha and m, printed as "
    "10 lg(e) = 4,343",
)
def _chk_ten_lg_e() -> Outcome:
    """The factor EN ISO 354 prints only as a formula, printed as a number.

    EN ISO 354:2003 8.1.2.1 gives ``m = alpha / (10 lg(e))`` and evaluates it
    nowhere; Vigran writes the same relation the other way round, as
    ``alpha = 10 lg(e) m`` with the factor worked out to four figures, which is
    a number this library can be held to.
    """
    printed = oracle.VIGRAN_EQ_4_41_TEN_LG_E
    unity = float(ph.materials.attenuation_from_alpha(1.0))
    return numeric(
        printed,
        1.0 / unity,
        0.0005,
        places=6,
        expected_label="4,343, to the four figures the page prints",
    )


@register(
    _CEILINGS,
    "Vigran (2008) Eq. (4.42) and the Example, printed page 123, PDF page 144",
    "The factor of four in the air term of 4.2.1, against a printed "
    "air-absorption area of 20 m2",
)
def _chk_four_m_v() -> Outcome:
    """``4mV`` from the printed volume and the printed attenuation.

    Vigran's example reads ``m`` off Figure 4.8 as 0,05 m-1 at 8 kHz in a
    100 m3 room and prints the resulting absorption area: "The air absorption
    alone then gives an absorption area of 20 m2". EN 16487 4.2.1 carries the
    same ``4V(m2 - m1)`` divided by the specimen area, so multiplying the
    correction back by that area has to return the printed 20 m2.

    The arrangement is a classroom, not a reverberation-room test: the
    correction it implies is far over the cap of 4.2.1 and the clause says so,
    which is why the warning is silenced here rather than asserted.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SuspendedCeilingWarning)
        correction = ph.materials.air_absorption_correction(
            volume_m3=oracle.VIGRAN_EXAMPLE_VOLUME_M3,
            specimen_area_m2=TARGET_SPECIMEN_AREA_M2,
            attenuation_with=[oracle.VIGRAN_EXAMPLE_M_PER_M],
            attenuation_empty=[0.0],
        )
    return numeric(
        oracle.VIGRAN_EXAMPLE_AIR_ABSORPTION_M2,
        float(correction[0]) * TARGET_SPECIMEN_AREA_M2,
        5e-9,
        unit="m2",
        expected_label="20 m2 of air absorption, from V = 100 m3 and m = 0,05 1/m",
    )


@register(
    _CEILINGS,
    "Cox & D'Antonio 3e Table 4.2, printed page 104, PDF page 161",
    "The air absorption constant m at 20 degC, over the three humidity rows "
    "4.2.2 admits",
)
def _chk_cox_table_4_2() -> Outcome:
    """A second printed table of the very quantity 4.2.1 consumes.

    ISO 9613-1 prints ``alpha`` and leaves the conversion to EN ISO 354; this
    table prints ``m`` itself, in reciprocal metres, so the two legs of the
    chain are checked together against a source that owes nothing to either.
    The rows below 50 % relative humidity are left out on purpose: 4.2.2 does
    not allow a room that dry, and the book's 63 Hz / 40 % cell is a rounding
    of the standard's already-rounded decibels rather than of the model.
    The book evaluates at the nominal octave centres, so ``exact_midband``
    stays off here where the ISO 9613-1 row above turns it on.
    """
    matching = 0
    total = 0
    worst = 0.0
    for humidity, row in oracle.COX_TABLE_4_2_M_MILLI.items():
        computed = (
            ph.environment.air_attenuation_m(
                oracle.COX_TABLE_4_2_BANDS_HZ,
                temperature_c=20.0,
                relative_humidity_percent=humidity,
                atmospheric_pressure_kpa=101.325,
            )
            * 1e3
        )
        for printed, got in zip(row, computed.tolist(), strict=True):
            limit = _half_printed_decimal(printed)
            total += 1
            matching += int(abs(got - printed) <= limit)
            worst = max(worst, abs(got - printed) / limit)
    return count(
        matching,
        total,
        subject="printed cells inside half of their own last decimal",
        expected_label=f"24/24 (worst cell {worst:.0%} of its half-digit)",
    )


@register(
    _CEILINGS,
    "EN 16487:2014 4.2.1 (printed folio 12, PDF page 14) with ISO 9613-1:1993 "
    "Table 1(i) and EN ISO 354:2003 8.1.2.1",
    "The air-absorption correction of a 300 m3 room whose humidity moved from "
    "50 % to 60 %, which the clause reports as over its printed cap",
)
def _chk_air_correction_over_the_cap() -> Outcome:
    """The clause failing, on a real room and printed climates.

    The room and the specimen are the ones SRL certificate 13441 prints,
    300 m3 and 10,7 m2; the two climates are two columns of ISO 9613-1
    Table 1(i) at 20 degC, so every input is on a page. The correction itself
    is printed nowhere, so no value of it is compared here: the 10 lg(e) and
    the factor of four it is built from are held to the numbers Vigran prints
    in the two rows above. What this row compares is what the clause decides,
    against the 0,05 it prints: the cap the library holds is that 0,05, and it
    reports this room as over it on the absolute value of a negative
    correction. The computed side shows the correction the verdict rests on.
    """
    bands = (500.0, 1000.0, 2000.0, 4000.0)
    computed, warned = _library_correction(
        volume_m3=oracle.SRL_13441_VOLUME_M3,
        specimen_area_m2=oracle.SRL_13441_AREA_M2,
        empty=(20.0, 50.0),
        with_specimen=(20.0, 60.0),
        bands_hz=bands,
    )
    return _cap_verdict(computed, bands, warned=warned, over=True)


@register(
    _CEILINGS,
    "EN 16487:2014 4.2.1 (printed folio 12, PDF page 14) with ISO 9613-1:1993 "
    "Table 1(i) and 1(j)",
    "The same correction in a 200 m3 room at 90 % relative humidity, which "
    "the clause passes in silence as inside its printed cap",
)
def _chk_air_correction_inside_the_cap() -> Outcome:
    """The clause passing, so the cap is exercised from both sides.

    The room is the one SP report P302808 prints, 200 m3 with a 10,8 m2
    specimen at 200 mm. Its printed climates are 20 degC / 90 % empty and
    24 degC / 89 % on the object; ISO 9613-1 Table 1 is printed on a 5 degC
    grid with humidity columns every ten points, so the nearer grid point,
    25 degC and 90 %, stands in for the second of them. At 90 % the printed
    attenuation rises with temperature from 500 Hz to 4 kHz and falls at
    125 Hz and 250 Hz, so the substitution overstates the correction in the
    four bands where it is positive, the largest of them at 2 kHz, and
    understates it by a thousandth or two below zero in the other two. As in
    the row above, no value of the correction is compared: what is checked is
    the cap and the clause's silence under it.
    """
    bands = (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0)
    computed, warned = _library_correction(
        volume_m3=oracle.SP_P302808_VOLUME_M3,
        specimen_area_m2=oracle.SP_P302808_AREA_M2,
        empty=(20.0, 90.0),
        with_specimen=(25.0, 90.0),
        bands_hz=bands,
    )
    return _cap_verdict(computed, bands, warned=warned, over=False)


def _cap_verdict(
    computed: np.ndarray, bands: tuple[float, ...], *, warned: bool, over: bool
) -> Outcome:
    """The printed cap of 4.2.1 and the verdict the clause reaches against it.

    :param computed: The library's correction per band, shown as evidence.
    :param bands: The bands it was evaluated at, in hertz.
    :param warned: Whether the library reported the cap as exceeded.
    :param over: Whether the case is the one the clause must report.
    :return: A record of the cap and the verdict, both of which must match.
    """
    worst = int(np.argmax(np.abs(computed)))
    verdict = "reported as over it" if over else "passed in silence"
    return record(
        {"cap of 4.2.1": _PRINTED_CAP, verdict: 1.0},
        {"cap of 4.2.1": AIR_CORRECTION_LIMIT, verdict: float(warned is over)},
        label=f"the printed 0,05, and the room {verdict}",
        computed_label=(
            f"cap {AIR_CORRECTION_LIMIT:g}, largest correction "
            f"{float(computed[worst]):+.5f} at {bands[worst]:g} Hz, "
            + ("reported" if warned else "not reported")
        ),
    )


@register(
    _CEILINGS,
    "ISO 354:2003 Formulae (8) and (9) (printed folios 10 and 11, PDF pages 20 "
    "and 21 of the EN printing), as EN 16487:2014 4.2.1 uses them",
    "The absorption coefficient of a type E 200 mm ceiling, from the "
    "reverberation times and climates a UKAS certificate prints",
)
def _chk_srl_absorption_coefficient() -> Outcome:
    """Printed inputs to a printed output, on an accredited measurement.

    Sound Research Laboratories certificate No. 13441 prints the room, the
    specimen area, both climates including two different barometric pressures,
    and per band the empty-room and with-specimen reverberation times beside
    the coefficient it derived from them. Feeding the library nothing but those
    printed numbers reproduces the six octave-centre coefficients to the 0,01
    the certificate prints.

    The air term is what makes this a check rather than a formality: dropped,
    the same call misses three of the six bands, by 0,016 at 4 kHz.
    """
    empty_temperature_c, empty_humidity, empty_pressure_mbar = oracle.SRL_13441_EMPTY
    temperature_c, humidity, pressure_mbar = oracle.SRL_13441_WITH_SPECIMEN
    m_1 = ph.environment.air_attenuation_m(
        oracle.SRL_13441_BANDS_HZ,
        temperature_c=empty_temperature_c,
        relative_humidity_percent=empty_humidity,
        atmospheric_pressure_kpa=empty_pressure_mbar / 10.0,
    )
    m_2 = ph.environment.air_attenuation_m(
        oracle.SRL_13441_BANDS_HZ,
        temperature_c=temperature_c,
        relative_humidity_percent=humidity,
        atmospheric_pressure_kpa=pressure_mbar / 10.0,
    )
    got = ph.materials.absorption_coefficient(
        oracle.SRL_13441_T1_S,
        oracle.SRL_13441_T2_S,
        oracle.SRL_13441_VOLUME_M3,
        oracle.SRL_13441_AREA_M2,
        temperature1_c=empty_temperature_c,
        temperature2_c=temperature_c,
        m1=m_1,
        m2=m_2,
    )
    worst = 0.0
    matching = 0
    for value, printed in zip(got.tolist(), oracle.SRL_13441_ALPHA_S, strict=True):
        matching += int(abs(value - printed) <= 0.005)
        worst = max(worst, abs(value - printed))
    return count(
        matching,
        len(oracle.SRL_13441_ALPHA_S),
        subject="printed coefficients within the rounding of the certificate",
        expected_label=f"6/6 (worst departure {worst:.4f})",
    )


@register(
    _CEILINGS,
    "EN 16487:2014 4.1.1.1.1 and 4.1.1.2.3.1 (printed folios 6 and 9, PDF "
    "pages 8 and 11)",
    "Four real suspended-ceiling arrangements judged against the printed "
    "10,80 m2 and the printed 200 mm",
)
def _chk_real_arrangements() -> Outcome:
    """Specimens nobody here chose, against the two numbers the clauses fix.

    4.1.1.1.1 asks for an area as close to 10,80 m2 as the product allows and
    4.1.1.2.3.1 fixes the type E depth at 200 mm for the measurement CE marking
    rests on. Two of these four arrangements sit on both, one is the E-50 of a
    CSTB report that names this test code on its face, and the last is the
    E-400 of a university reverberation room. The area error and the CE marking
    verdict are checked; the area is a target and not a tolerance, so nothing
    here makes a failure of the 0,30 m2 the CSTB specimen falls short by. The
    E-400 and its 10,8 m2 are printed in van Hout's thesis on page 27 (PDF
    page 45), which the module docstring cites in full.
    """
    cases = {
        # (area in m2, overall depth in mm), then the printed consequences.
        "SRL 13441, E-200": (
            (oracle.SRL_13441_AREA_M2, oracle.SRL_13441_DEPTH_MM),
            (-0.10, True),
        ),
        "SP P302808, 200 mm": (
            (oracle.SP_P302808_AREA_M2, oracle.SP_P302808_DEPTH_MM),
            (0.00, True),
        ),
        "CSTB AC14-26051052/10, E-50": (
            (oracle.CSTB_AC14_AREA_M2, oracle.CSTB_AC14_DEPTH_MM),
            (-0.30, False),
        ),
        "van Hout 2016, E-400": (
            (oracle.VAN_HOUT_AREA_M2, oracle.VAN_HOUT_DEPTH_MM),
            (0.00, False),
        ),
    }
    matching = 0
    for (area_m2, depth_mm), (error_m2, ce_marking) in cases.values():
        with warnings.catch_warnings():
            # A depth other than 200 mm is reported by the clause, which is the
            # verdict being checked rather than a surprise.
            warnings.simplefilter("ignore", SuspendedCeilingWarning)
            got = ph.materials.check_ceiling_specimen(
                area_m2=area_m2, mounting="E", depth_mm=depth_mm
            )
        matching += int(
            abs(got.area_error_m2 - error_m2) <= 5e-9
            and got.ce_marking_depth is ce_marking
            and got.satisfied is True
        )
    return count(
        matching,
        len(cases),
        subject="arrangements judged as the two clauses print them",
        expected_label=(
            f"4/4 against the 10,80 m2 of 4.1.1.1.1 and the "
            f"{TYPE_E_DEPTH_MM:g} mm of 4.1.1.2.3.1"
        ),
    )


@register(
    _CEILINGS,
    "EN 16487:2014 4.2.2 (printed folio 12, PDF page 14)",
    "The 50 % relative humidity floor against the room climates three "
    "laboratories printed",
)
def _chk_humidity_floor() -> Outcome:
    """Which of three real measurements were made in a room dry enough to fail.

    4.2.2 reads "The relative humidity in the room shall be at least 50 %".
    The UKAS certificate was measured at 41 % and 44 %, below it; the CSTB
    report at 62 % and 58 % and the SP report at 89 % and 90 %, above it. None
    of the three is an EN 16487 report, so the dry one is an illustration of
    the clause rather than a defect anyone reported, and it is the reason this
    floor is worth carrying: a real accredited laboratory measured a suspended
    ceiling under conditions this test code would not accept.

    Each climate goes to the library with the arrangement the same report
    prints, and the row reads back the humidity verdict and the overall one:
    the humidity is the only limit any of the three leaves, so the dry room
    fails on it and the other two pass, the CSTB E-50 included, whose depth is
    reported against CE marking and not failed.
    """
    printed = {
        # (area in m2, overall depth in mm), then the two climates in percent,
        # the empty room first.
        "SRL 13441": (
            (oracle.SRL_13441_AREA_M2, oracle.SRL_13441_DEPTH_MM),
            (oracle.SRL_13441_EMPTY[1], oracle.SRL_13441_WITH_SPECIMEN[1]),
        ),
        "CSTB AC14-26051052/10": (
            (oracle.CSTB_AC14_AREA_M2, oracle.CSTB_AC14_DEPTH_MM),
            (oracle.CSTB_AC14_EMPTY[1], oracle.CSTB_AC14_WITH_SPECIMEN[1]),
        ),
        "SP P302808": (
            (oracle.SP_P302808_AREA_M2, oracle.SP_P302808_DEPTH_MM),
            (oracle.SP_P302808_EMPTY[1], oracle.SP_P302808_WITH_SPECIMEN[1]),
        ),
    }
    below_the_floor = {"SRL 13441"}
    matching = 0
    for report, ((area_m2, depth_mm), climates) in printed.items():
        with warnings.catch_warnings():
            # The dry room, and the depth of the E-50, are reported by the
            # clause, which is the verdict being checked rather than a surprise.
            warnings.simplefilter("ignore", SuspendedCeilingWarning)
            got = ph.materials.check_ceiling_specimen(
                area_m2=area_m2,
                mounting="E",
                depth_mm=depth_mm,
                relative_humidity_percent=climates,
            )
        expected = report not in below_the_floor
        matching += int(got.humidity_ok is expected and got.satisfied is expected)
    return count(
        matching,
        len(printed),
        subject="printed climates judged against the floor of the clause",
        expected_label=(
            f"3/3 against the {MIN_RELATIVE_HUMIDITY_PERCENT:g} % of 4.2.2, "
            "one of them below it"
        ),
    )


@register(
    _CEILINGS,
    "EN 16487:2014 Table 1 footnote b with EN ISO 11654:1997 4.1 and 4.2 "
    "(printed folios 2 and 3)",
    "The weighted rating and absorption class three laboratories printed for "
    "their own suspended ceilings",
)
def _chk_printed_ratings() -> Outcome:
    """The chain footnote b of Table 1 points at, on three real ceilings.

    Table 1's weighted figure is qualified as "calculated without any rounding
    in the calculation chain in EN ISO 11654", so the chain is named by this
    test code even though the rating itself belongs to the other standard. The
    three reports print what came out of it: alpha_w = 0,95 class A from
    fifteen one-third-octave coefficients, alpha_w = 0,9 class A from five
    octave ones, and alpha_w = 0,70(MH) class C, the last of these on a report
    whose own standards line names prEN 16487.

    The CSTB case is the discriminating one. Both high-frequency bands sit
    exactly 0,25 above the shifted curve, so a strict comparison there prints M
    where the page prints MH, and the accepted shift leaves an unfavourable sum
    of exactly 0,10, so a strict comparison there gives 0,65 where the page
    prints 0,70.
    """
    from_third_octave = ph.materials.weighted_absorption_from_third_octave(
        oracle.SRL_13441_THIRD_OCTAVE_ALPHA_S
    )
    alpha_p = ph.materials.practical_absorption_coefficient(
        oracle.SRL_13441_THIRD_OCTAVE_ALPHA_S
    )
    sp = ph.materials.weighted_absorption(list(oracle.SP_P302808_ALPHA_P))
    cstb = ph.materials.weighted_absorption(list(oracle.CSTB_AC14_ALPHA_P))
    results = {
        # printed rating, printed indicator, printed class
        "SRL 13441": (oracle.SRL_13441_RATING, from_third_octave),
        "SP P302808": (oracle.SP_P302808_RATING, sp),
        "CSTB AC14-26051052/10": (oracle.CSTB_AC14_RATING, cstb),
    }
    matching = sum(
        int(
            abs(got.alpha_w - alpha_w) <= 5e-4
            and got.shape_indicator == indicator
            and got.absorption_class == absorption_class
        )
        for (alpha_w, indicator, absorption_class), got in results.values()
    )
    # The UKAS certificate also prints the five octave coefficients it rated,
    # so the one-third-octave to octave step of 4.1 is checked as well as the
    # shifting of 4.2.
    octaves = sum(
        int(abs(value - printed) <= 5e-4)
        for value, printed in zip(
            alpha_p.tolist(), oracle.SRL_13441_ALPHA_P, strict=True
        )
    )
    return count(
        matching + octaves,
        len(results) + len(oracle.SRL_13441_ALPHA_P),
        subject="printed ratings and practical coefficients reproduced",
        expected_label="3/3 printed alpha_w with class and indicator, and "
        "5/5 printed alpha_p",
    )
